"""Deterministic load progression (Henselmans double-progression).

The next-session target is pure arithmetic, so it is computed here, not guessed by
an LLM (CLAUDE.md rule #5). Rules, from the Henselmans progression guidelines:

- Actual RIR ABOVE target (set was too easy)  -> add weight (compound +2.5 kg, isolation +1.25 kg), reset reps to the bottom of the range.
- Actual RIR EQUAL to target                  -> keep weight, add one rep (up to the top of the range).
- Actual RIR BELOW target (set was too hard)  -> hold weight, focus on technique.

Weight steps are smaller for isolation lifts. When RIR was not logged we cannot judge
effort, so we hold the weight and ask the user to log RIR next time (fail loud, rule #12).
"""
from __future__ import annotations

from dataclasses import dataclass

# Muscle groups trained mostly by isolation work get the smaller weight increment.
_ISOLATION_MUSCLES = {"biceps", "triceps", "calves", "rear_delts", "abs", "forearms"}

COMPOUND_STEP_KG = 2.5
ISOLATION_STEP_KG = 1.25
DEFAULT_RIR_TARGET = 2


@dataclass
class NextTarget:
    weight_kg: float | None
    reps: int | None
    note: str


def _top_working_set(logged_sets: list[dict]) -> dict | None:
    """Heaviest set with a recorded weight (working sets drive progression)."""
    working = [s for s in logged_sets if s.get("weight_kg") is not None]
    if not working:
        return None
    return max(working, key=lambda s: (s.get("weight_kg") or 0, s.get("reps") or 0))


def compute_next_target(
    *,
    muscle_group: str | None,
    rir_target: int | None,
    reps_min: int | None,
    reps_max: int | None,
    logged_sets: list[dict],
) -> NextTarget:
    """Compute the next-session target for one exercise from this session's sets.

    `logged_sets` items look like {"weight_kg": float|None, "reps": int|None, "rir": int|None}.
    """
    top = _top_working_set(logged_sets)
    if top is None:
        return NextTarget(None, None, "Няма логнати работни серии с тегло.")

    weight = top.get("weight_kg")
    reps = top.get("reps")
    rir = top.get("rir")
    target = rir_target if rir_target is not None else DEFAULT_RIR_TARGET
    is_isolation = (muscle_group or "").lower() in _ISOLATION_MUSCLES
    step = ISOLATION_STEP_KG if is_isolation else COMPOUND_STEP_KG

    if rir is None:
        return NextTarget(weight, reps, "Логни RIR следващия път за точна прогресия; засега запази теглото.")

    if rir > target:
        new_weight = round(weight + step, 2)
        new_reps = reps_min if reps_min is not None else reps
        return NextTarget(new_weight, new_reps, f"RIR над целевия ({rir} > {target}) → +{step} кг.")

    if rir == target:
        base_reps = reps if reps is not None else (reps_min or 0)
        new_reps = min(base_reps + 1, reps_max) if reps_max is not None else base_reps + 1
        if reps_max is not None and base_reps >= reps_max:
            new_weight = round(weight + step, 2)
            return NextTarget(
                new_weight, reps_min if reps_min is not None else reps,
                f"Достигна върха на диапазона ({reps_max} повт.) → +{step} кг, върни се в дъното на диапазона.",
            )
        return NextTarget(weight, new_reps, f"RIR на целта ({rir}) → +1 повторение.")

    return NextTarget(weight, reps, f"RIR под целевия ({rir} < {target}) → запази теглото, фокус върху техника.")
