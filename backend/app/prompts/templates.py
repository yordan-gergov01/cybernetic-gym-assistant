"""Versioned prompt templates.

Every LLM prompt in the app lives here as a versioned builder function, so prompts
can be reviewed, A/B tested, or rolled back without touching route/business code.
Add a new version as a new `<name>_vN` function and register it in registry.py;
never edit a shipped version in place (that would silently change behaviour).

Naming: `<domain>_<purpose>_vN`. Builders are pure functions that return a string.
"""
from __future__ import annotations

import json


def _is_bulgarian(response_language: str) -> bool:
    return "bulgar" in response_language.lower()


# CHAT

def chat_language_rules_v1(response_language: str) -> str:
    if _is_bulgarian(response_language):
        return (
            "ПРАВИЛА: Отговаряй САМО на БЪЛГАРСКИ. Използвай килограми. "
            "Имената на упражненията винаги на АНГЛИЙСКИ (стандартни имена в залата, напр. Barbell Row). "
            "Бъди директен и практичен."
        )
    return (
        f"RULES: Reply in the user's configured language ({response_language}). "
        "Use kilograms. Use standard English names for exercises. Be direct and practical."
    )


def chat_profile_block_v1(level_label: str, goal: str | None, energy: dict) -> str:
    return f"""
Профил на потребителя: ниво {level_label} | цел: {goal}
Калории (цел): {energy.get('target_kcal', '?')} ккал | протеин: {energy.get('protein_g', '?')} г | мазнини: {energy.get('fat_g', '?')} г | въглехидрати: {energy.get('carbs_g', '?')} г
"""


def chat_system_v1(response_language: str, profile_block: str, context: str) -> str:
    bg = _is_bulgarian(response_language)
    intro = (
        "Ти си персонален AI фитнес треньор по методологията на Menno Henselmans."
        if bg
        else "You are a personal AI fitness coach trained on Menno Henselmans methodology."
    )
    context_label = "Контекст от курса на Henselmans:" if bg else "Course context (Henselmans):"
    return f"""{intro}
{chat_language_rules_v1(response_language)}
{profile_block}
{context_label}
{context}"""


def chat_system_v2(response_language: str, profile_block: str, context: str) -> str:
    """Grounded variant: forces answers to lean on retrieved context, cite sources,
    and admit when the course material does not cover the question."""
    bg = _is_bulgarian(response_language)
    has_context = bool(context.strip())
    if bg:
        intro = "Ти си персонален AI фитнес треньор по методологията на Menno Henselmans."
        grounding = (
            "ОСНОВАВАНЕ: Отговаряй приоритетно спрямо КОНТЕКСТА от курса по-долу. "
            "Когато твърдиш нещо от материалите, цитирай източника в скоби (напр. [Protein PTC 2022.pdf]). "
            "Ако контекстът НЕ покрива въпроса, кажи ясно, че нямаш конкретна информация от материалите, "
            "и обозначи общите съвети като такива. Не измисляй цитати, числа или проучвания."
        )
        context_label = (
            "Контекст от курса на Henselmans:" if has_context
            else "Няма намерен релевантен контекст от курса за този въпрос."
        )
    else:
        intro = "You are a personal AI fitness coach trained on Menno Henselmans methodology."
        grounding = (
            "GROUNDING: Base your answer primarily on the COURSE CONTEXT below. "
            "When you state something from the materials, cite the source in brackets (e.g. [Protein PTC 2022.pdf]). "
            "If the context does NOT cover the question, say clearly that you have no specific information from the "
            "materials, and label any general advice as such. Never invent citations, numbers, or studies."
        )
        context_label = (
            "Course context (Henselmans):" if has_context
            else "No relevant course context was found for this question."
        )
    return f"""{intro}
{chat_language_rules_v1(response_language)}
{grounding}
{profile_block}
{context_label}
{context}"""


# RAG QUERY REWRITE

def rag_query_rewrite_v1(question: str) -> str:
    return (
        f"User question: {question}\n"
        "Rewrite as a SHORT English search query (5-10 words) for a fitness science "
        "knowledge base (Henselmans PTC course).\n"
        "Reply ONLY with the search query, nothing else."
    )


