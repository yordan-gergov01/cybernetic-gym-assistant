import json
from datetime import date, timedelta

import faiss
import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from openai import AsyncOpenAI, OpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.config import settings
from db.database import get_db
from deps import get_current_user
from models import Program, ProgramDay, ProgramExercise, ProgramWeek, User, UserProfile
from schemas import ProgramCreate, ProgramExerciseOut, ProgramGenerateRequest, ProgramOut

router = APIRouter(prefix="/programs", tags=["programs"])

openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def load_rag_context(query: str) -> str:
    try:
        index = faiss.read_index(str(settings.faiss_index_path))
        meta = json.loads(settings.faiss_metadata_path.read_text(encoding="utf-8"))
        sync_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        emb = np.array(
            sync_client.embeddings.create(model=settings.EMBEDDING_MODEL, input=[query]).data[0].embedding,
            dtype="float32",
        ).reshape(1, -1)
        faiss.normalize_L2(emb)
        k = min(settings.RETRIEVAL_TOP_K, max(1, len(meta)))
        _, ids = index.search(emb, k)
        chunks = [meta[i]["text"] for i in ids[0] if i != -1 and i < len(meta)]
        return "\n\n".join(chunks)
    except Exception:
        return ""


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

    context = await load_rag_context(
        f"{level_map_bg.get(profile.training_status, 'трениращ')} клиент програма хипертрофия "
        f"{profile.training_days_per_week} дни седмично цел {profile.goal or ''}"
    )

    prompt = f"""Ти си сертифициран личен треньор по методологията на Menno Henselmans. Генерирай пълна {data.total_weeks}-седмична тренировъчна програма.

КЛИЕНТСКИ ПРОФИЛ:
- Ниво: {level_map_bg.get(profile.training_status, 'Средно напреднал')}
- Цел: {profile.goal_validated or profile.goal}
- Тренировъчни дни седмично: {profile.training_days_per_week}
- Оборудване: {profile.available_equipment}
- Продължителност на сесия: {profile.session_duration_min} мин
- Приоритетни мускули: {profile.priority_muscles}
- Травми/ограничения: {profile.injuries or 'няма'}
- Предпочитания за упражнения: {profile.exercise_preferences or 'няма'}

РЕЗУЛТАТИ ОТ КАЛКУЛАТОРИТЕ:
- Целеви калории: {energy.get('target_kcal', 'няма')} ккал
- Протеин: {energy.get('protein_g', 'няма')} г
- Оптимален обем (JSON): {json.dumps(volume, ensure_ascii=False)}
- Оценени 1ПМ (JSON): {json.dumps(lifts, ensure_ascii=False)}

КОНТЕКСТ ОТ КУРСА (принципи на Henselmans):
{context}

ИЗИСКВАНИЯ:
- Прогресивно натоварване (MEV първи седмици, към MAV към седмица {data.total_weeks - 1}).
- Без отделна deload седмица в този JSON - deload само при нужда от оценка на умора.
- Всички обяснения в текстовите полета на JSON (`name`, `description`, `notes`, `day_name` и т.н.) на БЪЛГАРСКИ.
- Полето `exercise_name` за всяко упражнение ВИНАГИ на АНГЛИЙСКИ със стандартно име в залата (напр. "Barbell Bench Press", "Romanian Deadlift").
- `muscle_group` и `equipment` на латиница с кратки термини (chest, back, barbell, dumbbell) за съвместимост с базата.

Върни САМО валиден JSON със следната структура (пример за форма; попълни реални данни):
{{
  "name": "Име на програмата на български",
  "description": "Кратко описание на български",
  "template_type": "upper_lower|ppl|full_body|custom",
  "weeks": [
    {{
      "week_number": 1,
      "week_type": "loading",
      "notes": "Бележки на български",
      "days": [
        {{
          "day_number": 1,
          "day_name": "Име на деня на български или латиница",
          "is_rest_day": false,
          "exercises": [
            {{
              "exercise_name": "Barbell Bench Press",
              "muscle_group": "chest",
              "equipment": "barbell",
              "sets_prescribed": 3,
              "reps_min": 8,
              "reps_max": 12,
              "rir_target": 2,
              "rest_seconds": 180,
              "notes": "Бележка на български"
            }}
          ]
        }}
      ]
    }}
  ]
}}"""

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
