import json
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.llm import openai_client
from app.db.database import get_db
from app.deps import get_current_user
from app.models import FatigueAssessment, Program, ProgramDay, ProgramExercise, ProgramWeek, User, UserProfile
from app.prompts.registry import get_prompt
from app.schemas import (
    FatigueAssessmentOut,
    FatigueAssessmentRequest,
    ProgramCreate,
    ProgramExerciseOut,
    ProgramGenerateRequest,
    ProgramOut,
)
from app.services.fatigue import assess_fatigue
from app.services.rag_pipeline import retrieve_context

router = APIRouter(prefix="/programs", tags=["programs"])



async def save_program_structure(db: AsyncSession, program: Program, weeks_data: list) -> Program:
    for w in weeks_data:
        week = ProgramWeek(
            program_id=program.id,
            week_number=w["week_number"],
            week_type=w.get("week_type", "loading"),
            notes=w.get("notes"),
        )
        db.add(week)
        await db.flush()
        for d in w.get("days", []):
            day = ProgramDay(
                week_id=week.id,
                day_number=d["day_number"],
                day_name=d.get("day_name"),
                is_rest_day=d.get("is_rest_day", False),
            )
            db.add(day)
            await db.flush()
            for i, ex in enumerate(d.get("exercises", [])):
                db.add(
                    ProgramExercise(
                        day_id=day.id,
                        order_index=i,
                        exercise_name=ex.get("exercise_name", ""),
                        muscle_group=ex.get("muscle_group"),
                        equipment=ex.get("equipment"),
                        sets_prescribed=ex.get("sets_prescribed"),
                        reps_min=ex.get("reps_min"),
                        reps_max=ex.get("reps_max"),
                        rir_target=ex.get("rir_target", 2),
                        rest_seconds=ex.get("rest_seconds", 120),
                        notes=ex.get("notes"),
                    )
                )
    return program


@router.get("", response_model=list[ProgramOut])
async def list_programs(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Program).where(Program.user_id == user.id).order_by(Program.created_at.desc()))
    return r.scalars().all()


