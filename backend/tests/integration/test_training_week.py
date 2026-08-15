"""`build_today` against a real database.

The Today screen renders whatever this returns, so the questions here are the coaching
ones: which session is next, whether today is a rest day, and what this week's volume
looks like. The scheduling arithmetic itself is covered by tests/test_schedule.py.
"""
from datetime import date, timedelta

from app.models import WeightLog
from app.services.training_week import build_today

from .factories import log_session, make_profile, make_program, make_user, week_days

MONDAY = date(2026, 1, 5)

UPPER = ("Upper", [("Barbell Bench Press", "chest", 4, 6, 8), ("Barbell Row", "back", 4, 6, 10)])
LOWER = ("Lower", [("Barbell Squat", "quads", 4, 6, 8)])


async def test_no_program_means_no_today(db):
    user = await make_user(db)
    await make_profile(db, user)
    assert await build_today(db, user.id, MONDAY) is None


async def test_the_next_session_follows_the_rotation_not_the_weekday(db):
    """Sessions advance one slot per logged workout - a missed day does not skip a session."""
    user = await make_user(db)
    await make_profile(db, user, training_days_per_week=2)
    program = await make_program(db, user, [UPPER, LOWER])
    days = await week_days(db, program, 1)

    first = await build_today(db, user.id, MONDAY)
    assert first.day_name == "Upper"

    await log_session(db, user, program, days[0], MONDAY, [("Barbell Bench Press", 100, 8)])
    second = await build_today(db, user.id, MONDAY + timedelta(days=2))
    assert second.day_name == "Lower", "the rotation moved on, whatever day of the week it is"


async def test_a_session_logged_today_makes_today_a_rest_day(db):
    user = await make_user(db)
    await make_profile(db, user, training_days_per_week=2)
    program = await make_program(db, user, [UPPER, LOWER])
    days = await week_days(db, program, 1)

    await log_session(db, user, program, days[0], MONDAY, [("Barbell Bench Press", 100, 8)])

    today = await build_today(db, user.id, MONDAY)
    assert today.trained_today
    assert today.is_rest_day, "training twice in one day is not what the plan asks for"


async def test_the_week_is_rest_once_the_planned_sessions_are_done(db):
    user = await make_user(db)
    await make_profile(db, user, training_days_per_week=2)
    program = await make_program(db, user, [UPPER, LOWER])
    days = await week_days(db, program, 1)

    await log_session(db, user, program, days[0], MONDAY, [("Barbell Bench Press", 100, 8)])
    await log_session(db, user, program, days[1], MONDAY + timedelta(days=1), [("Barbell Squat", 140, 6)])

    today = await build_today(db, user.id, MONDAY + timedelta(days=3))
    assert today.sessions_this_week == 2
    assert today.is_rest_day


async def test_weekly_volume_counts_only_this_week_and_only_work_sets(db):
    """Last week's sets and today's warm-ups must not inflate the volume bars."""
    user = await make_user(db)
    await make_profile(db, user, training_days_per_week=4)
    program = await make_program(db, user, [UPPER, LOWER])
    days = await week_days(db, program, 1)

    await log_session(
        db, user, program, days[0], MONDAY - timedelta(days=7), [("Barbell Bench Press", 100, 8)]
    )
    await log_session(
        db,
        user,
        program,
        days[0],
        MONDAY,
        [("Barbell Bench Press", 100, 8), ("Barbell Bench Press", 100, 7)],
        warmups=[("Barbell Bench Press", 60, 10)],
    )

    today = await build_today(db, user.id, MONDAY + timedelta(days=2))
    chest = next(v for v in today.weekly_volume if v.muscle_group == "chest")
    assert chest.sets_done == 2, "two work sets this week; the warm-up and last week do not count"


async def test_the_weigh_in_nudge_reflects_the_weight_log(db):
    user = await make_user(db)
    await make_profile(db, user, training_days_per_week=2)
    await make_program(db, user, [UPPER, LOWER])

    today = await build_today(db, user.id, MONDAY)
    assert today.weighed_in_today is False

    db.add(WeightLog(user_id=user.id, date=MONDAY, weight_kg=82.0))
    await db.flush()
    assert (await build_today(db, user.id, MONDAY)).weighed_in_today is True
