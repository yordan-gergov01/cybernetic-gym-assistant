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


def program_week_template_v3(
    *,
    level_label: str,
    goal: str | None,
    training_days_per_week: int | None,
    split_description: str,
    split_rationale: str,
    min_frequency: int,
    available_equipment: str | None,
    equipment_details: dict | None,
    session_duration_min: int | None,
    priority_muscles,
    avoid_growth_muscles,
    injuries: str | None,
    exercise_preferences: str | None,
    other_activities: str | None,
    volume: dict,
    lifts: dict,
    context: str,
    retry_feedback: str = "",
) -> str:
    """v3 hands the model a split decided in code, instead of letting it choose one.

    v2 was free to pick the structure and produced Push/Pull/Legs on 3 days, which
    trains every muscle once a week - a direct violation of the course's ≥2x rule.
    The split now comes from domain/program_design.py and the frequency requirement is
    stated as a hard constraint; the model's job is exercise selection within it.
    """
    equipment_list = ", ".join(k for k, v in (equipment_details or {}).items() if v) or "не е уточнено"
    feedback_block = (
        f"\n\nПРЕДИШНИЯТ ТИ ОТГОВОР БЕШЕ ОТХВЪРЛЕН:\n{retry_feedback}\nПоправи това." if retry_feedback else ""
    )
    return f"""Ти си сертифициран личен треньор по методологията на Menno Henselmans. Състави ЕДНА тренировъчна седмица, която ще се повтаря през целия мезоцикъл.

ЗАДЪЛЖИТЕЛНА СТРУКТУРА (определена е предварително, НЕ я променяй):
- Сплит: {split_description}
- Защо: {split_rationale}
- Точно {training_days_per_week} тренировъчни дни.
- ВСЯКА основна мускулна група трябва да се тренира минимум {min_frequency} пъти седмично.
  Това е най-важното изискване - програма, която не го спазва, е невалидна.

КЛИЕНТСКИ ПРОФИЛ:
- Ниво: {level_label}
- Цел: {goal}
- Продължителност на сесия: {session_duration_min} мин
- Оборудване: {available_equipment}
- Налични уреди: {equipment_list}
- Приоритетни мускули (повече обем): {priority_muscles}
- Мускули, които клиентът НЕ иска да уголемява: {avoid_growth_muscles or 'няма'}
- Травми/ограничения: {injuries or 'няма'}
- Предпочитания за упражнения: {exercise_preferences or 'няма'}
- Друга активност извън залата: {other_activities or 'няма'}

ОПТИМАЛЕН СЕДМИЧЕН ОБЕМ (серии на мускулна група, от калкулатора):
{json.dumps(volume, ensure_ascii=False)}

ОЦЕНЕНИ 1ПМ:
{json.dumps(lifts, ensure_ascii=False)}

КОНТЕКСТ ОТ КУРСА:
{context}

ОСТАНАЛИ ИЗИСКВАНИЯ:
- Разпредели зададения седмичен обем през сесиите; не го надвишавай значително.
- Избирай упражнения САМО спрямо наличното оборудване; избягвай конфликт с травмите.
- Съобрази броя серии с продължителността на сесията ({session_duration_min} мин).
- Всички текстови полета (`name`, `description`, `notes`, `day_name`) на БЪЛГАРСКИ.
- `exercise_name` ВИНАГИ на АНГЛИЙСКИ със стандартно име в залата.
- Използвай точно тези стойности за `muscle_group`: chest, back, shoulders, biceps, triceps, quads, hamstrings, glutes, calves, abs, rear_delts.{feedback_block}

Върни САМО валиден JSON:
{{
  "name": "Име на програмата на български",
  "description": "Кратко описание на подхода на български",
  "template_type": "upper_lower|ppl|full_body|custom",
  "days": [
    {{
      "day_number": 1,
      "day_name": "Име на деня на български",
      "exercises": [
        {{
          "exercise_name": "Barbell Bench Press",
          "muscle_group": "chest",
          "equipment": "barbell",
          "sets_prescribed": 4,
          "reps_min": 6,
          "reps_max": 8,
          "rir_target": 2,
          "rest_seconds": 180,
          "notes": "Кратка бележка на български"
        }}
      ]
    }}
  ]
}}"""


