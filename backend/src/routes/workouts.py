import json
import logging
from datetime import date as date_type
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.config import settings
from db.database import get_db
from deps import get_current_user
from models import ProgramExercise, User, WorkoutLog, WorkoutSet
from prompts.registry import get_prompt
from schemas import WorkoutLogCreate, WorkoutLogOut

router = APIRouter(prefix="/workouts", tags=["workouts"])
logger = logging.getLogger(__name__)

openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


@router.post("", response_model=WorkoutLogOut, status_code=201)
async def log_workout(data: WorkoutLogCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    log = WorkoutLog(
        user_id=user.id,
        program_id=data.program_id,
        day_id=data.day_id,
        date=data.date,
        started_at=datetime.utcnow(),
        notes=data.notes,
    )
    db.add(log)
    await db.flush()
    for s in data.sets:
        db.add(WorkoutSet(workout_log_id=log.id, **s.model_dump()))
    log.finished_at = datetime.utcnow()
    log.duration_min = int((log.finished_at - log.started_at).seconds / 60)
    await db.commit()

    if data.day_id:
        await update_next_targets(db, data.day_id, data.sets)

    r = await db.execute(select(WorkoutLog).where(WorkoutLog.id == log.id).options(selectinload(WorkoutLog.sets)))
    return r.scalar_one()


async def update_next_targets(db: AsyncSession, day_id: str, sets: list):
    r = await db.execute(select(ProgramExercise).where(ProgramExercise.day_id == day_id))
    exercises = r.scalars().all()
    if not exercises:
        return

    logged_by_exercise = {}
    for s in sets:
        name = s.exercise_name
        if name not in logged_by_exercise:
            logged_by_exercise[name] = []
        logged_by_exercise[name].append({"weight_kg": s.weight_kg, "reps": s.reps, "rir": s.rir_actual})

    prompt = get_prompt("progression_targets")(logged_by_exercise)

    try:
        resp = await openai_client.chat.completions.create(
            model=settings.PRIMARY_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=500,
        )
        targets = json.loads(resp.choices[0].message.content)
        for ex in exercises:
            if ex.exercise_name in targets:
                t = targets[ex.exercise_name]
                ex.target_weight_kg = t.get("weight_kg")
                ex.target_reps = t.get("reps")
                ex.target_note = t.get("note")
        await db.commit()
    except Exception:
        logger.warning("Failed to compute next-session targets for day %s; workout was saved without them",
                       day_id, exc_info=True)


@router.get("", response_model=list[WorkoutLogOut])
async def list_workouts(limit: int = 30, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    r = await db.execute(
        select(WorkoutLog)
        .where(WorkoutLog.user_id == user.id)
        .options(selectinload(WorkoutLog.sets))
        .order_by(WorkoutLog.date.desc())
        .limit(limit)
    )
    return r.scalars().all()


@router.get("/week/summary")
async def week_summary(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    week_start = date_type.today() - timedelta(days=date_type.today().weekday())
    r = await db.execute(
        select(WorkoutLog)
        .where(WorkoutLog.user_id == user.id, WorkoutLog.date >= week_start)
        .options(selectinload(WorkoutLog.sets))
    )
    logs = r.scalars().all()
    return {
        "week_start": str(week_start),
        "workouts_done": len(logs),
        "total_sets": sum(len(l.sets) for l in logs),
        "dates": [str(l.date) for l in logs],
    }


@router.get("/{workout_id}", response_model=WorkoutLogOut)
async def get_workout(workout_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    r = await db.execute(
        select(WorkoutLog)
        .where(WorkoutLog.id == workout_id, WorkoutLog.user_id == user.id)
        .options(selectinload(WorkoutLog.sets))
    )
    w = r.scalar_one_or_none()
    if not w:
        raise HTTPException(404, "Workout not found")
    return w
