"""Applies a review verdict to the program itself.

`services/program_progress.py` says what should change; this module is the only place
that changes it. The rules stay in `domain/` - here there is nothing but loading rows,
writing them, and reporting what was written.

Every change covers **all** weeks of the program, not the ones after the current week.
A generated program is one template week repeated, and the training rotation is served
from the first week's day rows (`services/training_week.py`), so a change that skipped
week 1 would never reach the session the user actually trains. The logged history is
untouched: a WorkoutSet carries its own exercise name.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.exercise_library import Exercise
from app.domain.program_design import MuscleAdjustment
from app.models import ProgramDay, ProgramExercise, ProgramWeek

logger = logging.getLogger(__name__)


@dataclass
class ProgramChange:
    """What the program looks like after the change, in the user's words."""

    action: str
    summary_bg: str
    exercises: list[str] = field(default_factory=list)
    rows_changed: int = 0


async def program_weeks(db: AsyncSession, program_id: str) -> list[ProgramWeek]:
    """Every week with its days and exercises, oldest week first."""
    r = await db.execute(
        select(ProgramWeek)
        .where(ProgramWeek.program_id == program_id)
        .order_by(ProgramWeek.week_number)
        .options(selectinload(ProgramWeek.days).selectinload(ProgramDay.exercises))
    )
    return list(r.scalars().all())


def exercise_rows(weeks: list[ProgramWeek], exercise_name: str) -> list[ProgramExercise]:
    """Every prescribed row for one exercise, across all weeks."""
    return [
        exercise
        for week in weeks
        for day in week.days
        for exercise in day.exercises
        if exercise.exercise_name == exercise_name
    ]


def template_days(weeks: list[ProgramWeek]) -> list[dict]:
    """The first week as plain dicts, which is what the domain rules take.

    The first week is the template every other week copies, and the one the training
    rotation is served from, so it is the week a structural decision is made on.
    """
    if not weeks:
        return []
    return [
        {
            "day_number": day.day_number,
            "is_rest_day": day.is_rest_day,
            "exercises": [
                {
                    "exercise_name": exercise.exercise_name,
                    "muscle_group": exercise.muscle_group,
                    "sets_prescribed": exercise.sets_prescribed,
                    "order_index": exercise.order_index,
                }
                for exercise in sorted(day.exercises, key=lambda e: e.order_index)
            ],
        }
        for day in sorted(weeks[0].days, key=lambda d: d.day_number)
    ]


async def apply_swap(
    db: AsyncSession, rows: list[ProgramExercise], replacement: Exercise
) -> ProgramChange:
    """Replace one exercise with another everywhere it is prescribed.

    The progression targets are cleared rather than carried over: they are the next
    session's load for the exercise that stalled, and prescribing them for a different
    movement would ask for a weight nobody has ever lifted on it.
    """
    previous = rows[0].exercise_name
    for row in rows:
        row.exercise_name = replacement.name
        row.muscle_group = replacement.muscle_group or row.muscle_group
        row.target_weight_kg = None
        row.target_reps = None
        row.target_note = None
    await db.commit()

    logger.info("Swapped %s for %s across %d prescribed rows", previous, replacement.name, len(rows))
    return ProgramChange(
        action="swap",
        summary_bg=(
            f"{previous} е заменено с {replacement.name} във всички {len(rows)} тренировки "
            "от програмата. Прогресията започва отначало за новото упражнение."
        ),
        exercises=[replacement.name],
        rows_changed=len(rows),
    )


async def apply_rep_range(
    db: AsyncSession, rows: list[ProgramExercise], rep_range: tuple[int, int]
) -> ProgramChange:
    """Lower the prescribed rep range - the course's intensification of a stalled lift."""
    low, high = rep_range
    previous = f"{rows[0].reps_min}-{rows[0].reps_max}"
    for row in rows:
        row.reps_min = low
        row.reps_max = high
    await db.commit()

    return ProgramChange(
        action="intensify",
        summary_bg=(
            f"{rows[0].exercise_name}: целта слиза от {previous} на {low}-{high} повторения "
            f"в {len(rows)} тренировки. По-тежко тегло за по-малко повторения."
        ),
        exercises=[rows[0].exercise_name],
        rows_changed=len(rows),
    )


async def apply_undulation(
    db: AsyncSession,
    weeks: list[ProgramWeek],
    exercise_name: str,
    heavy: tuple[int, int],
    volume: tuple[int, int],
) -> ProgramChange:
    """Give one exercise two rep targets that alternate between its sessions.

    The alternation is inside each week, not across weeks: undulation is about the next
    session carrying a different stimulus than the last one, and spreading the two
    targets over separate weeks would just be a slow linear change with extra steps.

    The first session of the week keeps the heavy target it already had, so the exercise
    the lifter is stuck on is not suddenly lighter everywhere.
    """
    changed = 0
    for week in weeks:
        occurrences = [
            exercise
            for day in week.days
            for exercise in day.exercises
            if exercise.exercise_name == exercise_name
        ]
        for index, row in enumerate(occurrences):
            row.reps_min, row.reps_max = heavy if index % 2 == 0 else volume
            changed += 1
    await db.commit()

    logger.info("Undulated %s across %d prescribed rows", exercise_name, changed)
    return ProgramChange(
        action="periodize",
        summary_bg=(
            f"{exercise_name}: сесиите вече не са еднакви - първата в седмицата остава "
            f"{heavy[0]}-{heavy[1]} повторения, втората става {volume[0]}-{volume[1]} при "
            f"по-малка тежест. Променени са {changed} тренировки."
        ),
        exercises=[exercise_name],
        rows_changed=changed,
    )


def weekly_occurrences(weeks: list[ProgramWeek], exercise_name: str) -> int:
    """How many times a week the exercise is trained, by the first week of the program.

    Undulation needs two sessions to alternate between; one session a week can only ever
    carry one stimulus.
    """
    if not weeks:
        return 0
    return len([
        exercise
        for day in weeks[0].days
        for exercise in day.exercises
        if exercise.exercise_name == exercise_name
    ])


async def apply_muscle_adjustment(
    db: AsyncSession, weeks: list[ProgramWeek], adjustment: MuscleAdjustment
) -> ProgramChange:
    """Carry out a frequency or volume change for one muscle group, in every week."""
    if adjustment.action == "add_sets":
        rows = exercise_rows(weeks, adjustment.exercise_name or "")
        for row in rows:
            row.sets_prescribed = (row.sets_prescribed or 0) + 1
        await db.commit()
        return ProgramChange(
            action="add_sets",
            summary_bg=adjustment.reason_bg,
            exercises=[adjustment.exercise_name] if adjustment.exercise_name else [],
            rows_changed=len(rows),
        )

    moved = 0
    for week in weeks:
        days = {day.day_number: day for day in week.days}
        source, target = days.get(adjustment.from_day), days.get(adjustment.to_day)
        if not source or not target:
            # A week that does not have both days is left alone rather than half-changed.
            logger.warning(
                "Week %s of program %s lacks day %s or %s; frequency change skipped there",
                week.week_number, week.program_id, adjustment.from_day, adjustment.to_day,
            )
            continue
        row = next(
            (e for e in source.exercises if e.exercise_name == adjustment.exercise_name), None
        )
        if not row:
            continue
        row.day_id = target.id
        row.order_index = max((e.order_index for e in target.exercises), default=-1) + 1
        moved += 1
    await db.commit()

    return ProgramChange(
        action="move_exercise",
        summary_bg=adjustment.reason_bg,
        exercises=[adjustment.exercise_name] if adjustment.exercise_name else [],
        rows_changed=moved,
    )
