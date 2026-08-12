"""Fill a demo account with realistic history, so screens can be judged with content.

Usage (from backend/):
    python -m scripts.seed_demo                  # create/refresh demo@example.com
    python -m scripts.seed_demo --email me@x.bg  # seed an existing account instead
    python -m scripts.seed_demo --clear          # remove the demo account and its data

Everything is written through the real models, so the screens render the same code
paths they will in production - no fixtures inside the app, and nothing to strip out
before shipping. Re-running replaces the seeded history rather than stacking a second
copy on top of it.

The numbers are shaped to exercise the interesting states: a downward weight trend with
day-to-day noise, four weeks of sessions where most lifts progress and one deliberately
stalls, and a day of food that lands under target.
"""
from __future__ import annotations

import argparse
import asyncio
import random
import sys
from datetime import date, datetime, timedelta

from sqlalchemy import delete, select

from app.core.security import hash_password
from app.db.database import get_db
from app.models import (
    FoodLog,
    Notification,
    NutritionTarget,
    Program,
    ProgramDay,
    ProgramExercise,
    ProgramWeek,
    User,
    UserProfile,
    WeightLog,
    WorkoutLog,
    WorkoutSet,
)

# example.com is the reserved test domain; a .local address is rejected by the
# API's email validation, so the seeded account could not sign in.
DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "demo12345"

WEEKS = 4
START_WEIGHT = 86.4
WEEKLY_LOSS = 0.42

# Upper/Lower over four days, the split the course recommends at this frequency.
DAYS: list[tuple[str, list[tuple[str, str, int, int, int, float]]]] = [
    ("Горна част A", [
        ("Barbell Bench Press", "chest", 4, 6, 8, 80.0),
        ("Weighted Pull-up", "back", 4, 6, 10, 10.0),
        ("Incline Dumbbell Press", "chest", 3, 8, 12, 28.0),
        ("Chest Supported Row", "back", 4, 8, 12, 60.0),
        ("Seated Dumbbell Shoulder Press", "shoulders", 3, 8, 12, 22.0),
        ("Cable Lateral Raise", "shoulders", 3, 12, 15, 9.0),
    ]),
    ("Долна част A", [
        ("Barbell Squat", "quads", 4, 5, 8, 110.0),
        ("Romanian Deadlift", "hamstrings", 3, 8, 10, 90.0),
        ("Leg Press", "quads", 3, 10, 12, 160.0),
        ("Seated Leg Curl", "hamstrings", 3, 10, 12, 45.0),
        ("Standing Calf Raise", "calves", 4, 10, 15, 70.0),
    ]),
    ("Горна част Б", [
        ("Overhead Press", "shoulders", 4, 5, 8, 52.5),
        ("Barbell Row", "back", 4, 6, 10, 75.0),
        ("Flat Dumbbell Bench Press", "chest", 3, 8, 12, 30.0),
        ("Wide Grip Lat Pulldown", "back", 3, 10, 12, 65.0),
        ("Triceps Pushdown", "triceps", 3, 10, 15, 32.5),
        ("Bayesian Curl", "biceps", 3, 10, 15, 14.0),
    ]),
    ("Долна част Б", [
        ("Deadlift", "hamstrings", 3, 3, 5, 140.0),
        ("Front Squat", "quads", 3, 6, 8, 80.0),
        ("Hip Thrust", "glutes", 3, 8, 12, 100.0),
        ("Leg Extension", "quads", 3, 12, 15, 50.0),
        ("Seated Calf Raise", "calves", 4, 12, 15, 45.0),
    ]),
]

# One lift is held flat on purpose so the plateau engine has something to find.
STALLED_LIFT = "Overhead Press"

FOODS = [
    ("breakfast", "овесени ядки", 100, 372, 12.5, 6.9, 62.0),
    ("breakfast", "яйце", 120, 172, 15.4, 11.5, 1.1),
    ("lunch", "пилешко филе", 200, 212, 44.6, 2.4, 0.0),
    ("lunch", "ориз", 150, 195, 4.0, 0.5, 42.0),
    ("dinner", "сьомга", 180, 372, 36.0, 24.0, 0.0),
    ("dinner", "картофи", 250, 192, 5.0, 0.2, 44.0),
    ("snack", "гръцко кисело мляко", 200, 118, 20.0, 0.8, 7.2),
]

NOTIFICATIONS = [
    ("weight", "Не забравяй да логнеш теглото си", "Последно измерване преди 2 дни.", 2),
    ("workout", "Още 2 тренировки тази седмица", "Долна част Б и Горна част Б остават.", 6),
    ("checkin", "Време е за седмичния чек-ин", "6 въпроса. Определя дали ти трябва deload.", 26),
]


def _round_to(value: float, step: float) -> float:
    return round(round(value / step) * step, 2)


