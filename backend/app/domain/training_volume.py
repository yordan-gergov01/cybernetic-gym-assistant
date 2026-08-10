"""What was actually lifted: sets per muscle group, and tonnage.

Aggregation over logged sets, kept pure so the route stays a thin shell. The weekly
targets these are compared against are not computed here - they come from
`calculators.calculate_optimal_volume` and are stored on the profile, so the target and
the count can never drift apart.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MuscleVolume:
    muscle_group: str
    sets_done: int
    sets_target: int | None


def _is_working_set(logged: dict) -> bool:
    """Warm-ups do not count towards volume, and neither does an unrecorded set."""
    return not logged.get("is_warmup") and logged.get("reps") is not None


def tonnage_kg(logged_sets: list[dict]) -> float:
    """Total load moved: weight x reps over the working sets.

    Sets logged without a weight (bodyweight work) contribute nothing here rather than
    being guessed at from the user's bodyweight - an invented number would quietly
    inflate the total.
    """
    total = sum(
        (s.get("weight_kg") or 0) * (s.get("reps") or 0)
        for s in logged_sets
        if _is_working_set(s)
    )
    return round(total, 1)


def working_set_count(logged_sets: list[dict]) -> int:
    return sum(1 for s in logged_sets if _is_working_set(s))


def sets_per_muscle(logged_sets: list[dict]) -> dict[str, int]:
    """Working sets grouped by muscle. Sets with no muscle recorded are left out."""
    counts: dict[str, int] = {}
    for logged in logged_sets:
        if not _is_working_set(logged):
            continue
        muscle = (logged.get("muscle_group") or "").strip().lower()
        if not muscle:
            continue
        counts[muscle] = counts.get(muscle, 0) + 1
    return counts


def weekly_volume(logged_sets: list[dict], targets: dict[str, float] | None) -> list[MuscleVolume]:
    """Sets done this week against the target, for every muscle on either side.

    A muscle that was trained but has no target still appears (with target None) instead
    of being dropped - work that is happening outside the plan is exactly what the user
    needs to see.
    """
    done = sets_per_muscle(logged_sets)
    target_map = {k.strip().lower(): v for k, v in (targets or {}).items()}
    muscles = sorted(set(done) | set(target_map))
    return [
        MuscleVolume(
            muscle_group=muscle,
            sets_done=done.get(muscle, 0),
            sets_target=int(target_map[muscle]) if muscle in target_map else None,
        )
        for muscle in muscles
    ]
