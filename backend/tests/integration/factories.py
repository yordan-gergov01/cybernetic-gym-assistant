"""Builders for the rows an integration test needs before it can assert anything.

Deliberately small and explicit: a test reads top to bottom, and the shape of the
program under test is written in the test itself, not hidden in a fixture file.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_password
from app.models import (
    Program,
    ProgramDay,
    ProgramExercise,
    ProgramWeek,
    User,
    UserProfile,
    WorkoutLog,
    WorkoutSet,
)

# (exercise name, muscle group, sets, reps_min, reps_max)
Exercise = tuple[str, str, int, int, int]
# (day name, exercises)
Day = tuple[str, list[Exercise]]


async def make_user(db: AsyncSession, email: str = "lifter@example.com") -> User:
    user = User(email=email, hashed_password=hash_password("hunter2hunter2!"), name="Lifter")
    db.add(user)
    await db.flush()
    return user


async def make_profile(db: AsyncSession, user: User, **overrides) -> UserProfile:
    fields = {
        "age": 30,
        "sex": "male",
        "height_cm": 180,
        "bodyweight_kg": 82,
        "goal": "bulk",
        "training_status": 2,
        "training_days_per_week": 2,
        "calculator_results": {"volume": {"chest": 16, "quads": 16}},
        **overrides,
    }
    profile = UserProfile(user_id=user.id, **fields)
    db.add(profile)
    await db.flush()
    return profile


async def make_program(
    db: AsyncSession,
    user: User,
    days: list[Day],
    *,
    weeks: int = 2,
    start_date: date = date(2026, 1, 5),
    status: str = "active",
) -> Program:
    """A program of `weeks` identical weeks - the shape the generator produces."""
    program = Program(
        user_id=user.id,
        name="Test program",
        created_by="manual",
        total_weeks=weeks,
        start_date=start_date,
        status=status,
        training_status=2,
    )
    db.add(program)
    await db.flush()

    for week_number in range(1, weeks + 1):
        week = ProgramWeek(program_id=program.id, week_number=week_number)
        db.add(week)
        await db.flush()
        for day_number, (day_name, exercises) in enumerate(days, start=1):
            day = ProgramDay(
                week_id=week.id,
                day_number=day_number,
                day_name=day_name,
                is_rest_day=not exercises,
            )
            db.add(day)
            await db.flush()
            for order, (name, muscle, sets, reps_min, reps_max) in enumerate(exercises):
                db.add(
                    ProgramExercise(
                        day_id=day.id,
                        order_index=order,
                        exercise_name=name,
                        muscle_group=muscle,
                        sets_prescribed=sets,
                        reps_min=reps_min,
                        reps_max=reps_max,
                        rir_target=2,
                        rest_seconds=120,
                    )
                )
    await db.flush()
    return program


async def log_session(
    db: AsyncSession,
    user: User,
    program: Program,
    day: ProgramDay | None,
    on: date,
    sets: list[tuple[str, float | None, int | None]],
    *,
    warmups: list[tuple[str, float, int]] | None = None,
) -> WorkoutLog:
    """One logged session. `sets` are work sets in the order they were performed.

    Sets are linked back to the prescribed exercise by name, exactly as the app does -
    that link is what carries the muscle group into the weekly volume.
    """
    prescribed_ids: dict[str, str] = {}
    if day:
        r = await db.execute(select(ProgramExercise).where(ProgramExercise.day_id == day.id))
        prescribed_ids = {e.exercise_name: e.id for e in r.scalars().all()}

    log = WorkoutLog(
        user_id=user.id,
        program_id=program.id,
        day_id=day.id if day else None,
        date=on,
    )
    db.add(log)
    await db.flush()

    number = 0
    for name, weight, reps in warmups or []:
        number += 1
        db.add(
            WorkoutSet(
                workout_log_id=log.id,
                exercise_name=name,
                set_number=number,
                weight_kg=weight,
                reps=reps,
                is_warmup=True,
            )
        )
    for name, weight, reps in sets:
        number += 1
        db.add(
            WorkoutSet(
                workout_log_id=log.id,
                program_exercise_id=prescribed_ids.get(name),
                exercise_name=name,
                set_number=number,
                weight_kg=weight,
                reps=reps,
            )
        )
    await db.flush()
    return log


async def week_days(db: AsyncSession, program: Program, week_number: int) -> list[ProgramDay]:
    """Days of one week, queried rather than walked - relationships do not lazy-load
    under an async session, and a test that tripped on that would fail for the wrong
    reason.

    `populate_existing` makes this read the database again instead of handing back what
    the session already had: production serves every request from a fresh session, so a
    test asserting on stale in-memory rows would be asserting about nothing.
    """
    r = await db.execute(
        select(ProgramDay)
        .join(ProgramWeek, ProgramDay.week_id == ProgramWeek.id)
        .where(ProgramWeek.program_id == program.id, ProgramWeek.week_number == week_number)
        .order_by(ProgramDay.day_number)
        .options(selectinload(ProgramDay.exercises))
        .execution_options(populate_existing=True)
    )
    return list(r.scalars().all())


async def prescribed(db: AsyncSession, program: Program, exercise_name: str) -> list[ProgramExercise]:
    """Every prescribed row for one exercise across the whole program."""
    r = await db.execute(
        select(ProgramExercise)
        .join(ProgramDay, ProgramExercise.day_id == ProgramDay.id)
        .join(ProgramWeek, ProgramDay.week_id == ProgramWeek.id)
        .where(ProgramWeek.program_id == program.id, ProgramExercise.exercise_name == exercise_name)
        .execution_options(populate_existing=True)
    )
    return list(r.scalars().all())
