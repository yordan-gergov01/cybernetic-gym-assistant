from collections import deque
import statistics
from datetime import date, timedelta

import numpy as np
from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from deps import get_current_user
from models import User, WeightLog
from schemas import WeightLogCreate, WeightLogOut

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
    if len(entries) < 3:
        return {"status": "insufficient_data", "entries": []}
    weights = [e.weight_kg for e in entries]
    window = deque(maxlen=7)
    avgs = []
    for i, e in enumerate(entries):
        window.append(e.weight_kg)
        if len(window) >= 3:
            avgs.append(
                {"date": str(e.date), "avg_weight": round(statistics.mean(window), 2), "raw_weight": e.weight_kg}
            )
    x = np.arange(len(weights))
    slope = float(np.polyfit(x, weights, 1)[0])
    weekly_rate = round(slope * 7, 3)
    return {
        "status": "ok",
        "current_weight": round(statistics.mean(weights[-7:]) if len(weights) >= 7 else weights[-1], 2),
        "start_weight": round(statistics.mean(weights[:7]) if len(weights) >= 7 else weights[0], 2),
        "weekly_rate_kg": weekly_rate,
        "direction": "down" if weekly_rate < -0.05 else "up" if weekly_rate > 0.05 else "stable",
        "weekly_averages": avgs[-12:],
        "total_entries": len(entries),
    }
