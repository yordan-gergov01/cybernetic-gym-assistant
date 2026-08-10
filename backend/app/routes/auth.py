from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import get_db
from app.deps import get_current_user
from app.models import User, UserProfile
from app.schemas import TokenResponse, UserLogin, UserRegister

router = APIRouter(prefix="/auth", tags=["auth"])


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
