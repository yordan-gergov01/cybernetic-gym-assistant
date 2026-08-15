import json
import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.llm import openai_client
from app.db.database import get_db
from app.deps import get_current_user
from app.domain import exercise_library
from app.domain.program_design import (
    MIN_WEEKLY_FREQUENCY,
    frequency_violations,
    plan_muscle_adjustment,
    recommend_split,
    weekly_frequency,
)
from app.domain.plateau import MAX_PROGRAM_WEEKS, intensified_rep_range
from app.models import FatigueAssessment, Program, ProgramDay, ProgramExercise, ProgramWeek, User, UserProfile
from app.prompts.registry import get_prompt
from app.schemas import (
    ExerciseIntensifyRequest,
    ExerciseProgressOut,
    ExerciseSwapRequest,
    FatigueAssessmentOut,
    FatigueAssessmentRequest,
    MuscleAdjustRequest,
    PlateauBreakerOut,
    ProgramAdjustmentOut,
    ProgramCreate,
    ProgramExerciseOut,
    ProgramGenerateRequest,
    ProgramOut,
    ProgramReviewOut,
    ProgramSummary,
)
from app.services.fatigue import assess_fatigue
from app.services.program_adjust import (
    apply_muscle_adjustment,
    apply_rep_range,
    apply_swap,
    exercise_rows,
    program_weeks,
    template_days,
)
from app.services.program_progress import review_program
from app.services.rag_pipeline import retrieve_context

router = APIRouter(prefix="/programs", tags=["programs"])
logger = logging.getLogger(__name__)



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


