"""Bulgarian error responses for the whole API.

Every error the user can see must say what went wrong and what to do about it, in
Bulgarian, without a technical term (CLAUDE.md rule #12 - nothing fails quietly, and a
message nobody understands is a quiet failure).

Validation errors get this treatment here rather than in the frontend because only the
backend knows the schema: which field failed, what its bounds are, and which values it
accepts. The frontend cannot reconstruct that from a status code. What the frontend does
own is the case where there is no response at all - no connection, a timeout - which the
backend by definition cannot answer.

The response shape stays `{"detail": "<sentence>"}` so existing callers keep working; a
`fields` list is added alongside it so a form can highlight the inputs that failed.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# What the user calls each field. Kept as singular noun phrases so they agree with the
# reasons below ("<label> липсва"). Anything missing falls back to the field name, which
# is ugly but honest - better than a generic "invalid input" that says nothing.
_FIELD_LABELS = {
    "age": "Възрастта",
    "sex": "Полът",
    "height_cm": "Височината",
    "bodyweight_kg": "Теглото",
    "body_fat_pct": "Процентът телесни мазнини",
    "goal": "Целта",
    "activity_level": "Нивото на активност",
    "training_status": "Тренировъчният опит",
    "training_years": "Тренировъчният стаж",
    "training_days_per_week": "Броят тренировъчни дни",
    "session_duration_min": "Продължителността на тренировката",
    "available_equipment": "Наличното оборудване",
    "min_barbell_increment_kg": "Най-малката стъпка с щанга",
    "min_dumbbell_increment_kg": "Стъпката между дъмбелите",
    "stress_level": "Нивото на стрес",
    "sleep_quality": "Качеството на съня",
    "sleep_hours": "Броят часове сън",
    "dedication_level": "Темпото",
    "caffeine_mg_per_day": "Кофеинът на ден",
    "occupation": "Професията",
    "priority_muscles": "Изборът на приоритетни мускули",
    "dietary_restrictions": "Хранителният режим",
    "email": "Имейлът",
    "password": "Паролата",
    "name": "Името",
    "weight_kg": "Теглото",
    "reps": "Броят повторения",
    "rir_actual": "RIR",
    "set_number": "Номерът на серията",
    "date": "Датата",
    "taken_at": "Датата на снимката",
    "photo_ids": "Изборът на снимки",
    "total_weeks": "Броят седмици",
    "start_date": "Началната дата",
    "week_number": "Номерът на седмицата",
    "quantity_g": "Количеството",
    "calories": "Броят калории",
    "food_name": "Името на храната",
}


def _label(loc: tuple[Any, ...]) -> str:
    """Human name of the field that failed, ignoring the body/query wrapper."""
    parts = [p for p in loc if p not in ("body", "query", "path", "header")]
    if not parts:
        return "Данните"
    field = str(parts[-1])
    # A list item reads better named by its list: photo_ids.0 -> "Снимките".
    if field.isdigit() and len(parts) >= 2:
        field = str(parts[-2])
    return _FIELD_LABELS.get(field, field)


def _options(expected: Any) -> str:
    """Pydantic renders the accepted values as "'a' or 'b'" - English, and quoted."""
    return str(expected or "").replace("'", "").replace(" or ", " или ")


def _chars(count: Any) -> str:
    """"1 символ" but "8 символа" - the singular form is not optional in Bulgarian."""
    return f"{count} символ" if count == 1 else f"{count} символа"


def _reason(error: dict) -> str:
    """Why the value was rejected, in plain Bulgarian."""
    kind = error.get("type", "")
    ctx = error.get("ctx") or {}

    if kind == "missing":
        return "липсва"
    if kind in ("int_parsing", "int_type"):
        return "трябва да е цяло число"
    if kind in ("float_parsing", "float_type", "decimal_parsing"):
        return "трябва да е число"
    if kind in ("bool_parsing", "bool_type"):
        return "трябва да е да или не"
    if kind in ("date_parsing", "date_from_datetime_parsing", "date_type"):
        return "трябва да е валидна дата"
    if kind == "greater_than":
        return f"трябва да е повече от {ctx.get('gt')}"
    if kind == "greater_than_equal":
        return f"не може да е под {ctx.get('ge')}"
    if kind == "less_than":
        return f"трябва да е под {ctx.get('lt')}"
    if kind == "less_than_equal":
        return f"не може да е над {ctx.get('le')}"
    if kind in ("string_too_short", "too_short"):
        return f"трябва да е поне {_chars(ctx.get('min_length'))}"
    if kind in ("string_too_long", "too_long"):
        return f"трябва да е най-много {_chars(ctx.get('max_length'))}"
    if kind in ("literal_error", "enum"):
        return f"приема само: {_options(ctx.get('expected'))}"
    if kind in ("string_type", "string_pattern_mismatch"):
        return "е в невалиден формат"
    if kind == "value_error":
        # EmailStr and custom validators land here, but their message is English prose
        # ("An email address must have an @-sign") and must not reach the user.
        return "е в невалиден формат"
    if kind == "json_invalid":
        return "не е изпратено коректно"
    return "е в невалиден формат"


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Turn Pydantic's English field errors into one Bulgarian sentence.

    Without this the raw error list reaches the UI and the user reads
    "Input should be a valid integer" - or worse, the serialized JSON of it.
    """
    problems: list[str] = []
    fields: list[str] = []
    for error in exc.errors():
        loc = tuple(error.get("loc") or ())
        problems.append(f"{_label(loc)} {_reason(error)}")
        named = [str(p) for p in loc if p not in ("body", "query", "path", "header")]
        if named:
            fields.append(".".join(named))

    detail = "; ".join(problems) + "." if problems else "Изпратените данни са невалидни."
    logger.info("Validation failed for %s %s: %s", request.method, request.url.path, exc.errors())
    return JSONResponse(
        status_code=422,
        content={"detail": detail, "fields": fields},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Last resort: never show the user a stack trace or an empty screen.

    The real error goes to the log with full context; the user gets a sentence saying
    the problem is on our side and that their data is not lost.
    """
    logger.error("Unhandled error on %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "detail": (
                "Възникна неочакван проблем от наша страна. Данните ти са запазени - "
                "опитай пак след малко."
            )
        },
    )
