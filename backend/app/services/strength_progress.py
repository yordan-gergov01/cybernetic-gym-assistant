"""Estimated max per exercise over a recent window, for the Progress screen.

Same benchmark as everywhere else in the app - the first work set of each session
(Progression Guidelines p.3) - so the number shown on Progress cannot disagree with the
one the progression engine acted on.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date as date_type
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.plateau import BenchmarkSet, strength_trend
from app.models import ProgramExercise, WorkoutLog, WorkoutSet

# Exercises with a single logged session have no trend to speak of; showing them with a
# flat line would imply a plateau that was never observed.
MIN_SESSIONS = 2


@dataclass
class ExerciseStrength:
    exercise_name: str
    muscle_group: str | None
    best_e1rm: float
    change_kg: float
    sessions: int
    points: list[float]


async def strength_by_exercise(
    db: AsyncSession, user_id: str, *, weeks: int, today: date_type
) -> list[ExerciseStrength]:
    """Strength trend per exercise over the last `weeks`, strongest change first."""
    since = today - timedelta(weeks=weeks)

    r = await db.execute(
        select(WorkoutSet, WorkoutLog.date, WorkoutLog.id, ProgramExercise.muscle_group)
        .join(WorkoutLog, WorkoutSet.workout_log_id == WorkoutLog.id)
        .outerjoin(ProgramExercise, WorkoutSet.program_exercise_id == ProgramExercise.id)
        .where(WorkoutLog.user_id == user_id, WorkoutLog.date >= since)
        .order_by(WorkoutLog.date, WorkoutSet.set_number)
    )

    # First usable work set of each (exercise, session) - the benchmark.
    first_of_session: dict[tuple[str, str], BenchmarkSet] = {}
    muscles: dict[str, str | None] = {}
    for workout_set, log_date, log_id, muscle in r.all():
        if workout_set.is_warmup or workout_set.weight_kg is None or workout_set.reps is None:
            continue
        key = (workout_set.exercise_name, log_id)
        if key in first_of_session:
            continue
        first_of_session[key] = BenchmarkSet(
            date=log_date, weight_kg=workout_set.weight_kg, reps=workout_set.reps
        )
        muscles.setdefault(workout_set.exercise_name, muscle)

    series: dict[str, list[BenchmarkSet]] = {}
    for (exercise_name, _), benchmark in first_of_session.items():
        series.setdefault(exercise_name, []).append(benchmark)

    results: list[ExerciseStrength] = []
    for name, sessions in series.items():
        if len(sessions) < MIN_SESSIONS:
            continue
        trend = strength_trend(sessions)
        results.append(
            ExerciseStrength(
                exercise_name=name,
                muscle_group=muscles.get(name),
                best_e1rm=trend.best_e1rm,
                change_kg=trend.change_kg,
                sessions=len(sessions),
                points=list(trend.points),
            )
        )

    # Heaviest first: the compounds are what the plan is judged on, and ranking by
    # kilos gained floats a lateral raise above a squat.
    results.sort(key=lambda e: e.best_e1rm, reverse=True)
    return results
