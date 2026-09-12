"""Reads a program's logged sets and turns them into a continuation decision.

The rules live in `app.domain.plateau` as pure functions; this module only supplies them
with data from the database and reports what came out. Nothing here decides anything by
itself, and nothing here asks a model.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.plateau import (
    BenchmarkSet,
    ExerciseProgress,
    PlateauTechnique,
    ProgramDecision,
    classify_exercise,
    decide_program_continuation,
    intensified_rep_target,
    reactive_deload,
    recommend_exercise_technique,
)
from app.models import Program, ProgramDay, ProgramExercise, ProgramWeek, WorkoutLog, WorkoutSet

logger = logging.getLogger(__name__)


# Muscle groups trained mostly by isolation work - same split progression.py uses for
# load steps, repeated here because the plateau breaker cap differs for them (p.7).
_ISOLATION_MUSCLES = {"biceps", "triceps", "calves", "rear_delts", "abs", "forearms"}


@dataclass
class ExerciseTechnique:
    """A course technique, attached to the exercise it is prescribed for."""

    exercise_name: str
    name: str
    title_bg: str
    how_bg: str
    source_bg: str


def _attach(exercise_name: str, technique: PlateauTechnique) -> ExerciseTechnique:
    """The technique carries no exercise of its own - it is pure advice until it is
    pinned to the lift it was worked out for."""
    return ExerciseTechnique(
        exercise_name=exercise_name,
        name=technique.name,
        title_bg=technique.title_bg,
        how_bg=technique.how_bg,
        source_bg=technique.source_bg,
    )


@dataclass
class ProgramReview:
    decision: ProgramDecision
    exercises: list[ExerciseProgress] = field(default_factory=list)
    techniques: list[ExerciseTechnique] = field(default_factory=list)
    new_rep_target: int | None = None       # set when the decision is adjust_exercise
    sessions_analysed: int = 0
    skipped_exercises: list[str] = field(default_factory=list)


async def _program_exercises(db: AsyncSession, program_id: str) -> dict[str, ProgramExercise]:
    """Prescribed exercises of the program, keyed by name (first occurrence wins)."""
    r = await db.execute(
        select(ProgramExercise)
        .join(ProgramDay, ProgramExercise.day_id == ProgramDay.id)
        .join(ProgramWeek, ProgramDay.week_id == ProgramWeek.id)
        .where(ProgramWeek.program_id == program_id)
        .order_by(ProgramWeek.week_number, ProgramDay.day_number, ProgramExercise.order_index)
    )
    by_name: dict[str, ProgramExercise] = {}
    for ex in r.scalars().all():
        by_name.setdefault(ex.exercise_name, ex)
    return by_name


async def _benchmark_series(db: AsyncSession, program_id: str) -> dict[str, list[BenchmarkSet]]:
    """First work set per exercise per session, oldest session first.

    Warm-ups and sets logged without a weight or reps cannot serve as a benchmark, so
    they are skipped; an exercise whose sets were all like that simply produces no
    series and is reported as skipped rather than silently counted as stalled.
    """
    r = await db.execute(
        select(WorkoutSet, WorkoutLog.date, WorkoutLog.id)
        .join(WorkoutLog, WorkoutSet.workout_log_id == WorkoutLog.id)
        .where(WorkoutLog.program_id == program_id)
        .order_by(WorkoutLog.date, WorkoutSet.set_number)
    )

    # (exercise, session) -> the first usable work set of that session.
    first_of_session: dict[tuple[str, str], BenchmarkSet] = {}
    for workout_set, log_date, log_id in r.all():
        if workout_set.is_warmup or workout_set.weight_kg is None or workout_set.reps is None:
            continue
        key = (workout_set.exercise_name, log_id)
        if key in first_of_session:
            continue
        first_of_session[key] = BenchmarkSet(
            date=log_date, weight_kg=workout_set.weight_kg, reps=workout_set.reps
        )

    series: dict[str, list[BenchmarkSet]] = {}
    for (exercise_name, _), benchmark in first_of_session.items():
        series.setdefault(exercise_name, []).append(benchmark)
    for sets in series.values():
        sets.sort(key=lambda s: s.date)
    return series


async def review_program(db: AsyncSession, program: Program) -> ProgramReview:
    """Classify every exercise in the program and decide what to do with the program."""
    prescribed = await _program_exercises(db, program.id)
    series = await _benchmark_series(db, program.id)

    progress: list[ExerciseProgress] = []
    techniques: list[ExerciseTechnique] = []
    skipped: list[str] = []

    for name, prescribed_ex in prescribed.items():
        sessions = series.get(name)
        if not sessions:
            skipped.append(name)
            continue
        result = classify_exercise(
            exercise_name=name,
            muscle_group=prescribed_ex.muscle_group,
            sessions=sessions,
            training_status=program.training_status,
        )
        progress.append(result)

        latest = sessions[-1]
        is_isolation = (prescribed_ex.muscle_group or "").lower() in _ISOLATION_MUSCLES

        # p.7 prescribes a breaker session whenever a workout did not progress as
        # planned, which covers both the exercise stuck on its weight and the one that
        # simply came out worse. How far the stall has gone decides which technique
        # `recommend_exercise_technique` returns.
        if result.status in ("stalled", "holding"):
            techniques.append(
                _attach(
                    name,
                    recommend_exercise_technique(
                        result,
                        latest=latest,
                        reps_min=prescribed_ex.reps_min,
                        reps_max=prescribed_ex.reps_max,
                        is_isolation=is_isolation,
                        training_status=program.training_status,
                    ),
                )
            )

        # Orthogonal to the plateau itself: losing reps is the course's signal to cut
        # the rest of *that* session short (p.46), whatever happens to the program.
        if result.last_session and result.last_session.reps_dropped and len(sessions) >= 2:
            reps_lost = sessions[-2].reps - latest.reps
            techniques.append(_attach(name, reactive_deload(latest, reps_lost)))

    decision = decide_program_continuation(progress, total_weeks=program.total_weeks)

    new_rep_target = None
    if decision.action == "adjust_exercise" and decision.exercise_name:
        stalled_ex = prescribed.get(decision.exercise_name)
        if stalled_ex:
            new_rep_target = intensified_rep_target(stalled_ex.reps_max)

    if skipped:
        logger.info(
            "Program %s review: %d exercise(s) had no usable work sets: %s",
            program.id, len(skipped), ", ".join(skipped),
        )

    return ProgramReview(
        decision=decision,
        exercises=progress,
        techniques=techniques,
        new_rep_target=new_rep_target,
        sessions_analysed=sum(len(s) for s in series.values()),
        skipped_exercises=skipped,
    )
