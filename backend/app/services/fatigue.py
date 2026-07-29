"""Deterministic fatigue / deload decision engine (Henselmans methodology).

The DECISION is made by transparent rules here - never by an LLM (see CLAUDE.md
rule #5: if code can answer, code answers). An LLM is used elsewhere only to
phrase the explanation for the user; the recommendation itself is deterministic
and reproducible.

Henselmans deloading rationale: accumulated fatigue masks fitness. The signals
that fatigue has outrun recovery are declining performance, poor sleep/recovery,
joint pain, dropping motivation, and reduced appetite. When enough of these stack
up, a deload (or a volume cut) restores the fitness-fatigue balance so progress
can resume.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Answer -> fatigue points. Higher total = more accumulated fatigue.
_RECOVERY_POINTS = {"poor": 2, "fair": 1, "good": 0}
_SLEEP_POINTS = {"poor": 2, "fair": 1, "good": 0}
_PERFORMANCE_POINTS = {"declining": 3, "stable": 0, "improving": -1}
_MOTIVATION_POINTS = {"low": 2, "moderate": 1, "high": 0}
_APPETITE_POINTS = {"decreased": 1, "normal": 0, "increased": 0}
_JOINT_PAIN_POINTS = 2

# Human-readable contributing factor per signal, in Bulgarian.
_FACTOR_LABELS = {
    "recovery_quality": {"poor": "лошо възстановяване", "fair": "средно възстановяване"},
    "sleep_quality": {"poor": "лош сън", "fair": "среден сън"},
    "performance_trend": {"declining": "спадаща сила/представяне"},
    "motivation": {"low": "ниска мотивация", "moderate": "умерена мотивация"},
    "appetite": {"decreased": "намален апетит"},
}

DELOAD_THRESHOLD = 6      # score >= this -> deload
CAUTION_THRESHOLD = 3     # score in [CAUTION, DELOAD) -> reduce volume / monitor


@dataclass
class FatigueDecision:
    decision: str                 # "continue" | "caution" | "deload"
    score: int
    factors: list[str] = field(default_factory=list)
    recommendation_bg: str = ""   # deterministic Bulgarian fallback explanation


def assess_fatigue(answers: dict) -> FatigueDecision:
    """Score the check-in answers and return a deterministic deload recommendation.

    `answers` keys match schemas.FatigueAnswers:
      recovery_quality, performance_trend, joint_pain, sleep_quality,
      motivation, appetite.
    """
    recovery = answers.get("recovery_quality", "good")
    performance = answers.get("performance_trend", "stable")
    joint_pain = bool(answers.get("joint_pain", False))
    sleep = answers.get("sleep_quality", "good")
    motivation = answers.get("motivation", "high")
    appetite = answers.get("appetite", "normal")

    score = (
        _RECOVERY_POINTS.get(recovery, 0)
        + _PERFORMANCE_POINTS.get(performance, 0)
        + (_JOINT_PAIN_POINTS if joint_pain else 0)
        + _SLEEP_POINTS.get(sleep, 0)
        + _MOTIVATION_POINTS.get(motivation, 0)
        + _APPETITE_POINTS.get(appetite, 0)
    )

    factors: list[str] = []
    for key, value in (
        ("recovery_quality", recovery),
        ("sleep_quality", sleep),
        ("performance_trend", performance),
        ("motivation", motivation),
        ("appetite", appetite),
    ):
        label = _FACTOR_LABELS.get(key, {}).get(value)
        if label:
            factors.append(label)
    if joint_pain:
        factors.append("болка в стави")

    # Hard override: declining performance combined with poor recovery or poor
    # sleep is the classic "fatigue is masking fitness" pattern - deload even if
    # the raw score is a point short.
    hard_deload = performance == "declining" and (recovery == "poor" or sleep == "poor")

    if score >= DELOAD_THRESHOLD or hard_deload:
        decision = "deload"
        rec = (
            "Препоръка: deload седмица (~50% обем, запази интензитета/техниката). "
            "Натрупаната умора надвишава възстановяването и маскира формата ти."
        )
    elif score >= CAUTION_THRESHOLD:
        decision = "caution"
        rec = (
            "Препоръка: намали обема с ~20% тази седмица и следи внимателно. "
            "Има ранни признаци на умора, но още не е нужен пълен deload."
        )
    else:
        decision = "continue"
        rec = (
            "Препоръка: продължи с прогресията по план. "
            "Възстановяването ти покрива натоварването."
        )

    if factors:
        rec += " Фактори: " + ", ".join(factors) + "."

    return FatigueDecision(decision=decision, score=score, factors=factors, recommendation_bg=rec)