# PROGRAM GENERATION

def program_generation_v1(
    *,
    total_weeks: int,
    level_label: str,
    goal: str | None,
    training_days_per_week: int | None,
    available_equipment: str | None,
    session_duration_min: int | None,
    priority_muscles,
    injuries: str | None,
    exercise_preferences: str | None,
    target_kcal,
    protein_g,
    volume: dict,
    lifts: dict,
    context: str,
) -> str:
    return f"""Ти си сертифициран личен треньор по методологията на Menno Henselmans. Генерирай пълна {total_weeks}-седмична тренировъчна програма.

КЛИЕНТСКИ ПРОФИЛ:
- Ниво: {level_label}
- Цел: {goal}
- Тренировъчни дни седмично: {training_days_per_week}
- Оборудване: {available_equipment}
- Продължителност на сесия: {session_duration_min} мин
- Приоритетни мускули: {priority_muscles}
- Травми/ограничения: {injuries or 'няма'}
- Предпочитания за упражнения: {exercise_preferences or 'няма'}

РЕЗУЛТАТИ ОТ КАЛКУЛАТОРИТЕ:
- Целеви калории: {target_kcal} ккал
- Протеин: {protein_g} г
- Оптимален обем (JSON): {json.dumps(volume, ensure_ascii=False)}
- Оценени 1ПМ (JSON): {json.dumps(lifts, ensure_ascii=False)}

КОНТЕКСТ ОТ КУРСА (принципи на Henselmans):
{context}

ИЗИСКВАНИЯ:
- Прогресивно натоварване (MEV първи седмици, към MAV към седмица {total_weeks - 1}).
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


# FATIGUE / DELOAD EXPLANATION

def fatigue_explanation_v1(*, decision_label: str, factors: list[str], answers: dict, context: str) -> str:
    return f"""Ти си треньор по методологията на Menno Henselmans. Обясни на клиента на БЪЛГАРСКИ (2-3 изречения) защо решението е: {decision_label}.

Решението вече е взето детерминистично - НЕ го променяй, само го обясни ясно и практично.
Наблюдавани фактори за умора: {', '.join(factors) or 'няма значими'}.
Отговори от чек-ина: {json.dumps(answers, ensure_ascii=False)}

Принципи от курса (използвай ги за обосновката):
{context}"""


# FOOD

def food_extraction_v1(text: str) -> str:
    return f"""Извлечи всички храни и количества от текста по-долу. Текстът може да е на български.

Текст: {text}

За всяка храна върни JSON полета (имената на полетата задължително на английски, както е указано):
- food_name_en: име на английски за търсене в USDA (напр. "chicken breast raw", "oats dry", "whole egg")
- food_name_bg: име за показване на български
- quantity_g: грамове (оцени типична порция, ако не е уточнено)
- cooking_method: начин на приготвяне (напр. raw, boiled, grilled) - на латиница е достатъчно

Чести превръщания: 1 яйце ≈ 60г; 1 банан ≈ 120г; 1 филия хляб ≈ 30г; 1 с.л. масло ≈ 15г; 1 ч.л. ≈ 5г; 1 чаша течност ≈ 240мл.

Върни САМО валиден JSON обект с ключ "items" — масив от обекти с горните полета.
Примерна структура: {{"items": [{{"food_name_en": "...", "food_name_bg": "...", "quantity_g": 0, "cooking_method": ""}}]}}"""


def food_llm_estimate_v1(*, food_name_en: str, cooking_method: str, quantity_g: float, food_name_bg: str) -> str:
    return (
        f"Оцени хранителната стойност за: {food_name_en} ({cooking_method}), {quantity_g} г. "
        f"Българско име за референция: {food_name_bg}. "
        f"Върни САМО валиден JSON с числови полета: calories, protein_g, fat_g, carbs_g (ключовете точно така, на английски)."
    )


# --- WORKOUT PROGRESSION ------------------------------------------------------
# Next-session load progression is deterministic and lives in services/progression.py