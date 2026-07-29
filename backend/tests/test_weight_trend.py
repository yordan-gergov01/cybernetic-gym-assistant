"""Tests for EWMA weight-trend analysis and calorie-adjustment coaching.

The point of the trend is to see through daily water/glycogen noise, and the point of
the advice is to push intake in the direction that closes the gap to the goal rate —
those are what these tests assert.
"""
import random
from datetime import date, timedelta

from app.services.weight_trend import (
    MIN_POINTS,
    TARGET_WEEKLY_RATE,
    analyze_trend,
    recommend_calorie_adjustment,
)


def series(start_weight: float, kg_per_week: float, days: int, noise: float = 0.0, seed: int = 7):
    rng = random.Random(seed)
    d0, w = date(2026, 6, 1), start_weight
    out = []
    for i in range(days):
        w += kg_per_week / 7
        out.append((d0 + timedelta(days=i), round(w + rng.uniform(-noise, noise), 1)))
    return out


def test_too_few_points_returns_none():
    assert analyze_trend(series(90, -0.5, MIN_POINTS - 1)) is None


def test_detects_weight_loss_through_daily_noise():
    t = analyze_trend(series(90, -0.5, 28, noise=0.8))
    assert t.direction == "down"
    assert t.weekly_rate_kg < 0
    assert abs(t.weekly_rate_kg - (-0.5)) < 0.35, "noise must not swamp the underlying trend"


def test_detects_weight_gain():
    t = analyze_trend(series(80, 0.3, 28, noise=0.5))
    assert t.direction == "up" and t.weekly_rate_kg > 0


def test_stable_weight_reads_as_stable():
    t = analyze_trend(series(85, 0.0, 28, noise=0.4))
    assert t.direction == "stable"


def test_unsorted_input_is_handled():
    entries = series(90, -0.5, 20, noise=0.3)
    assert analyze_trend(list(reversed(entries))).weekly_rate_kg == analyze_trend(entries).weekly_rate_kg


def test_cutting_too_slowly_cuts_calories():
    advice = recommend_calorie_adjustment(goal="cut", actual_weekly_rate_kg=-0.1, current_calories=2200)
    assert not advice.on_track
    assert advice.calorie_delta < 0, "losing slower than target -> eat less"
    assert advice.new_calorie_target == 2200 + advice.calorie_delta


def test_bulking_but_losing_weight_raises_calories():
    advice = recommend_calorie_adjustment(goal="bulk", actual_weekly_rate_kg=-0.2, current_calories=3000)
    assert advice.calorie_delta > 0, "goal is to gain but weight is falling -> eat more"


def test_on_target_rate_keeps_calories():
    target = TARGET_WEEKLY_RATE["cut"]
    advice = recommend_calorie_adjustment(goal="cut", actual_weekly_rate_kg=target, current_calories=2200)
    assert advice.on_track
    assert advice.calorie_delta == 0
    assert advice.new_calorie_target == 2200


def test_advice_works_without_a_known_calorie_target():
    advice = recommend_calorie_adjustment(goal="cut", actual_weekly_rate_kg=0.2, current_calories=None)
    assert advice.new_calorie_target is None
    assert advice.calorie_delta < 0 and advice.note
