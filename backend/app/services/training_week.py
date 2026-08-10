"""Everything the Today screen needs, answered from the database.

The rules live in `domain/schedule.py` and `domain/training_volume.py`; this module only
feeds them and assembles the result. Nothing is computed in the client - the frontend
renders what it is given.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date as date_type
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.schedule import (
    CalendarDay,
    SessionEstimate,
    calendar_week,
    estimate_session,
    is_rest_today,
    next_day_index,
    week_number,
)
from app.domain.training_volume import MuscleVolume, tonnage_kg, weekly_volume, working_set_count
from app.models import (
    Program,
    ProgramDay,
    ProgramExercise,
    ProgramWeek,
    UserProfile,
    WeightLog,
    WorkoutLog,
    WorkoutSet,
)

logger = logging.getLogger(__name__)


@dataclass
class LastSession:
    date: date_type
    tonnage_kg: float
    working_sets: int


@dataclass
class TodayView:
    program_id: str
    program_name: str
    template_type: str | None
    goal: str | None
    week_number: int
    total_weeks: int
    is_rest_day: bool
    trained_today: bool
    weighed_in_today: bool
    sessions_this_week: int
    sessions_planned: int
    calendar: list[CalendarDay] = field(default_factory=list)
    day_id: str | None = None
    day_name: str | None = None
    exercises: list[ProgramExercise] = field(default_factory=list)
    estimate: SessionEstimate | None = None
    last_session: LastSession | None = None
    weekly_volume: list[MuscleVolume] = field(default_factory=list)


async def _active_program(db: AsyncSession, user_id: str) -> Program | None:
    """The program in play: the active one, else the most recent."""
    r = await db.execute(
        select(Program)
        .where(Program.user_id == user_id)
        .order_by((Program.status != "active"), Program.created_at.desc())
    )
    return r.scalars().first()


async def _training_days(db: AsyncSession, program_id: str) -> list[ProgramDay]:
    """The program's rotation of training days, from its first week.

    Every week of a generated program repeats the same template, so the rotation is the
    first week's non-rest days in order.
    """
    r = await db.execute(
        select(ProgramWeek)
        .where(ProgramWeek.program_id == program_id)
        .order_by(ProgramWeek.week_number)
        .options(selectinload(ProgramWeek.days).selectinload(ProgramDay.exercises))
        .limit(1)
    )
    week = r.scalars().first()
    if not week:
        return []
    return [d for d in sorted(week.days, key=lambda d: d.day_number) if not d.is_rest_day]


async def _logged_sets(db: AsyncSession, user_id: str, since: date_type) -> list[dict]:
    """Working sets logged since a date, carrying the muscle they trained.

    The muscle comes from the prescribed exercise; a set logged outside a program has
    none, and is counted in tonnage but not against a muscle's weekly target.
    """
    r = await db.execute(
        select(WorkoutSet, WorkoutLog.date, ProgramExercise.muscle_group)
        .join(WorkoutLog, WorkoutSet.workout_log_id == WorkoutLog.id)
        .outerjoin(ProgramExercise, WorkoutSet.program_exercise_id == ProgramExercise.id)
        .where(WorkoutLog.user_id == user_id, WorkoutLog.date >= since)
    )
    return [
        {
            "date": log_date,
            "weight_kg": s.weight_kg,
            "reps": s.reps,
            "is_warmup": s.is_warmup,
            "muscle_group": muscle,
        }
        for s, log_date, muscle in r.all()
    ]


async def build_today(db: AsyncSession, user_id: str, today: date_type) -> TodayView | None:
    """Assemble the Today screen. Returns None when there is no program yet."""
    program = await _active_program(db, user_id)
    if not program:
        return None

    pr = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = pr.scalar_one_or_none()
    weekly_target = (profile.training_days_per_week if profile else None) or 0

    # Dates of every session logged against this program, plus this week's sets.
    r = await db.execute(
        select(WorkoutLog.date).where(
            WorkoutLog.user_id == user_id, WorkoutLog.program_id == program.id
        )
    )
    session_dates = sorted(r.scalars().all())
    monday = today - timedelta(days=today.weekday())

    trained_dates = set(session_dates)
    sessions_this_week = len({d for d in session_dates if d >= monday})
    trained_today = today in trained_dates

    # Whether today's weigh-in is done is decided here too - the client should not have
    # to fetch the weight log just to know if it needs to nudge.
    wr = await db.execute(
        select(WeightLog.id).where(WeightLog.user_id == user_id, WeightLog.date == today)
    )
    weighed_in_today = wr.first() is not None

    days = await _training_days(db, program.id)
    index = next_day_index(len(session_dates), len(days))
    day = days[index] if index is not None and days else None

    rest = is_rest_today(
        trained_today=trained_today,
        sessions_this_week=sessions_this_week,
        weekly_target=weekly_target,
    )

    exercises = sorted(day.exercises, key=lambda e: e.order_index) if day else []
    estimate = (
        estimate_session(
            [{"sets_prescribed": e.sets_prescribed, "rest_seconds": e.rest_seconds} for e in exercises]
        )
        if exercises
        else None
    )

    week_sets = await _logged_sets(db, user_id, monday)
    volume_targets = ((profile.calculator_results or {}).get("volume") if profile else None) or {}
    if not isinstance(volume_targets, dict):
        logger.warning("Profile %s has a non-dict volume target; weekly targets omitted", user_id)
        volume_targets = {}

    last_session = None
    if session_dates:
        last_date = session_dates[-1]
        last_sets = await _logged_sets(db, user_id, last_date)
        same_day = [s for s in last_sets if s["date"] == last_date]
        last_session = LastSession(
            date=last_date,
            tonnage_kg=tonnage_kg(same_day),
            working_sets=working_set_count(same_day),
        )

    return TodayView(
        program_id=program.id,
        program_name=program.name,
        template_type=program.template_type,
        goal=program.goal,
        week_number=week_number(program.start_date, today, program.total_weeks),
        total_weeks=program.total_weeks,
        is_rest_day=rest or day is None,
        trained_today=trained_today,
        weighed_in_today=weighed_in_today,
        sessions_this_week=sessions_this_week,
        sessions_planned=weekly_target,
        calendar=calendar_week(today, trained_dates),
        day_id=day.id if day else None,
        day_name=day.day_name if day else None,
        exercises=exercises,
        estimate=estimate,
        last_session=last_session,
        weekly_volume=weekly_volume(week_sets, volume_targets),
    )
