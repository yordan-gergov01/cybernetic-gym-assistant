"""The profile → calculators handoff.

This broke in production: the route reached into `data.lifts` and subscripted the
Pydantic `LiftEntry` models (`v["weight"]`), which raises TypeError. The exception was
caught and logged, so the API still returned 200 — the user finished a 16-step
onboarding and silently got a profile with no macros and no nutrition targets.

These tests lock the contract that the calculators accept exactly what the schema
produces, so a shape change fails here instead of at runtime.
"""
import pytest

from app.domain.calculators import run_all_calculators
from app.schemas import ProfileCreate


def profile(**overrides) -> ProfileCreate:
    base = dict(
        age=25,
        sex="male",
        height_cm=169,
        bodyweight_kg=68,
        body_fat_pct=11,
        goal="bulk",
        activity_level="sedentary",
        training_status=3,
        training_years=6,
        training_days_per_week=3,
        available_equipment="full_gym",
        session_duration_min=90,
        priority_muscles=["chest", "biceps", "shoulders"],
    )
    return ProfileCreate(**{**base, **overrides})


def run(data: ProfileCreate) -> dict:
    """Mirrors the route: dump the schema, then hand it to the calculators."""
    payload = data.model_dump()
    payload["body_fat_pct"] = data.body_fat_pct or 20.0
    return run_all_calculators(payload)


def test_calculators_accept_a_profile_with_lifts():
    """The regression: nested LiftEntry models must survive the handoff."""
    calc = run(profile(lifts={"Barbell Bench Press": {"weight": 100, "reps": 3}}))
    assert calc["lifts"]["Barbell Bench Press"].estimated_1rm > 100, "1RM must exceed a 3-rep max"


def test_calculators_work_without_any_lifts():
    calc = run(profile(lifts=None))
    assert calc["energy"].target_kcal > 0


def test_energy_targets_are_produced_for_every_macro():
    energy = run(profile())["energy"]
    for value in (energy.tdee_kcal, energy.target_kcal, energy.protein_g, energy.fat_g, energy.carbs_g):
        assert value and value > 0


def test_bulking_target_exceeds_maintenance():
    energy = run(profile(goal="bulk"))["energy"]
    assert energy.target_kcal > energy.tdee_kcal


def test_cutting_target_is_below_maintenance():
    energy = run(profile(goal="cut", body_fat_pct=20))["energy"]
    assert energy.target_kcal < energy.tdee_kcal


def test_volume_covers_the_priority_muscles():
    volume = run(profile(priority_muscles=["chest", "back"]))["volume"]
    assert volume.muscle_groups["chest"] > 0 and volume.muscle_groups["back"] > 0


@pytest.mark.parametrize("goal,bf,expect_override", [("bulk", 22, True), ("bulk", 11, False)])
def test_goal_validation_flags_a_mismatched_goal(goal, bf, expect_override):
    """Bulking at high body fat should be talked out of, and the API must say so."""
    validation = run(profile(goal=goal, body_fat_pct=bf))["goal_validation"]
    assert validation.override is expect_override