@router.get("", response_model=list[ProgramSummary])
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
        raise HTTPException(404, "Програмата не е намерена.")
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
        raise HTTPException(400, "Попълни профила си, преди да генерираме програма.")

    if data.total_weeks > MAX_PROGRAM_WEEKS:
        raise HTTPException(
            400,
            f"Максималната дължина на програма е {MAX_PROGRAM_WEEKS} седмици. "
            "Ако прогресът продължава, програмата се удължава седмица по седмица.",
        )

    level_map_bg = {1: "Начинаещ", 2: "Средно напреднал", 3: "Напреднал"}
    calc = profile.calculator_results or {}
    energy = calc.get("energy", {})
    volume = calc.get("volume", {})
    lifts = calc.get("lifts", {})

    context = await retrieve_context(
        f"{level_map_bg.get(profile.training_status, 'трениращ')} клиент програма хипертрофия "
        f"{profile.training_days_per_week} дни седмично цел {profile.goal or ''}"
    )

    # The split is a rule from the course, not something the model gets to choose.
    split = recommend_split(profile.training_days_per_week or 3)

    async def ask_model(feedback: str = "") -> dict:
        prompt = get_prompt("program_week_template")(
            level_label=level_map_bg.get(profile.training_status, "Средно напреднал"),
            goal=profile.goal_validated or profile.goal,
            training_days_per_week=profile.training_days_per_week,
            split_description=split.description_bg,
            split_rationale=split.rationale_bg,
            min_frequency=MIN_WEEKLY_FREQUENCY,
            available_equipment=profile.available_equipment,
            equipment_details=profile.equipment_details,
            session_duration_min=profile.session_duration_min,
            priority_muscles=profile.priority_muscles,
            avoid_growth_muscles=profile.avoid_growth_muscles,
            injuries=profile.injuries,
            exercise_preferences=profile.exercise_preferences,
            other_activities=profile.other_activities,
            volume=volume,
            lifts=lifts,
            context=context,
            retry_feedback=feedback,
        )
        response = await openai_client.chat.completions.create(
            model=settings.PRIMARY_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=4000,
        )
        choice = response.choices[0]
        # A truncated response yields invalid JSON, and a bare parse error tells the
        # user nothing about what to do; name the cause instead.
        if choice.finish_reason == "length":
            logger.error("Program generation hit the token limit for user %s", user.id)
            raise HTTPException(502, "Отговорът на модела беше отрязан. Опитай пак или намали броя тренировъчни дни.")
        try:
            return json.loads(choice.message.content)
        except json.JSONDecodeError:
            logger.error("Program generation returned invalid JSON for user %s: %.400s",
                         user.id, choice.message.content, exc_info=True)
            raise HTTPException(502, "Моделът върна невалиден отговор. Опитай пак.") from None

    prog_data = await ask_model()
    template_days = prog_data.get("days") or []
    if not template_days:
        raise HTTPException(502, "Моделът не върна тренировъчни дни. Опитай пак.")

    # Verify the methodology rule rather than trusting the model to have followed it.
    violations = frequency_violations(template_days)
    if violations:
        logger.warning("Generated program under-trains %s for user %s; retrying once",
                       ", ".join(violations), user.id)
        retry_data = await ask_model(
            f"Следните мускулни групи бяха тренирани по-малко от {MIN_WEEKLY_FREQUENCY} пъти седмично: "
            f"{', '.join(violations)}. Преразпредели упражненията така, че всяка от тях да се тренира "
            f"поне {MIN_WEEKLY_FREQUENCY} пъти в различни дни."
        )
        retry_days = retry_data.get("days") or []
        if retry_days and not frequency_violations(retry_days):
            prog_data, template_days, violations = retry_data, retry_days, []
        elif retry_days:
            prog_data, template_days = retry_data, retry_days
            violations = frequency_violations(retry_days)

    # The LLM designs one week; the mesocycle is that week repeated. Load progression
    # between sessions is handled deterministically by services/progression.py.
    weeks_data = [
        {
            "week_number": week_number,
            "week_type": "loading",
            "days": template_days,
        }
        for week_number in range(1, data.total_weeks + 1)
    ]

    description = prog_data.get("description")
    if violations:
        # Two attempts and the frequency rule still is not met. Ship the program rather
        # than leaving the user with nothing, but carry the shortfall in the description
        # so it is not passed off as a correct plan.
        logger.error("Program for user %s still under-trains %s after retry", user.id, ", ".join(violations))
        description = (
            f"{description or ''}\n\n⚠️ Внимание: {', '.join(violations)} се тренира(т) по-рядко от "
            f"{MIN_WEEKLY_FREQUENCY}× седмично. Прегледай програмата или я генерирай отново."
        ).strip()

    # Generating a new program is also how the user swaps out one they are done with.
    # Leaving the old one active would make "the active program" ambiguous everywhere.
    if data.archive_active:
        previous = await db.execute(
            select(Program).where(Program.user_id == user.id, Program.status == "active")
        )
        for old in previous.scalars().all():
            old.status = "archived"

    start = data.start_date or date.today()
    program = Program(
        user_id=user.id,
        name=prog_data.get("name", "AI Program"),
        description=description,
        created_by="ai",
        template_type=prog_data.get("template_type"),
        total_weeks=data.total_weeks,
        start_date=start,
        end_date=start + timedelta(weeks=data.total_weeks),
        goal=profile.goal_validated or profile.goal,
        training_status=profile.training_status,
        ai_context={
            "profile_snapshot": profile.calculator_results,
            "split": split.name,
            "weekly_frequency": weekly_frequency(template_days),
            "frequency_violations": violations,
        },
    )
    db.add(program)
    await db.flush()
    await save_program_structure(db, program, weeks_data)
    await db.commit()

    r = await db.execute(
        select(Program)
        .where(Program.id == program.id)
        .options(selectinload(Program.weeks).selectinload(ProgramWeek.days).selectinload(ProgramDay.exercises))
    )
    return r.scalar_one()


async def _owned_program(db: AsyncSession, program_id: str, user: User) -> Program:
    r = await db.execute(select(Program).where(Program.id == program_id, Program.user_id == user.id))
    program = r.scalar_one_or_none()
    if not program:
        raise HTTPException(404, "Програмата не е намерена.")
    return program


