from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.deps import get_current_user
from app.models import Notification, User
from app.schemas import NotificationOut
from app.services.notifications import generate_for_user

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
    """Generate today's reminders for the caller.

    The scheduler does this on its own; the endpoint stays because the app can ask for a
    refresh when it opens, and because it is how the rules are exercised by hand.
    """
    return {"created": await generate_for_user(db, user.id)}
