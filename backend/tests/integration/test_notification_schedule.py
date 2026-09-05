"""Reminders under a scheduler: the same day gets visited many times.

The rules themselves were already exercised through the endpoint. What is new, and what
only a database can show, is that visiting a day twice does not tell the user twice.
"""
from datetime import date, datetime, time, timedelta

from sqlalchemy import select

from app.models import Notification, WeightLog
from app.services.notifications import (
    WEIGHT_REMINDER,
    WORKOUT_REMINDER,
    generate_for_everyone,
    generate_for_user,
)

from .factories import make_profile, make_program, make_user
from .test_routes import UPPER, auth

TODAY = date.today()


async def _reminders(db, user_id: str) -> list[str]:
    rows = await db.execute(select(Notification.type).where(Notification.user_id == user_id))
    return sorted(rows.scalars().all())


async def test_running_twice_in_one_day_does_not_remind_twice(db):
    """This is what makes a scheduler possible at all: it wakes hourly, and every wake
    after the first has to be a no-op."""
    user = await make_user(db)
    await make_profile(db, user, training_days_per_week=4)
    await make_program(db, user, [UPPER])

    first = await generate_for_user(db, user.id)
    second = await generate_for_user(db, user.id)

    assert WEIGHT_REMINDER in first
    assert second == [], "the second run of the day found everything already sent"
    assert await _reminders(db, user.id) == sorted(first)


async def test_yesterdays_reminder_does_not_silence_today(db):
    """Idempotency is per day, not forever - otherwise the user is reminded once and
    never again."""
    user = await make_user(db)
    db.add(Notification(
        user_id=user.id,
        type=WEIGHT_REMINDER,
        title="вчерашно",
        created_at=datetime.combine(TODAY - timedelta(days=1), time(9, 0)),
    ))
    await db.flush()

    created = await generate_for_user(db, user.id)

    assert WEIGHT_REMINDER in created


async def test_a_user_who_already_weighed_in_is_left_alone(db):
    user = await make_user(db)
    db.add(WeightLog(user_id=user.id, date=TODAY, weight_kg=82.0))
    await db.flush()

    created = await generate_for_user(db, user.id)

    assert WEIGHT_REMINDER not in created


async def test_the_workout_reminder_counts_what_is_left_of_the_week(db):
    user = await make_user(db)
    await make_profile(db, user, training_days_per_week=4)
    await make_program(db, user, [UPPER])

    created = await generate_for_user(db, user.id)

    assert WORKOUT_REMINDER in created
    body = (await db.execute(
        select(Notification.title).where(
            Notification.user_id == user.id, Notification.type == WORKOUT_REMINDER
        )
    )).scalar_one()
    assert "4" in body, "nothing was logged this week, so all four sessions are still due"


async def test_a_user_without_a_program_gets_no_workout_reminder(db):
    """There is nothing to be behind on."""
    user = await make_user(db)
    await make_profile(db, user, training_days_per_week=4)

    created = await generate_for_user(db, user.id)

    assert WORKOUT_REMINDER not in created


async def test_the_scheduler_run_covers_every_account(db):
    """The endpoint reminds whoever called it; the scheduler has nobody to ask."""
    first = await make_user(db, email="one@example.com")
    second = await make_user(db, email="two@example.com")

    results = await generate_for_everyone(db)

    assert set(results) == {first.id, second.id}


async def test_the_endpoint_still_reminds_the_caller(client, db):
    user = await make_user(db)

    answered = await client.post("/api/v1/notifications/generate", headers=auth(user))

    assert answered.status_code == 201
    assert WEIGHT_REMINDER in answered.json()["created"]
