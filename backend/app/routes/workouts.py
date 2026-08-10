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
from app.schemas import (
    CalendarDayOut,
    ExerciseStrengthOut,
    LastSessionOut,
    MuscleVolumeOut,
    SessionEstimateOut,
    TodayOut,
    WorkoutLogCreate,
    WorkoutLogOut,
)
from app.services.progression import compute_next_target
from app.services.strength_progress import strength_by_exercise
from app.services.training_week import build_today

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


@router.get("/today", response_model=TodayOut)
async def today(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """What to train today, where that sits in the program, and the week so far.

    The whole decision - which session is next, whether today is a rest day, how much
    volume each muscle has had - is made here. Doing it in the client would mean two
    implementations of the same rules, drifting apart.
    """
    view = await build_today(db, user.id, date_type.today())
    if not view:
        raise HTTPException(404, "Още нямаш програма. Създай програма, за да започнеш.")
    return TodayOut(
        program_id=view.program_id,
        program_name=view.program_name,
        template_type=view.template_type,
        goal=view.goal,
        week_number=view.week_number,
        total_weeks=view.total_weeks,
        is_rest_day=view.is_rest_day,
        trained_today=view.trained_today,
        weighed_in_today=view.weighed_in_today,
        sessions_this_week=view.sessions_this_week,
        sessions_planned=view.sessions_planned,
        calendar=[
            CalendarDayOut(date=d.date, trained=d.trained, is_today=d.is_today) for d in view.calendar
        ],
        day_id=view.day_id,
        day_name=view.day_name,
        exercises=view.exercises,
        estimate=(
            SessionEstimateOut(
                exercise_count=view.estimate.exercise_count,
                total_sets=view.estimate.total_sets,
                minutes=view.estimate.minutes,
            )
            if view.estimate
            else None
        ),
        last_session=(
            LastSessionOut(
                date=view.last_session.date,
                tonnage_kg=view.last_session.tonnage_kg,
                working_sets=view.last_session.working_sets,
            )
            if view.last_session
            else None
        ),
        weekly_volume=[
            MuscleVolumeOut(
                muscle_group=v.muscle_group, sets_done=v.sets_done, sets_target=v.sets_target
            )
            for v in view.weekly_volume
        ],
    )


@router.get("/strength", response_model=list[ExerciseStrengthOut])
async def strength_progress(
    weeks: int = 4,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Estimated max per exercise over the last `weeks`, and how much it moved.

    Computed here, from the same first-work-set benchmark the progression engine uses,
    so the client never runs a second version of the Epley formula.
    """
    if not 1 <= weeks <= 52:
        raise HTTPException(400, "Периодът трябва да е между 1 и 52 седмици.")
    results = await strength_by_exercise(db, user.id, weeks=weeks, today=date_type.today())
    return [
        ExerciseStrengthOut(
            exercise_name=e.exercise_name,
            muscle_group=e.muscle_group,
            best_e1rm=e.best_e1rm,
            change_kg=e.change_kg,
            sessions=e.sessions,
            points=e.points,
        )
        for e in results
    ]


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
        raise HTTPException(404, "Тренировката не е намерена.")
    return w
