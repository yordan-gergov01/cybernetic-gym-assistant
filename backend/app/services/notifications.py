"""Reminders: what is worth telling a user today, and when to look.

The rules were written for a button the user presses. A scheduler presses it instead,
which changes one thing fundamentally: the same day is now visited many times, so
generating has to be idempotent. Each reminder type is created at most once per user per
day, and a run that finds one already there does nothing rather than adding a second.

The loop wakes hourly rather than firing at a fixed minute. An app that is restarted at
09:05 would miss a 09:00 alarm entirely and the user would get nothing that day; waking
often and letting the "already sent today" check decide is restart-proof.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timezone, time, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import AsyncSessionLocal
from app.models import Notification, Program, User, UserProfile, WeightLog, WorkoutLog

logger = logging.getLogger(__name__)

WEIGHT_REMINDER = "weight_reminder"
WORKOUT_REMINDER = "workout_reminder"


async def _already_sent_on(db: AsyncSession, user_id: str, kind: str, day: date) -> bool:
    """Was this user already told this on that day?

    Bounded at both ends: an open-ended "since the day began" would also count a
    notification created later, which is only ever true when the day being generated is
    not the day the clock is on.
    """
    r = await db.execute(
        select(Notification.id).where(
            Notification.user_id == user_id,
            Notification.type == kind,
            Notification.created_at >= datetime.combine(day, time.min),
            Notification.created_at < datetime.combine(day + timedelta(days=1), time.min),
        ).limit(1)
    )
    return r.scalar_one_or_none() is not None


async def generate_for_user(db: AsyncSession, user_id: str) -> list[str]:
    """Create today's reminders for one user and return the types created.

    Nothing is created twice: repeating the call on the same day is how the scheduler
    works, and the user must not pay for that with a duplicate notification.
    """
    today = date.today()
    created: list[str] = []

    if not await _already_sent_on(db, user_id, WEIGHT_REMINDER, today):
        weighed = await db.execute(
            select(WeightLog.id).where(WeightLog.user_id == user_id, WeightLog.date == today).limit(1)
        )
        if weighed.scalar_one_or_none() is None:
            db.add(Notification(
                user_id=user_id,
                type=WEIGHT_REMINDER,
                title="Не забравяй да логнеш теглото си",
                body="Дневното тегло помага за точен анализ на прогреса.",
                scheduled_for=datetime.now(timezone.utc),
            ))
            created.append(WEIGHT_REMINDER)

    if not await _already_sent_on(db, user_id, WORKOUT_REMINDER, today):
        profile = (await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )).scalar_one_or_none()
        planned = profile.training_days_per_week if profile else None
        program = (await db.execute(
            select(Program).where(Program.user_id == user_id, Program.status == "active")
        )).scalar_one_or_none()

        if program and planned:
            week_start = today - timedelta(days=today.weekday())
            done = len((await db.execute(
                select(WorkoutLog.id).where(
                    WorkoutLog.user_id == user_id,
                    WorkoutLog.date >= week_start,
                    WorkoutLog.status == "completed",
                )
            )).scalars().all())
            remaining = planned - done
            if remaining > 0:
                db.add(Notification(
                    user_id=user_id,
                    type=WORKOUT_REMINDER,
                    title=f"Още {remaining} тренировки тази седмица",
                    body=f"Направил си {done} от {planned} тренировки.",
                    scheduled_for=datetime.utcnow(),
                ))
                created.append(WORKOUT_REMINDER)

    await db.commit()
    return created


async def generate_for_everyone(db: AsyncSession) -> dict[str, list[str]]:
    """Run the reminders for every active account, one failure at a time.

    One user's broken data must not stop the others from being reminded, so each is
    committed on its own and a failure is logged with the account it belongs to.
    """
    users = (await db.execute(select(User.id).where(User.is_active.is_(True)))).scalars().all()
    results: dict[str, list[str]] = {}
    for user_id in users:
        try:
            created = await generate_for_user(db, user_id)
        except Exception:
            await db.rollback()
            logger.warning("Could not generate reminders for user %s", user_id, exc_info=True)
            continue
        if created:
            results[user_id] = created
    return results


def is_within_sending_hours(now: datetime) -> bool:
    """Reminders are for the day ahead, not for the middle of the night.

    The check is on the hour rather than on a schedule so that an app started at any
    moment behaves the same as one that has been running since midnight.
    """
    return now.hour >= settings.NOTIFICATIONS_HOUR


async def run_scheduler() -> None:
    """Wake periodically and generate whatever today still needs.

    Never raises: a scheduler that dies on one bad cycle stops reminding everyone,
    silently, until the next deploy.
    """
    interval = timedelta(minutes=settings.NOTIFICATIONS_INTERVAL_MINUTES)
    logger.info(
        "Reminder scheduler started: every %d min, not before %02d:00",
        settings.NOTIFICATIONS_INTERVAL_MINUTES, settings.NOTIFICATIONS_HOUR,
    )
    # Cancellation is caught around the whole loop, including the sleep - that is where
    # a shutdown almost always lands, and a handler that only wraps the work would never
    # run. A failing cycle is caught inside, so it costs a tick and not the scheduler.
    try:
        while True:
            try:
                if is_within_sending_hours(datetime.now()):
                    async with AsyncSessionLocal() as db:
                        created = await generate_for_everyone(db)
                    if created:
                        logger.info("Reminders created for %d user(s)", len(created))
            except Exception:
                logger.warning("A reminder cycle failed; will try again next tick", exc_info=True)
            await asyncio.sleep(interval.total_seconds())
    except asyncio.CancelledError:
        logger.info("Reminder scheduler stopped")
        raise
