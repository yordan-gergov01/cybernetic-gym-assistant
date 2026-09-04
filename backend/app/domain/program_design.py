"""Deterministic training-split rules (Henselmans methodology).

The course is explicit that every muscle group should be trained **at least twice per
week** ("...trained at least 2x per week. 3. Create the program split." - Training case
studies PTC 2022). That makes the split structure a rule, not a judgment call, so it is
decided here in code and handed to the model as a constraint.

This exists because an unconstrained model produced Push/Pull/Legs over 3 days, which
trains every muscle only once a week and violates the methodology outright.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.domain.muscles import muscle_bg

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


@dataclass(frozen=True)
class MuscleAdjustment:
    """The answer to a muscle group where several exercises have stalled.

    The course's order is fixed: raise the frequency of the group first, and only when
    the schedule cannot carry another session raise the number of sets
    (`domain/plateau.py`, action `adjust_muscle`).
    """

    action: str                  # move_exercise | add_sets | none
    exercise_name: str | None    # the exercise that moves, or that gains a set
    from_day: int | None         # day_number it leaves (move_exercise)
    to_day: int | None           # day_number it joins (move_exercise)
    reason_bg: str


def _muscle_exercises(day: dict, muscle: str) -> list[dict]:
    return [
        ex
        for ex in day.get("exercises", [])
        if (ex.get("muscle_group") or "").strip().lower() == muscle
    ]


def plan_muscle_adjustment(
    days: list[dict],
    muscle: str,
    target_weekly_sets: int | None = None,
) -> MuscleAdjustment:
    """Decide how to train a stalling muscle group more often, or harder.

    Frequency is raised by *moving* an exercise to a day that does not train the group,
    not by adding one: that keeps the weekly set count exactly where it was, so the
    change under test is the frequency alone. It needs a source day with at least two
    exercises for the muscle - moving the only one would just relocate the session.

    Adding sets is the fallback, and it stops at the profile's optimal weekly volume.
    Past that point the plateau is not a volume problem, and more sets only add fatigue.
    """
    muscle = (muscle or "").strip().lower()
    training_days = sorted(
        (d for d in days if not d.get("is_rest_day")),
        key=lambda d: d.get("day_number", 0),
    )

    with_muscle = [d for d in training_days if _muscle_exercises(d, muscle)]
    if not with_muscle:
        return MuscleAdjustment(
            action="none",
            exercise_name=None,
            from_day=None,
            to_day=None,
            reason_bg=f"Програмата не съдържа упражнения за {muscle_bg(muscle)}.",
        )

    free_days = [d for d in training_days if not _muscle_exercises(d, muscle)]
    # The day carrying the most work for the muscle can spare an exercise; ties go to
    # the earliest day so the same program always produces the same change.
    sources = sorted(
        (d for d in with_muscle if len(_muscle_exercises(d, muscle)) >= 2),
        key=lambda d: (-len(_muscle_exercises(d, muscle)), d.get("day_number", 0)),
    )

    if free_days and sources:
        source = sources[0]
        moving = sorted(
            _muscle_exercises(source, muscle), key=lambda ex: ex.get("order_index", 0)
        )[-1]
        return MuscleAdjustment(
            action="move_exercise",
            exercise_name=moving.get("exercise_name"),
            from_day=source.get("day_number"),
            to_day=free_days[0].get("day_number"),
            reason_bg=(
                f"Честотата на {muscle_bg(muscle)} се вдига от {len(with_muscle)}× на "
                f"{len(with_muscle) + 1}× седмично - {moving.get('exercise_name')} се мести "
                f"в ден {free_days[0].get('day_number')}, без да се променя седмичният обем."
            ),
        )

    planned = sum(
        (ex.get("sets_prescribed") or 0) for day in with_muscle for ex in _muscle_exercises(day, muscle)
    )
    if target_weekly_sets is not None and planned + 1 > target_weekly_sets:
        return MuscleAdjustment(
            action="none",
            exercise_name=None,
            from_day=None,
            to_day=None,
            reason_bg=(
                f"Обемът за {muscle_bg(muscle)} вече е {planned} серии седмично при оптимум "
                f"{target_weekly_sets}. Застоят не е от липса на обем - провери "
                "възстановяването и храненето, преди да се добавя още."
            ),
        )

    primary = sorted(
        _muscle_exercises(with_muscle[0], muscle), key=lambda ex: ex.get("order_index", 0)
    )[0]
    return MuscleAdjustment(
        action="add_sets",
        exercise_name=primary.get("exercise_name"),
        from_day=None,
        to_day=None,
        reason_bg=(
            f"Графикът не позволява по-висока честота за {muscle_bg(muscle)}, затова "
            f"{primary.get('exercise_name')} получава още една серия "
            f"({planned} → {planned + 1} седмично)."
        ),
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
