"""Tests for the deterministic load-progression engine (Henselmans double progression).

Asserts the coaching decision — add weight / add a rep / hold — rather than restating
the arithmetic, so a broken rule cannot pass by returning a plausible constant.
"""
from app.services.progression import COMPOUND_STEP_KG, ISOLATION_STEP_KG, compute_next_target

RANGE = {"rir_target": 2, "reps_min": 8, "reps_max": 12}


def test_easy_set_adds_weight_and_resets_to_bottom_of_range():
    t = compute_next_target(muscle_group="chest", logged_sets=[{"weight_kg": 100, "reps": 10, "rir": 4}], **RANGE)
    assert t.weight_kg == 100 + COMPOUND_STEP_KG
    assert t.reps == RANGE["reps_min"]


def test_isolation_uses_smaller_weight_step():
    t = compute_next_target(muscle_group="biceps", logged_sets=[{"weight_kg": 20, "reps": 10, "rir": 4}], **RANGE)
    assert t.weight_kg == 20 + ISOLATION_STEP_KG
    assert ISOLATION_STEP_KG < COMPOUND_STEP_KG


def test_on_target_rir_adds_a_rep_and_keeps_weight():
    t = compute_next_target(muscle_group="chest", logged_sets=[{"weight_kg": 100, "reps": 10, "rir": 2}], **RANGE)
    assert t.weight_kg == 100
    assert t.reps == 11


def test_double_progression_adds_weight_at_top_of_rep_range():
    """At the top of the range the rep ladder is done — the load must go up instead."""
    t = compute_next_target(muscle_group="chest", logged_sets=[{"weight_kg": 100, "reps": 12, "rir": 2}], **RANGE)
    assert t.weight_kg == 100 + COMPOUND_STEP_KG
    assert t.reps == RANGE["reps_min"]


def test_hard_set_holds_the_weight():
    t = compute_next_target(muscle_group="chest", logged_sets=[{"weight_kg": 100, "reps": 8, "rir": 0}], **RANGE)
    assert t.weight_kg == 100
    assert t.reps == 8


def test_missing_rir_holds_and_says_so():
    """Without RIR we cannot judge effort — hold, and tell the user to log it (rule #12)."""
    t = compute_next_target(muscle_group="chest", logged_sets=[{"weight_kg": 100, "reps": 10, "rir": None}], **RANGE)
    assert t.weight_kg == 100
    assert "RIR" in t.note


def test_progression_is_driven_by_the_first_work_set():
    # Progression Guidelines p.3: only the first work set is the benchmark. Later sets
    # are performed under accumulated fatigue, so they must not decide the next load.
    sets = [{"weight_kg": 100, "reps": 8, "rir": 2}, {"weight_kg": 120, "reps": 3, "rir": 0}]
    t = compute_next_target(muscle_group="chest", logged_sets=sets, **RANGE)
    assert t.weight_kg == 100, "the first work set decides progression, not a heavier later one"


def test_warmups_are_not_mistaken_for_the_first_work_set():
    sets = [
        {"weight_kg": 40, "reps": 10, "rir": 6, "is_warmup": True},
        {"weight_kg": 100, "reps": 8, "rir": 4},
    ]
    t = compute_next_target(muscle_group="chest", logged_sets=sets, **RANGE)
    assert t.weight_kg == 100 + COMPOUND_STEP_KG, "the warm-up must not become the benchmark"


def test_no_working_sets_yields_no_target():
    t = compute_next_target(muscle_group="chest", logged_sets=[{"weight_kg": None, "reps": None, "rir": None}], **RANGE)
    assert t.weight_kg is None and t.reps is None
    assert t.note


def test_gym_increment_overrides_textbook_step_when_coarser():
    """A gym whose lightest jump is 5 kg cannot load +2.5 kg — the target must be loadable."""
    t = compute_next_target(
        muscle_group="chest",
        logged_sets=[{"weight_kg": 100, "reps": 10, "rir": 4}],
        min_barbell_increment_kg=5.0,
        **RANGE,
    )
    assert t.weight_kg == 105, "must jump by what the gym can actually load"


def test_finer_gym_increment_does_not_shrink_the_textbook_step():
    """Micro-plates allow 0.5 kg jumps, but the prescribed progression stays ~2.5 kg."""
    t = compute_next_target(
        muscle_group="chest",
        logged_sets=[{"weight_kg": 100, "reps": 10, "rir": 4}],
        min_barbell_increment_kg=0.5,
        **RANGE,
    )
    assert t.weight_kg == 100 + COMPOUND_STEP_KG


def test_dumbbell_increment_applies_to_isolation_work():
    t = compute_next_target(
        muscle_group="biceps",
        logged_sets=[{"weight_kg": 20, "reps": 10, "rir": 4}],
        min_dumbbell_increment_kg=2.0,
        **RANGE,
    )
    assert t.weight_kg == 22.0, "dumbbell sets step by the rack's real gap"


def test_unknown_increments_fall_back_to_textbook_steps():
    t = compute_next_target(
        muscle_group="chest", logged_sets=[{"weight_kg": 100, "reps": 10, "rir": 4}], **RANGE
    )
    assert t.weight_kg == 100 + COMPOUND_STEP_KG
