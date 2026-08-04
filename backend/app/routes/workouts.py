import logging
from datetime import date as date_type
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.deps import get_current_user
from app.models import ProgramExercise, User, UserProfile, WorkoutLog, WorkoutSet
from app.schemas import WorkoutLogCreate, WorkoutLogOut
from app.services.progression import compute_next_target

router = APIRouter(prefix="/workouts", tags=["workouts"])
logger = logging.getLogger(__name__)


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
        await update_next_targets(db, user.id, data.day_id, data.sets)

    r = await db.execute(select(WorkoutLog).where(WorkoutLog.id == log.id).options(selectinload(WorkoutLog.sets)))
    return r.scalar_one()


async def update_next_targets(db: AsyncSession, user_id: str, day_id: str, sets: list):
    r = await db.execute(select(ProgramExercise).where(ProgramExercise.day_id == day_id))
    exercises = r.scalars().all()
    if not exercises:
        return

    # The user's gym decides what load jumps are actually possible.
    pr = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = pr.scalar_one_or_none()
    barbell_step = profile.min_barbell_increment_kg if profile else None
    dumbbell_step = profile.min_dumbbell_increment_kg if profile else None

    logged_by_exercise: dict[str, list[dict]] = {}
    # Sorted by set number, because "the first work set" has to mean the first one
    # performed, not whichever the client happened to send first.
    for s in sorted(sets, key=lambda s: s.set_number):
        logged_by_exercise.setdefault(s.exercise_name, []).append(
            # is_warmup travels with the set: the benchmark is the first WORK set, so a
            # warm-up must not be mistaken for it.
            {"weight_kg": s.weight_kg, "reps": s.reps, "rir": s.rir_actual, "is_warmup": s.is_warmup}
        )

    try:
        for ex in exercises:
            logged = logged_by_exercise.get(ex.exercise_name)
            if not logged:
                continue
            target = compute_next_target(
                muscle_group=ex.muscle_group,
                rir_target=ex.rir_target,
                reps_min=ex.reps_min,
                reps_max=ex.reps_max,
                logged_sets=logged,
                min_barbell_increment_kg=barbell_step,
                min_dumbbell_increment_kg=dumbbell_step,
            )
            ex.target_weight_kg = target.weight_kg
            ex.target_reps = target.reps
            ex.target_note = target.note
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
