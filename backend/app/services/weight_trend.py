"""Deterministic bodyweight trend analysis and calorie-adjustment coaching.

Daily weigh-ins are noisy (water, glycogen, gut content), so the real trend is
extracted with an exponentially weighted moving average (EWMA) rather than raw
readings. The weekly rate of change is the slope of the smoothed trend.

The calorie recommendation is pure arithmetic: compare the
actual weekly rate to the target rate for the user's goal and convert the gap into
a daily calorie adjustment. ~7700 kcal ≈ 1 kg of bodyweight change.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

MIN_POINTS = 3
EWMA_SPAN = 7          # ~1 week smoothing
TREND_WINDOW_DAYS = 28  # fit the rate over the last 4 weeks of the trend
KCAL_PER_KG = 7700

# Target weekly bodyweight change (kg/week) per validated goal.
TARGET_WEEKLY_RATE = {
    "bulk": 0.25,
    "lean_bulk": 0.25,
    "maintain": 0.0,
    "cut": -0.5,
    "aggressive_cut": -0.75,
}

# Only suggest a calorie change once the adjustment is meaningful.
MIN_CALORIE_ADJUSTMENT = 100


@dataclass
class TrendResult:
    current_weight: float
    weekly_rate_kg: float
    direction: str          # "up" | "down" | "stable"
    smoothed: list[dict]     # [{date, ewma, raw}]
    points: int


@dataclass
class CalorieAdvice:
    goal: str
    target_weekly_rate_kg: float
    actual_weekly_rate_kg: float
    on_track: bool
    calorie_delta: int              # suggested change to daily calories (signed)
    new_calorie_target: int | None  # current + delta, if current known
    note: str


def _ewma(values: list[float], span: int = EWMA_SPAN) -> list[float]:
    alpha = 2 / (span + 1)
    out: list[float] = []
    s = values[0]
    for v in values:
        s = alpha * v + (1 - alpha) * s
        out.append(s)
    return out


def analyze_trend(entries: list[tuple]) -> TrendResult | None:
    """`entries`: list of (date, weight_kg), any order. None if too few points."""
    if len(entries) < MIN_POINTS:
        return None
    rows = sorted(entries, key=lambda e: e[0])
    weights = [float(w) for _, w in rows]
    ewma = _ewma(weights)

    window = min(len(ewma), TREND_WINDOW_DAYS)
    ys = ewma[-window:]
    slope_per_point = float(np.polyfit(np.arange(window), ys, 1)[0]) if window >= 2 else 0.0
    weekly_rate = round(slope_per_point * 7, 3)

    direction = "down" if weekly_rate < -0.05 else "up" if weekly_rate > 0.05 else "stable"
    smoothed = [
        {"date": str(d), "ewma": round(e, 2), "raw": round(w, 2)}
        for (d, w), e in zip(rows, ewma)
    ]
    return TrendResult(
        current_weight=round(ewma[-1], 2),
        weekly_rate_kg=weekly_rate,
        direction=direction,
        smoothed=smoothed[-12:],
        points=len(rows),
    )


def recommend_calorie_adjustment(
    *,
    goal: str | None,
    actual_weekly_rate_kg: float,
    current_calories: int | None,
) -> CalorieAdvice:
    """Turn the gap between actual and target weekly rate into a calorie adjustment."""
    goal = goal or "maintain"
    target_rate = TARGET_WEEKLY_RATE.get(goal, 0.0)

    # Positive gap => need faster gain / slower loss => eat more.
    rate_gap = target_rate - actual_weekly_rate_kg
    raw_delta = rate_gap * KCAL_PER_KG / 7
    delta = int(round(raw_delta / 50.0) * 50)

    if abs(delta) < MIN_CALORIE_ADJUSTMENT:
        return CalorieAdvice(
            goal=goal, target_weekly_rate_kg=target_rate, actual_weekly_rate_kg=actual_weekly_rate_kg,
            on_track=True, calorie_delta=0,
            new_calorie_target=current_calories,
            note=f"В графика си: реална скорост {actual_weekly_rate_kg:+.2f} кг/седм спрямо цел {target_rate:+.2f}. Запази калориите.",
        )

    new_target = current_calories + delta if current_calories else None
    verb = "увеличи" if delta > 0 else "намали"
    note = (
        f"Реална скорост {actual_weekly_rate_kg:+.2f} кг/седм, целта е {target_rate:+.2f}. "
        f"{verb} дневните калории с {abs(delta)} ккал"
    )
    note += f" (към {new_target} ккал)." if new_target else "."
    return CalorieAdvice(
        goal=goal, target_weekly_rate_kg=target_rate, actual_weekly_rate_kg=actual_weekly_rate_kg,
        on_track=False, calorie_delta=delta, new_calorie_target=new_target, note=note,
    )