@router.get("/{program_id}", response_model=ProgramOut)
async def get_program(program_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    r = await db.execute(
        select(Program)
        .where(Program.id == program_id, Program.user_id == user.id)
        .options(selectinload(Program.weeks).selectinload(ProgramWeek.days).selectinload(ProgramDay.exercises))
    )
    p = r.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Program not found")
    return p


@router.post("", response_model=ProgramOut, status_code=201)
async def create_manual_program(data: ProgramCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    end_date = None
    if data.start_date:
        end_date = data.start_date + timedelta(weeks=data.total_weeks)
    program = Program(
        user_id=user.id,
        name=data.name,
        description=data.description,
        created_by="manual",
        template_type=data.template_type,
        total_weeks=data.total_weeks,
        start_date=data.start_date,
        end_date=end_date,
    )
    db.add(program)
    await db.flush()
    await save_program_structure(db, program, [w.model_dump() for w in data.weeks])
    await db.commit()
    r = await db.execute(
        select(Program)
        .where(Program.id == program.id)
        .options(selectinload(Program.weeks).selectinload(ProgramWeek.days).selectinload(ProgramDay.exercises))
    )
    return r.scalar_one()


@router.post("/generate", response_model=ProgramOut, status_code=201)
async def generate_ai_program(data: ProgramGenerateRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    pr = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = pr.scalar_one_or_none()
    if not profile or not profile.training_status:
        raise HTTPException(400, "Complete your profile before generating a program")

    level_map_bg = {1: "Начинаещ", 2: "Средно напреднал", 3: "Напреднал"}
    calc = profile.calculator_results or {}
    energy = calc.get("energy", {})
    volume = calc.get("volume", {})
    lifts = calc.get("lifts", {})

    context = await retrieve_context(
        f"{level_map_bg.get(profile.training_status, 'трениращ')} клиент програма хипертрофия "
        f"{profile.training_days_per_week} дни седмично цел {profile.goal or ''}"
    )

    prompt = get_prompt("program_generation")(
        total_weeks=data.total_weeks,
        level_label=level_map_bg.get(profile.training_status, "Средно напреднал"),
        goal=profile.goal_validated or profile.goal,
        training_days_per_week=profile.training_days_per_week,
        available_equipment=profile.available_equipment,
        session_duration_min=profile.session_duration_min,
        priority_muscles=profile.priority_muscles,
        injuries=profile.injuries,
        exercise_preferences=profile.exercise_preferences,
        target_kcal=energy.get("target_kcal", "няма"),
        protein_g=energy.get("protein_g", "няма"),
        volume=volume,
        lifts=lifts,
        context=context,
    )

    response = await openai_client.chat.completions.create(
        model=settings.PRIMARY_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.3,
        max_tokens=4000,
    )
    prog_data = json.loads(response.choices[0].message.content)

    start = data.start_date or date.today()
    program = Program(
        user_id=user.id,
        name=prog_data.get("name", "AI Program"),
        description=prog_data.get("description"),
        created_by="ai",
        template_type=prog_data.get("template_type"),
        total_weeks=data.total_weeks,
        start_date=start,
        end_date=start + timedelta(weeks=data.total_weeks),
        goal=profile.goal_validated or profile.goal,
        training_status=profile.training_status,
        ai_context={"profile_snapshot": profile.calculator_results},
    )
    db.add(program)
    await db.flush()
    await save_program_structure(db, program, prog_data.get("weeks", []))
    await db.commit()

    r = await db.execute(
        select(Program)
        .where(Program.id == program.id)
        .options(selectinload(Program.weeks).selectinload(ProgramWeek.days).selectinload(ProgramDay.exercises))
    )
    return r.scalar_one()


@router.patch("/{program_id}/exercises/{exercise_id}", response_model=ProgramExerciseOut)
async def update_exercise(
    program_id: str,
    exercise_id: str,
    data: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _ = program_id, user
    r = await db.execute(select(ProgramExercise).where(ProgramExercise.id == exercise_id))
    ex = r.scalar_one_or_none()
    if not ex:
        raise HTTPException(404, "Exercise not found")
    for k, v in data.items():
        if hasattr(ex, k):
            setattr(ex, k, v)
    await db.commit()
    await db.refresh(ex)
    return ex


@router.delete("/{program_id}", status_code=204)
async def delete_program(program_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Program).where(Program.id == program_id, Program.user_id == user.id))
    p = r.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Program not found")
    await db.delete(p)
    await db.commit()


_DELOAD_LABEL_BG = {"continue": "продължи по план", "caution": "внимание / намали обема", "deload": "deload седмица"}


async def _explain_fatigue_bg(decision, answers: dict) -> str:
    """Phrase the deterministic deload decision for the user, grounded in the course.

    The decision itself is already fixed by services.fatigue.assess_fatigue; the LLM
    only rewords it. On any failure we fall back to the deterministic Bulgarian text
    so the user always gets a correct, non-empty explanation.
    """
    try:
        context = await retrieve_context(
            f"deload умора възстановяване периодизация {' '.join(decision.factors)}"
        )
        prompt = get_prompt("fatigue_explanation")(
            decision_label=_DELOAD_LABEL_BG.get(decision.decision, decision.decision),
            factors=decision.factors,
            answers=answers,
            context=context,
        )
        resp = await openai_client.chat.completions.create(
            model=settings.PRIMARY_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300,
        )
        text = (resp.choices[0].message.content or "").strip()
        return text or decision.recommendation_bg
    except Exception:
        return decision.recommendation_bg


@router.post("/{program_id}/fatigue", response_model=FatigueAssessmentOut, status_code=201)
async def submit_fatigue_assessment(
    program_id: str,
    data: FatigueAssessmentRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    r = await db.execute(select(Program).where(Program.id == program_id, Program.user_id == user.id))
    program = r.scalar_one_or_none()
    if not program:
        raise HTTPException(404, "Program not found")

    answers = data.answers.model_dump()
    decision = assess_fatigue(answers)
    reasoning = await _explain_fatigue_bg(decision, answers)

    assessment = FatigueAssessment(
        user_id=user.id,
        program_id=program_id,
        week_number=data.week_number,
        answers=answers,
        agent_decision=decision.decision,
        agent_reasoning=reasoning,
    )
    db.add(assessment)
    await db.commit()
    await db.refresh(assessment)
    return assessment


@router.get("/{program_id}/fatigue", response_model=list[FatigueAssessmentOut])
async def list_fatigue_assessments(
    program_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    r = await db.execute(
        select(FatigueAssessment)
        .where(FatigueAssessment.program_id == program_id, FatigueAssessment.user_id == user.id)
        .order_by(FatigueAssessment.assessed_at.desc())
    )
    return r.scalars().all()