def program_week_template_v2(
    *,
    level_label: str,
    goal: str | None,
    training_days_per_week: int | None,
    available_equipment: str | None,
    equipment_details: dict | None,
    session_duration_min: int | None,
    priority_muscles,
    avoid_growth_muscles,
    injuries: str | None,
    exercise_preferences: str | None,
    other_activities: str | None,
    volume: dict,
    lifts: dict,
    context: str,
) -> str:
    """Ask for ONE training week, not the whole mesocycle.

    Exercise selection is the judgment call worth an LLM; repeating that week and
    progressing the load is arithmetic the deterministic engine already does
    for free. Asking for all weeks at once also produced JSON large enough to be
    truncated mid-response.
    """
    equipment_list = (
        ", ".join(k for k, v in (equipment_details or {}).items() if v) or "не е уточнено"
    )
    return f"""Ти си сертифициран личен треньор по методологията на Menno Henselmans. Състави ЕДНА тренировъчна седмица, която ще се повтаря през целия мезоцикъл.

КЛИЕНТСКИ ПРОФИЛ:
- Ниво: {level_label}
- Цел: {goal}
- Тренировъчни дни седмично: {training_days_per_week}
- Продължителност на сесия: {session_duration_min} мин
- Оборудване: {available_equipment}
- Налични уреди: {equipment_list}
- Приоритетни мускули (повече обем): {priority_muscles}
- Мускули, които клиентът НЕ иска да уголемява: {avoid_growth_muscles or 'няма'}
- Травми/ограничения: {injuries or 'няма'}
- Предпочитания за упражнения: {exercise_preferences or 'няма'}
- Друга активност извън залата: {other_activities or 'няма'}

ОПТИМАЛЕН СЕДМИЧЕН ОБЕМ (серии на мускулна група, от калкулатора):
{json.dumps(volume, ensure_ascii=False)}

ОЦЕНЕНИ 1ПМ:
{json.dumps(lifts, ensure_ascii=False)}

КОНТЕКСТ ОТ КУРСА (принципи на Henselmans):
{context}

ИЗИСКВАНИЯ:
- Точно {training_days_per_week} тренировъчни дни. Разпредели ги така, че всяка мускулна група да се тренира с подходяща честота.
- Спазвай зададения седмичен обем по мускулни групи — това са изчислени стойности, не ги надвишавай значително.
- Избирай упражнения САМО спрямо наличното оборудване и избягвай тези, които влизат в конфликт с травмите.
- Съобрази обема с продължителността на сесията ({session_duration_min} мин).
- Всички текстови полета (`name`, `description`, `notes`, `day_name`) на БЪЛГАРСКИ.
- `exercise_name` ВИНАГИ на АНГЛИЙСКИ със стандартно име в залата (напр. "Barbell Bench Press", "Romanian Deadlift").
- `muscle_group` и `equipment` на латиница с кратки термини (chest, back, barbell, dumbbell).
- Използвай точно тези стойности за muscle_group: chest, back, shoulders, biceps, triceps, quads, hamstrings, glutes, calves, abs, rear_delts.

Върни САМО валиден JSON:
{{
  "name": "Име на програмата на български",
  "description": "Кратко описание на подхода на български",
  "template_type": "upper_lower|ppl|full_body|custom",
  "days": [
    {{
      "day_number": 1,
      "day_name": "Име на деня на български",
      "exercises": [
        {{
          "exercise_name": "Barbell Bench Press",
          "muscle_group": "chest",
          "equipment": "barbell",
          "sets_prescribed": 4,
          "reps_min": 6,
          "reps_max": 8,
          "rir_target": 2,
          "rest_seconds": 180,
          "notes": "Кратка бележка на български"
        }}
      ]
    }}
  ]
}}"""


# BODY-FAT VISUAL ASSESSMENT

def bf_assessment_v1(*, sex: str, angles: list[str], rubric: str, context: str = "") -> str:
    """Estimate body-fat % from photos, anchored to the course's DXA-verified rubric.

    The model must ground its estimate in observed visual markers and report a range
    plus a confidence, so an uncertain read stays visible instead of being dressed up
    as precision.
    """
    rubric_block = (
        f"КАЛИБРАЦИОННА СКАЛА от курса (DXA-верифицирани примери и техните визуални маркери):\n{rubric}"
        if rubric
        else "ВНИМАНИЕ: калибрационната скала от курса не е налична - отбележи това като по-ниска увереност."
    )
    extra = f"\n\nДопълнителен контекст от курса:\n{context}" if context else ""
    return f"""Ти си експерт по оценка на телесна композиция по методологията на Menno Henselmans.

ЗАДАЧА: Оцени процента телесни мазнини (BF%) на човека от приложените снимки.
Пол: {sex}. Ъгли на снимките: {', '.join(angles) or 'неуточнени'}.

{rubric_block}{extra}

КАК ДА ОЦЕНИШ:
1. Опиши какво ВИЖДАШ обективно - коремна дефиниция, васкуларност, разделение на мускулите,
   мазнини около кръста/ханша, набразденост (striations), общ вид на кожата.
2. Сравни наблюдаваните маркери с калибрационната скала и намери най-близкото ниво.
3. Дай точкова оценка И диапазон. При лошо осветление, скриващо облекло или неудобен ъгъл
   НАМАЛИ увереността и го посочи изрично.

ВАЖНО:
- Не се води по това колко мускулест изглежда човекът - оценяваш САМО мазнините.
- Осветлението силно влияе на видимата дефиниция; при слабо осветление оценявай консервативно.
- Ако снимките не позволяват надеждна оценка, кажи го честно с confidence "low".

Върни САМО валиден JSON:
{{
  "bf_pct": число (точкова оценка),
  "bf_range_low": число,
  "bf_range_high": число,
  "confidence": "high" | "medium" | "low",
  "observed_markers": ["маркер 1 на български", "маркер 2"],
  "closest_reference": "най-близкото ниво от скалата, напр. 15.6% (male)",
  "limitations": "какво пречи на точността (на български), или празен низ",
  "reasoning_bg": "2-3 изречения обосновка на БЪЛГАРСКИ"
}}"""


# RAG QUERY REWRITE

def rag_query_rewrite_v1(question: str) -> str:
    return (
        f"User question: {question}\n"
        "Rewrite as a SHORT English search query (5-10 words) for a fitness science "
        "knowledge base (Henselmans PTC course).\n"
        "Reply ONLY with the search query, nothing else."
    )


def rag_query_rewrite_v2(question: str, history: str = "") -> str:
    """v2 resolves the question against the conversation before translating it.

    v1 saw the last message alone, so a follow-up like "а за жени?" was rewritten to
    "women" and retrieved noise. The preceding turns carry the subject; the model's job
    is to fold them back in and return a query that stands on its own.
    """
    if not history:
        return rag_query_rewrite_v1(question)
    return f"""Conversation so far:
{history}

Latest user message: {question}

The latest message may be a follow-up that only makes sense together with the conversation
above (pronouns, ellipsis, "and for X?"). Resolve it into a SELF-CONTAINED English search
query (5-12 words) for a fitness science knowledge base (Henselmans PTC course).
If the latest message already stands on its own, translate it and ignore the conversation.
Reply ONLY with the search query, nothing else."""


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
