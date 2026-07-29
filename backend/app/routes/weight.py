from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.deps import get_current_user
from app.models import NutritionTarget, User, UserProfile, WeightLog
from app.schemas import WeightLogCreate, WeightLogOut
from app.services.weight_trend import analyze_trend, recommend_calorie_adjustment

router = APIRouter(prefix="/weight", tags=["weight"])


@router.post("", response_model=WeightLogOut, status_code=201)
async def log_weight(
    data: WeightLogCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(delete(WeightLog).where(WeightLog.user_id == user.id, WeightLog.date == data.date))
    entry = WeightLog(user_id=user.id, **data.model_dump())
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.get("", response_model=list[WeightLogOut])
async def get_weight_logs(
    days: int = 90,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cutoff = date.today() - timedelta(days=days)
    result = await db.execute(
        select(WeightLog)
        .where(WeightLog.user_id == user.id, WeightLog.date >= cutoff)
        .order_by(WeightLog.date)
    )
    return result.scalars().all()


@router.get("/trend")
async def get_trend(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WeightLog).where(WeightLog.user_id == user.id).order_by(WeightLog.date))
    entries = result.scalars().all()
    trend = analyze_trend([(e.date, e.weight_kg) for e in entries])
    if trend is None:
        return {"status": "insufficient_data", "entries": []}
    return {
        "status": "ok",
        "current_weight": trend.current_weight,
        "weekly_rate_kg": trend.weekly_rate_kg,
        "direction": trend.direction,
        "trend_points": trend.smoothed,
        "total_entries": trend.points,
    }


@router.get("/coaching")
async def get_coaching(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Weight trend plus a deterministic calorie-adjustment recommendation for the goal."""
    result = await db.execute(select(WeightLog).where(WeightLog.user_id == user.id).order_by(WeightLog.date))
    entries = result.scalars().all()
    trend = analyze_trend([(e.date, e.weight_kg) for e in entries])
    if trend is None:
        return {"status": "insufficient_data", "message": "Логни поне 3 измервания за анализ на тренда."}

    pr = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = pr.scalar_one_or_none()
    goal = (profile.goal_validated or profile.goal) if profile else None

    nt = await db.execute(select(NutritionTarget).where(NutritionTarget.user_id == user.id))
    nt_row = nt.scalar_one_or_none()
    current_calories = nt_row.calories if nt_row else None

    advice = recommend_calorie_adjustment(
        goal=goal, actual_weekly_rate_kg=trend.weekly_rate_kg, current_calories=current_calories
    )
    return {
        "status": "ok",
        "current_weight": trend.current_weight,
        "weekly_rate_kg": trend.weekly_rate_kg,
        "direction": trend.direction,
        "goal": advice.goal,
        "target_weekly_rate_kg": advice.target_weekly_rate_kg,
        "on_track": advice.on_track,
        "calorie_delta": advice.calorie_delta,
        "new_calorie_target": advice.new_calorie_target,
        "recommendation": advice.note,
    }
