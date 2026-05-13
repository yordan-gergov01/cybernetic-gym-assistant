from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from deps import get_current_user
from models import Notification, Program, User, UserProfile, WeightLog, WorkoutLog
from schemas import NotificationOut

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
async def get_notifications(
    unread_only: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        q = q.where(Notification.is_read == False)
    q = q.order_by(Notification.created_at.desc()).limit(50)
    r = await db.execute(q)
    return r.scalars().all()


@router.patch("/{notification_id}/read", status_code=200)
async def mark_read(
    notification_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(Notification)
        .where(Notification.id == notification_id, Notification.user_id == user.id)
        .values(is_read=True)
    )
    await db.commit()
    return {"ok": True}


@router.patch("/read-all", status_code=200)
async def mark_all_read(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.execute(
        update(Notification).where(Notification.user_id == user.id, Notification.is_read == False).values(is_read=True)
    )
    await db.commit()
    return {"ok": True}


@router.post("/generate", status_code=201)
async def generate_notifications(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    created = []

    wr = await db.execute(select(WeightLog).where(WeightLog.user_id == user.id, WeightLog.date == today))
    if not wr.scalar_one_or_none():
        db.add(
            Notification(
                user_id=user.id,
                type="weight_reminder",
                title="Не забравяй да логнеш теглото си",
                body="Дневното тегло помага за точен анализ на прогреса.",
                scheduled_for=datetime.utcnow(),
            )
        )
        created.append("weight_reminder")

    pr_prof = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = pr_prof.scalar_one_or_none()
    training_days_per_week = profile.training_days_per_week if profile else None

    pr = await db.execute(select(Program).where(Program.user_id == user.id, Program.status == "active"))
    program = pr.scalar_one_or_none()

    if program and training_days_per_week:
        week_start = today - timedelta(days=today.weekday())
        wl = await db.execute(
            select(WorkoutLog).where(
                WorkoutLog.user_id == user.id,
                WorkoutLog.date >= week_start,
                WorkoutLog.status == "completed",
            )
        )
        done_this_week = len(wl.scalars().all())
        remaining = training_days_per_week - done_this_week

        if remaining > 0:
            db.add(
                Notification(
                    user_id=user.id,
                    type="workout_reminder",
                    title=f"Още {remaining} тренировки тази седмица",
                    body=f"Направил си {done_this_week} от {training_days_per_week} тренировки.",
                    scheduled_for=datetime.utcnow(),
                )
            )
            created.append("workout_reminder")

    await db.commit()
    return {"created": created}
