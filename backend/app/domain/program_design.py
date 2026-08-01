"""Deterministic training-split rules (Henselmans methodology).

The course is explicit that every muscle group should be trained **at least twice per
week** ("...trained at least 2x per week. 3. Create the program split." - Training case
studies PTC 2022). That makes the split structure a rule, not a judgment call, so it is
decided here in code and handed to the model as a constraint (CLAUDE.md rule #5).

This exists because an unconstrained model produced Push/Pull/Legs over 3 days, which
trains every muscle only once a week and violates the methodology outright.
"""
from __future__ import annotations

from dataclasses import dataclass

MIN_WEEKLY_FREQUENCY = 2

# Groups the ≥2x rule is enforced on. Small accessory muscles are left out: the course
# calls the per-muscle frequency "a minimum, not a rigid target", and direct calf/ab
# work is commonly programmed less often without breaking the plan.
MAJOR_MUSCLES = frozenset(
    {"chest", "back", "shoulders", "quads", "hamstrings", "glutes", "biceps", "triceps"}
)


@dataclass(frozen=True)
class SplitRecommendation:
    name: str            # short label, e.g. "upper_lower"
    description_bg: str  # what the model should build, in Bulgarian
    rationale_bg: str    # why, so the UI and the coach can explain it


def recommend_split(training_days_per_week: int) -> SplitRecommendation:
    """Pick a split whose structure can satisfy the ≥2x/week frequency rule.

    Push/Pull/Legs only reaches that frequency at 6 days a week; on 3 days it trains
    everything once, which is why it is not offered below 6.
    """
    days = max(1, min(7, training_days_per_week or 3))

    if days <= 2:
        return SplitRecommendation(
            name="full_body",
            description_bg=f"Full body - всяка от {days} сесии покрива цялото тяло.",
            rationale_bg="При малко сесии само full body осигурява достатъчна честота на мускулна група.",
        )
    if days == 3:
        return SplitRecommendation(
            name="full_body",
            description_bg="Full body - и трите сесии покриват цялото тяло, с различен акцент и подбор на упражнения.",
            rationale_bg=(
                "При 3 дни Push/Pull/Legs тренира всеки мускул само веднъж седмично. "
                "Full body дава честота 3× и е по-добрият избор според курса."
            ),
        )
    if days == 4:
        return SplitRecommendation(
            name="upper_lower",
            description_bg="Upper/Lower - горна, долна, горна, долна.",
            rationale_bg="Всяка мускулна група се тренира 2× седмично.",
        )
    if days == 5:
        return SplitRecommendation(
            name="upper_lower_full",
            description_bg="Upper, Lower, Upper, Lower и една full body сесия.",
            rationale_bg="Пета сесия добавя обем, без да сваля честотата под 2× седмично.",
        )
    return SplitRecommendation(
        name="ppl",
        description_bg="Push/Pull/Legs, повторен два пъти в седмицата.",
        rationale_bg="При 6 дни PPL достига честота 2× седмично на мускулна група.",
    )


def weekly_frequency(days: list[dict]) -> dict[str, int]:
    """How many days per week each muscle group is trained.

    `days` are the generated day dicts, each with an `exercises` list carrying
    `muscle_group`. A muscle counts once per day regardless of exercise count.
    """
    counts: dict[str, int] = {}
    for day in days:
        seen = {
            (ex.get("muscle_group") or "").strip().lower()
            for ex in day.get("exercises", [])
            if ex.get("muscle_group")
        }
        for muscle in seen:
            counts[muscle] = counts.get(muscle, 0) + 1
    return counts


def frequency_violations(days: list[dict]) -> list[str]:
    """Major muscle groups trained fewer than MIN_WEEKLY_FREQUENCY times a week.

    A group that is absent entirely is not reported here - that is a coverage problem,
    not a frequency one, and a program may legitimately omit direct work for a muscle
    the user asked not to grow.
    """
    counts = weekly_frequency(days)
    return sorted(
        muscle
        for muscle, count in counts.items()
        if muscle in MAJOR_MUSCLES and count < MIN_WEEKLY_FREQUENCY
    )