@router.patch("/{program_id}/exercises/{exercise_id}", response_model=ProgramExerciseOut)
async def update_exercise(
    program_id: str,
    exercise_id: str,
    data: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    program = await _owned_program(db, program_id, user)
    # The row is reached through the program, not by its id alone: an id on its own says
    # nothing about who owns it, and without the join any signed-in user could edit
    # somebody else's program by guessing one.
    r = await db.execute(
        select(ProgramExercise)
        .join(ProgramDay, ProgramExercise.day_id == ProgramDay.id)
        .join(ProgramWeek, ProgramDay.week_id == ProgramWeek.id)
        .where(ProgramExercise.id == exercise_id, ProgramWeek.program_id == program.id)
    )
    ex = r.scalar_one_or_none()
    if not ex:
        raise HTTPException(404, "Упражнението не е намерено в програмата.")
    for k, v in data.items():
        if hasattr(ex, k):
            setattr(ex, k, v)
    await db.commit()
    await db.refresh(ex)
    return ex


@router.post("/{program_id}/exercises/swap", response_model=ProgramAdjustmentOut)
async def swap_exercise(
    program_id: str,
    data: ExerciseSwapRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Replace a prescribed exercise with one from the course library, in every week.

    Deliberately not gated on the review: replacing an exercise is also how a user deals
    with a machine that is taken, an injury or a movement they simply cannot perform,
    and refusing that until something stalls would make the program unusable.
    """
    program = await _owned_program(db, program_id, user)

    replacement = exercise_library.find(data.replacement_name)
    if not replacement:
        raise HTTPException(
            404, f"Упражнението „{data.replacement_name}“ не е в библиотеката на курса."
        )

    weeks = await program_weeks(db, program.id)
    rows = exercise_rows(weeks, data.exercise_name)
    if not rows:
        raise HTTPException(404, f"„{data.exercise_name}“ не е в тази програма.")
    if rows[0].exercise_name == replacement.name:
        raise HTTPException(400, "Избери упражнение, различно от текущото.")

    return await apply_swap(db, rows, replacement)


@router.post("/{program_id}/exercises/intensify", response_model=ProgramAdjustmentOut)
async def intensify_exercise(
    program_id: str,
    data: ExerciseIntensifyRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lower the rep target of a stalled exercise (Periodization & progress, p.24).

    Gated on the review, because intensification is the course's answer to a *measured*
    stall. Applied to a lift that is still progressing it would only cut its volume.
    """
    program = await _owned_program(db, program_id, user)

    review = await review_program(db, program)
    if review.decision.action != "adjust_exercise" or review.decision.exercise_name != data.exercise_name:
        raise HTTPException(409, review.decision.reason_bg)

    weeks = await program_weeks(db, program.id)
    rows = exercise_rows(weeks, data.exercise_name)
    if not rows:
        raise HTTPException(404, f"„{data.exercise_name}“ не е в тази програма.")

    new_range = intensified_rep_range(rows[0].reps_min, rows[0].reps_max)
    if not new_range:
        raise HTTPException(
            409,
            "Повторенията не могат да слязат по-ниско без да падне обемът под нужния за "
            "растеж. Смени упражнението с алтернатива.",
        )

    return await apply_rep_range(db, rows, new_range)


@router.post("/{program_id}/muscles/adjust", response_model=ProgramAdjustmentOut)
async def adjust_muscle(
    program_id: str,
    data: MuscleAdjustRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Train a stalling muscle group more often, or - if the week is full - harder.

    The order is the course's, and the volume ceiling is the profile's own optimal
    weekly set count, so this can never turn a recovery problem into a volume spiral.
    """
    program = await _owned_program(db, program_id, user)

    review = await review_program(db, program)
    decided_for = (review.decision.muscle_group or "").strip().lower()
    if review.decision.action != "adjust_muscle" or decided_for != data.muscle_group.strip().lower():
        raise HTTPException(409, review.decision.reason_bg)

    pr = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = pr.scalar_one_or_none()
    volume = ((profile.calculator_results or {}).get("volume") or {}) if profile else {}
    if not isinstance(volume, dict):
        logger.warning("Profile %s has a non-dict volume target; the set ceiling is skipped", user.id)
        volume = {}

    weeks = await program_weeks(db, program.id)
    adjustment = plan_muscle_adjustment(
        template_days(weeks),
        data.muscle_group,
        target_weekly_sets=volume.get(data.muscle_group.strip().lower()),
    )
    if adjustment.action == "none":
        raise HTTPException(409, adjustment.reason_bg)

    return await apply_muscle_adjustment(db, weeks, adjustment)


@router.delete("/{program_id}", status_code=204)
async def delete_program(program_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Program).where(Program.id == program_id, Program.user_id == user.id))
    p = r.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Програмата не е намерена.")
    await db.delete(p)
    await db.commit()


@router.get("/{program_id}/review", response_model=ProgramReviewOut)
async def review_program_progress(
    program_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Should this program continue, and if not, what exactly needs to change?

    Every judgement comes from the logged first work sets via domain/plateau.py - no
    model is involved in the decision.
    """
    r = await db.execute(select(Program).where(Program.id == program_id, Program.user_id == user.id))
    program = r.scalar_one_or_none()
    if not program:
        raise HTTPException(404, "Програмата не е намерена.")

    review = await review_program(db, program)
    return ProgramReviewOut(
        action=review.decision.action,
        scope=review.decision.scope,
        reason_bg=review.decision.reason_bg,
        muscle_group=review.decision.muscle_group,
        exercise_name=review.decision.exercise_name,
        new_rep_target=review.new_rep_target,
        total_weeks=program.total_weeks,
        max_weeks=MAX_PROGRAM_WEEKS,
        exercises=[
            ExerciseProgressOut(
                exercise_name=e.exercise_name,
                muscle_group=e.muscle_group,
                status=e.status,
                sessions_since_best=e.sessions_since_best,
                best_e1rm=e.best_e1rm,
                latest_e1rm=e.latest_e1rm,
                change_pct=e.last_session.change_pct if e.last_session else None,
            )
            for e in review.exercises
        ],
        breakers=[
            PlateauBreakerOut(exercise_name=b.exercise_name, weight_kg=b.weight_kg, reps=b.reps)
            for b in review.breakers
        ],
        sessions_analysed=review.sessions_analysed,
        skipped_exercises=review.skipped_exercises,
    )


@router.post("/{program_id}/extend", response_model=ProgramOut)
async def extend_program(
    program_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add one more week to a program that is still producing progress.

    One week at a time on purpose: any larger step reintroduces exactly the arbitrary
    scheduling the course argues against (Periodization p.44). The extension is refused
    while something is stalling - a stall is answered by changing the program, not by
    running the same one longer.
    """
    r = await db.execute(
        select(Program)
        .where(Program.id == program_id, Program.user_id == user.id)
        .options(selectinload(Program.weeks).selectinload(ProgramWeek.days).selectinload(ProgramDay.exercises))
    )
    program = r.scalar_one_or_none()
    if not program:
        raise HTTPException(404, "Програмата не е намерена.")

    if program.total_weeks >= MAX_PROGRAM_WEEKS:
        raise HTTPException(
            400,
            f"Програмата вече е {program.total_weeks} седмици - максимумът е {MAX_PROGRAM_WEEKS}. "
            "Време е за нова програма.",
        )

    review = await review_program(db, program)
    if review.decision.action != "extend":
        raise HTTPException(409, review.decision.reason_bg)

    last_week = max(program.weeks, key=lambda w: w.week_number, default=None)
    if not last_week:
        raise HTTPException(400, "Програмата няма седмици, които да бъдат повторени.")

    new_week = ProgramWeek(
        program_id=program.id,
        week_number=last_week.week_number + 1,
        week_type=last_week.week_type,
        notes=last_week.notes,
    )
    db.add(new_week)
    await db.flush()
    for day in sorted(last_week.days, key=lambda d: d.day_number):
        new_day = ProgramDay(
            week_id=new_week.id,
            day_number=day.day_number,
            day_name=day.day_name,
            is_rest_day=day.is_rest_day,
            notes=day.notes,
        )
        db.add(new_day)
        await db.flush()
        for ex in sorted(day.exercises, key=lambda e: e.order_index):
            db.add(
                ProgramExercise(
                    day_id=new_day.id,
                    order_index=ex.order_index,
                    exercise_name=ex.exercise_name,
                    muscle_group=ex.muscle_group,
                    equipment=ex.equipment,
                    sets_prescribed=ex.sets_prescribed,
                    reps_min=ex.reps_min,
                    reps_max=ex.reps_max,
                    rir_target=ex.rir_target,
                    rest_seconds=ex.rest_seconds,
                    notes=ex.notes,
                )
            )

    program.total_weeks += 1
    if program.start_date:
        program.end_date = program.start_date + timedelta(weeks=program.total_weeks)
    await db.commit()

    r = await db.execute(
        select(Program)
        .where(Program.id == program.id)
        .options(selectinload(Program.weeks).selectinload(ProgramWeek.days).selectinload(ProgramDay.exercises))
    )
    return r.scalar_one()


@router.post("/{program_id}/archive", response_model=ProgramSummary)
async def archive_program(
    program_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stop a program without deleting it - the logged workouts stay attached to it."""
    r = await db.execute(select(Program).where(Program.id == program_id, Program.user_id == user.id))
    program = r.scalar_one_or_none()
    if not program:
        raise HTTPException(404, "Програмата не е намерена.")
    program.status = "archived"
    await db.commit()
    await db.refresh(program)
    return program


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
        raise HTTPException(404, "Програмата не е намерена.")

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