async def _wipe(db, user_id: str) -> None:
    """Remove previously seeded history so a re-run replaces it."""
    programs = (await db.execute(select(Program.id).where(Program.user_id == user_id))).scalars().all()
    weeks = (
        (await db.execute(select(ProgramWeek.id).where(ProgramWeek.program_id.in_(programs)))).scalars().all()
        if programs else []
    )
    days = (
        (await db.execute(select(ProgramDay.id).where(ProgramDay.week_id.in_(weeks)))).scalars().all()
        if weeks else []
    )
    logs = (await db.execute(select(WorkoutLog.id).where(WorkoutLog.user_id == user_id))).scalars().all()
    if logs:
        await db.execute(delete(WorkoutSet).where(WorkoutSet.workout_log_id.in_(logs)))
    await db.execute(delete(WorkoutLog).where(WorkoutLog.user_id == user_id))
    if days:
        await db.execute(delete(ProgramExercise).where(ProgramExercise.day_id.in_(days)))
        await db.execute(delete(ProgramDay).where(ProgramDay.week_id.in_(weeks)))
    if weeks:
        await db.execute(delete(ProgramWeek).where(ProgramWeek.program_id.in_(programs)))
    await db.execute(delete(Program).where(Program.user_id == user_id))
    await db.execute(delete(WeightLog).where(WeightLog.user_id == user_id))
    await db.execute(delete(FoodLog).where(FoodLog.user_id == user_id))
    await db.execute(delete(Notification).where(Notification.user_id == user_id))
    await db.execute(delete(NutritionTarget).where(NutritionTarget.user_id == user_id))


async def _ensure_user(db, email: str) -> User:
    user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user:
        return user
    user = User(email=email, hashed_password=hash_password(DEMO_PASSWORD), name="Мартин")
    db.add(user)
    await db.flush()
    return user


async def _profile(db, user: User) -> UserProfile:
    profile = (
        await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    ).scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
    profile.age = 25
    profile.sex = "male"
    profile.height_cm = 182
    profile.bodyweight_kg = 84.2
    profile.body_fat_pct = 16.8
    profile.bf_assessment_method = "visual (gemini-2.0-flash, medium)"
    profile.goal = "cut"
    profile.goal_validated = "cut"
    profile.activity_level = "moderate"
    profile.training_status = 2
    profile.training_years = 3
    profile.training_days_per_week = 4
    profile.session_duration_min = 75
    profile.available_equipment = "full_gym"
    profile.min_barbell_increment_kg = 2.5
    profile.min_dumbbell_increment_kg = 2.0
    profile.stress_level = "average"
    profile.sleep_quality = "fair"
    profile.sleep_hours = 7
    profile.dedication_level = "balanced"
    profile.priority_muscles = ["chest", "back", "shoulders"]
    profile.injuries = "Лек дискомфорт в лявото рамо при широк хват."
    profile.dietary_restrictions = "lactose_free"
    profile.calculator_results = {
        "energy": {"target_kcal": 2650, "tdee": 3040, "protein_g": 180, "carbs_g": 265, "fat_g": 76,
                   "method": "Katch-McArdle"},
        "volume": {"chest": 18, "back": 18, "shoulders": 16, "quads": 16, "hamstrings": 14,
                   "glutes": 12, "biceps": 12, "triceps": 12, "calves": 10},
    }
    return profile


async def _program(db, user: User, start: date) -> Program:
    program = Program(
        user_id=user.id,
        name="Хипертрофия · Горна/Долна",
        description="Четири дни седмично, всяка мускулна група два пъти.",
        created_by="seed",
        template_type="upper_lower",
        total_weeks=8,
        start_date=start,
        end_date=start + timedelta(weeks=8),
        status="active",
        goal="cut",
        training_status=2,
    )
    db.add(program)
    await db.flush()

    for week_number in range(1, 9):
        week = ProgramWeek(program_id=program.id, week_number=week_number, week_type="loading")
        db.add(week)
        await db.flush()
        for day_number, (day_name, exercises) in enumerate(DAYS, start=1):
            day = ProgramDay(week_id=week.id, day_number=day_number, day_name=day_name)
            db.add(day)
            await db.flush()
            for order, (name, muscle, sets, rep_min, rep_max, _load) in enumerate(exercises):
                db.add(ProgramExercise(
                    day_id=day.id, order_index=order, exercise_name=name, muscle_group=muscle,
                    sets_prescribed=sets, reps_min=rep_min, reps_max=rep_max,
                    rir_target=2 if order < 2 else 1, rest_seconds=180 if order < 2 else 120,
                ))
    return program


