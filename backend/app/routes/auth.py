import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    hash_password,
    hash_reset_token,
    new_reset_token,
    verify_password,
)
from app.db.database import get_db
from app.deps import get_current_user
from app.models import PasswordResetToken, User, UserProfile
from app.schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    MessageResponse,
    ResetPasswordRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
)
from app.services.mailer import send_password_reset

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


def normalize_email(email: str) -> str:
    """Email addresses are matched case-insensitively.

    Phone keyboards and browsers capitalise the first letter of a field by default, so
    the same person signs up as "Ivan@..." and signs in as "ivan@..." without ever
    noticing the difference. A case-sensitive lookup turns that into "wrong password",
    which is both wrong and impossible for the user to diagnose.
    """
    return email.strip().lower()


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    email = normalize_email(data.email)
    existing = await db.execute(select(User).where(func.lower(User.email) == email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Вече има регистрация с този имейл. Влез в профила си.")
    user = User(
        email=email,
        hashed_password=hash_password(data.password),
        name=data.name,
    )
    db.add(user)
    await db.flush()
    db.add(UserProfile(user_id=user.id))
    await db.commit()
    await db.refresh(user)
    return TokenResponse(
        access_token=create_access_token(user.id),
        user_id=user.id,
        name=user.name,
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    # Compared on the stored value too, so accounts created before addresses were
    # normalised still match.
    result = await db.execute(
        select(User).where(func.lower(User.email) == normalize_email(data.email))
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Грешен имейл или парола.")
    return TokenResponse(
        access_token=create_access_token(user.id),
        user_id=user.id,
        name=user.name,
    )


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "name": user.name}


# The same answer whether or not the address is registered. Anything else turns this
# endpoint into a way to find out who has an account here.
_RESET_SENT_BG = (
    "Ако има профил с този имейл, изпратихме линк за смяна на паролата. "
    "Линкът важи един час."
)


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Email a one-time link for setting a new password."""
    result = await db.execute(select(User).where(func.lower(User.email) == normalize_email(data.email)))
    user = result.scalar_one_or_none()

    if user and user.is_active:
        # Any earlier link is spent the moment a new one is asked for, so a forwarded
        # or shoulder-surfed email stops working as soon as the real owner retries.
        previous = await db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None)
            )
        )
        # The columns are timezone-aware, so the values compared against them must be
        # too - a naive datetime and one from Postgres cannot be compared at all.
        now = datetime.now(timezone.utc)
        for token in previous.scalars().all():
            token.used_at = now

        raw, token_hash = new_reset_token()
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=now + timedelta(minutes=settings.PASSWORD_RESET_TTL_MINUTES),
            )
        )
        await db.commit()

        await send_password_reset(
            user.email,
            f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={raw}",
            settings.PASSWORD_RESET_TTL_MINUTES,
        )

    return MessageResponse(detail=_RESET_SENT_BG)


@router.post("/reset-password", response_model=TokenResponse)
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Set a new password from a link, and sign the user straight in.

    Signing in here is the point of the flow: someone who has just proved they own the
    mailbox should not be sent back to a login form to type the password they set two
    seconds ago.
    """
    result = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == hash_reset_token(data.token))
    )
    token = result.scalar_one_or_none()

    # One message for every kind of bad token: which one it is tells the sender nothing
    # they need, and the answer is the same either way - ask for a new link.
    if not token or token.used_at or token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(400, "Линкът е невалиден или изтекъл. Заяви нов.")

    user = await db.get(User, token.user_id)
    if not user or not user.is_active:
        raise HTTPException(400, "Линкът е невалиден или изтекъл. Заяви нов.")

    user.hashed_password = hash_password(data.new_password)
    token.used_at = datetime.now(timezone.utc)
    await db.commit()

    logger.info("Password reset completed for user %s", user.id)
    return TokenResponse(access_token=create_access_token(user.id), user_id=user.id, name=user.name)


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    data: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change the password of the signed-in user.

    The current password is required even though the session already proves who this is:
    an unattended phone is the likeliest attacker here, and knowing the old password is
    what an unattended phone does not.
    """
    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(400, "Текущата парола не е вярна.")
    if data.current_password == data.new_password:
        raise HTTPException(400, "Новата парола трябва да е различна от текущата.")

    user.hashed_password = hash_password(data.new_password)
    await db.commit()
    return MessageResponse(detail="Паролата е сменена.")
