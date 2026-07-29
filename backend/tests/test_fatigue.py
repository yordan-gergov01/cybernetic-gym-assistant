"""Tests for the deterministic deload decision engine.

These assert the coaching INTENT (which decision comes out, and why), not the raw
score arithmetic — the thresholds may be retuned, but "declining performance plus
poor recovery means deload" must never silently stop being true (CLAUDE.md rule #9).
"""
from app.services.fatigue import CAUTION_THRESHOLD, DELOAD_THRESHOLD, assess_fatigue


def answers(**overrides):
    base = {
        "recovery_quality": "good",
        "performance_trend": "stable",
        "joint_pain": False,
        "sleep_quality": "good",
        "motivation": "high",
        "appetite": "normal",
    }
    return {**base, **overrides}


def test_fresh_and_improving_continues():
    d = assess_fatigue(answers(performance_trend="improving"))
    assert d.decision == "continue"
    assert d.factors == []


def test_multiple_fatigue_signals_trigger_deload():
    d = assess_fatigue(answers(
        recovery_quality="poor", performance_trend="declining", joint_pain=True,
        sleep_quality="poor", motivation="low", appetite="decreased",
    ))
    assert d.decision == "deload"
    assert d.score >= DELOAD_THRESHOLD
    assert "болка в стави" in d.factors


def test_mild_signals_trigger_caution_not_deload():
    d = assess_fatigue(answers(recovery_quality="fair", sleep_quality="fair", motivation="moderate"))
    assert d.decision == "caution"
    assert CAUTION_THRESHOLD <= d.score < DELOAD_THRESHOLD


def test_declining_performance_with_poor_recovery_overrides_threshold():
    """The classic 'fatigue masking fitness' pattern must deload even below the score threshold."""
    a = answers(performance_trend="declining", recovery_quality="poor")
    d = assess_fatigue(a)
    assert d.score < DELOAD_THRESHOLD, "precondition: this case is below the numeric threshold"
    assert d.decision == "deload", "hard override must fire regardless of score"


def test_declining_performance_with_poor_sleep_overrides_threshold():
    d = assess_fatigue(answers(performance_trend="declining", sleep_quality="poor"))
    assert d.decision == "deload"


def test_recommendation_mentions_the_named_factors():
    d = assess_fatigue(answers(sleep_quality="poor", joint_pain=True))
    assert "лош сън" in d.factors and "болка в стави" in d.factors
    for factor in d.factors:
        assert factor in d.recommendation_bg


def test_missing_answers_default_to_no_fatigue():
    d = assess_fatigue({})
    assert d.decision == "continue"