async def _history(db, user: User, program: Program, start: date, today: date) -> int:
    """Four weeks of sessions, most lifts adding load, one held flat."""
    rng = random.Random(7)
    day_ids: dict[int, str] = {}
    first_week = (
        await db.execute(
            select(ProgramWeek).where(ProgramWeek.program_id == program.id, ProgramWeek.week_number == 1)
        )
    ).scalar_one()
    days = (
        await db.execute(select(ProgramDay).where(ProgramDay.week_id == first_week.id).order_by(ProgramDay.day_number))
    ).scalars().all()
    for d in days:
        day_ids[d.day_number] = d.id

    exercise_ids: dict[str, str] = {}
    for d in days:
        rows = (
            await db.execute(select(ProgramExercise).where(ProgramExercise.day_id == d.id))
        ).scalars().all()
        for row in rows:
            exercise_ids.setdefault(row.exercise_name, row.id)

    sessions = 0
    for week in range(WEEKS):
        for day_number, (_day_name, exercises) in enumerate(DAYS, start=1):
            when = start + timedelta(weeks=week, days=(day_number - 1) * 2)
            if when >= today:
                continue
            log = WorkoutLog(
                user_id=user.id, program_id=program.id, day_id=day_ids[day_number], date=when,
                started_at=datetime.combine(when, datetime.min.time()) + timedelta(hours=18),
                finished_at=datetime.combine(when, datetime.min.time()) + timedelta(hours=19, minutes=15),
                duration_min=75, status="completed",
            )
            db.add(log)
            await db.flush()
            for name, _muscle, sets, rep_min, rep_max, base in exercises:
                # Everything creeps up week to week except the lift meant to stall.
                growth = 0 if name == STALLED_LIFT else week * 2.5
                load = _round_to(base + growth, 2.5)
                for set_number in range(1, sets + 1):
                    fatigue_drop = rng.choice([0, 0, 1]) * (set_number - 1)
                    reps = max(rep_min - 1, rep_max - (set_number - 1) - fatigue_drop)
                    db.add(WorkoutSet(
                        workout_log_id=log.id,
                        program_exercise_id=exercise_ids.get(name),
                        exercise_name=name, set_number=set_number,
                        weight_kg=load, reps=reps,
                        rir_actual=max(0, 2 - (set_number - 1)),
                    ))
            sessions += 1
    return sessions


async def _weights(db, user: User, today: date) -> int:
    """Sixty days of weigh-ins: a real downward trend under daily water noise."""
    rng = random.Random(11)
    count = 0
    for offset in range(59, -1, -1):
        when = today - timedelta(days=offset)
        # Not every day gets logged, which is what the trend smoothing exists for.
        if rng.random() < 0.18:
            continue
        weeks_elapsed = (59 - offset) / 7
        value = START_WEIGHT - WEEKLY_LOSS * weeks_elapsed + rng.uniform(-0.6, 0.6)
        db.add(WeightLog(user_id=user.id, date=when, weight_kg=round(value, 1)))
        count += 1
    return count


async def _food(db, user: User, today: date) -> None:
    for meal, name, grams, kcal, protein, fat, carbs in FOODS:
        db.add(FoodLog(
            user_id=user.id, date=today, meal_type=meal, food_name=name, quantity_g=grams,
            calories=kcal, protein_g=protein, fat_g=fat, carbs_g=carbs,
            source="USDA", confidence="high",
        ))
    db.add(NutritionTarget(user_id=user.id, calories=2650, protein_g=180, fat_g=76, carbs_g=265))


async def _notifications(db, user: User) -> None:
    now = datetime.utcnow()
    for kind, title, body, hours_ago in NOTIFICATIONS:
        db.add(Notification(
            user_id=user.id, type=kind, title=title, body=body,
            created_at=now - timedelta(hours=hours_ago),
            is_read=hours_ago > 24,
        ))


async def seed(email: str) -> None:
    today = date.today()
    start = today - timedelta(weeks=WEEKS - 1, days=today.weekday())

    agen = get_db()
    db = await agen.__anext__()
    try:
        user = await _ensure_user(db, email)
        await _wipe(db, user.id)
        await _profile(db, user)
        program = await _program(db, user, start)
        sessions = await _history(db, user, program, start, today)
        weigh_ins = await _weights(db, user, today)
        await _food(db, user, today)
        await _notifications(db, user)
        await db.commit()
    finally:
        try:
            await agen.aclose()
        except Exception:
            pass

    print(f"Seeded {email}")
    print(f"  password:      {DEMO_PASSWORD}" if email == DEMO_EMAIL else "  password:      (unchanged)")
    print(f"  program:       {program.name}, 8 weeks from {start}")
    print(f"  sessions:      {sessions} logged over {WEEKS} weeks")
    print(f"  weigh-ins:     {weigh_ins} over 60 days")
    print(f"  food:          {len(FOODS)} entries today")
    print(f"  stalled lift:  {STALLED_LIFT} (held flat so the plateau engine has a target)")


async def clear(email: str) -> None:
    agen = get_db()
    db = await agen.__anext__()
    try:
        user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if not user:
            print(f"No account for {email}")
            return
        await _wipe(db, user.id)
        await db.execute(delete(UserProfile).where(UserProfile.user_id == user.id))
        await db.execute(delete(User).where(User.id == user.id))
        await db.commit()
        print(f"Removed {email} and everything attached to it")
    finally:
        try:
            await agen.aclose()
        except Exception:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", default=DEMO_EMAIL, help="account to seed")
    parser.add_argument("--clear", action="store_true", help="delete the account instead")
    args = parser.parse_args()

    asyncio.run(clear(args.email) if args.clear else seed(args.email))
    return 0


if __name__ == "__main__":
    sys.exit(main())
