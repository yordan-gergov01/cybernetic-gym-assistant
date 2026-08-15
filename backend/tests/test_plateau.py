"""Tests for the plateau / program-continuation engine.

Asserts the coaching decision - keep going, break the plateau, change one exercise,
change the muscle group's parameters, or look at recovery - rather than the arithmetic
behind it. Thresholds are imported from the module so that retuning a constant cannot
quietly invalidate what a test claims to prove.
"""
from datetime import date, timedelta

from app.domain.plateau import (
    ADVANCED_MIN_PROGRESS_PCT,
    ADVANCED_TRAINING_STATUS,
    MAX_PROGRAM_WEEKS,
    MIN_PROGRESS_PCT,
    MIN_REPS_PER_SET,
    STALL_SESSIONS,
    BenchmarkSet,
    classify_exercise,
    classify_scope,
    compare_sessions,
    decide_program_continuation,
    intensified_rep_range,
    intensified_rep_target,
    plateau_breaker_weight,
)

START = date(2026, 1, 5)


def series(*sets: tuple[float, int]) -> list[BenchmarkSet]:
    """Benchmark sets one week apart, oldest first."""
    return [
        BenchmarkSet(date=START + timedelta(weeks=i), weight_kg=w, reps=r)
        for i, (w, r) in enumerate(sets)
    ]


def progress(name="Barbell Bench Press", muscle="chest", sets=(), status=None):
    """One classified exercise; `status` overrides for scope-level tests."""
    result = classify_exercise(name, muscle, series(*sets) if sets else series((100, 8), (102.5, 8)))
    if status is None:
        return result
    return type(result)(**{**result.__dict__, "status": status})


# --- session-to-session judgement ------------------------------------------------


def test_more_reps_at_the_same_weight_counts_as_progress():
    change = compare_sessions(BenchmarkSet(START, 100, 8), BenchmarkSet(START, 100, 10), None)
    assert change.progressed
    assert not change.needs_reactive_deload


def test_fewer_reps_than_last_time_calls_for_a_reactive_deload():
    # Periodization p.45: reps coming out lower instead of higher is the explicit signal.
    change = compare_sessions(BenchmarkSet(START, 100, 10), BenchmarkSet(START, 100, 8), None)
    assert change.reps_dropped
    assert change.needs_reactive_deload
    assert not change.progressed


def test_a_gain_too_small_to_count_still_calls_for_a_deload():
    # Half a percent is movement, but under the 2.5% the course asks for.
    change = compare_sessions(BenchmarkSet(START, 100, 8), BenchmarkSet(START, 100.5, 8), None)
    assert 0 < change.change_pct < MIN_PROGRESS_PCT, "precondition: a real but sub-threshold gain"
    assert not change.progressed
    assert change.needs_reactive_deload


def test_advanced_trainees_are_judged_against_a_lower_bar():
    previous, latest = BenchmarkSet(START, 100, 8), BenchmarkSet(START, 101.5, 8)
    novice = compare_sessions(previous, latest, 1)
    advanced = compare_sessions(previous, latest, ADVANCED_TRAINING_STATUS)
    assert ADVANCED_MIN_PROGRESS_PCT < novice.change_pct < MIN_PROGRESS_PCT, "precondition"
    assert not novice.progressed
    assert advanced.progressed, "an advanced lifter cannot be expected to hold 2.5% a session"


# --- exercise-level classification ------------------------------------------------


def test_a_new_best_this_session_is_progress():
    result = classify_exercise("Barbell Squat", "quads", series((140, 5), (145, 5)))
    assert result.status == "progressing"


def test_one_missed_session_is_not_yet_a_plateau():
    # p.23: a single plateau has many possible causes; it is answered inside the
    # exercise, not by rebuilding the program.
    result = classify_exercise("Barbell Squat", "quads", series((140, 5), (145, 5), (145, 4)))
    assert result.sessions_since_best < STALL_SESSIONS, "precondition: only one miss"
    assert result.status == "holding"


def test_repeated_failure_to_beat_the_best_is_a_plateau():
    sets = [(140, 5), (145, 5)] + [(145, 4)] * STALL_SESSIONS
    result = classify_exercise("Barbell Squat", "quads", series(*sets))
    assert result.status == "stalled"


def test_matching_the_best_again_is_not_drifting_away_from_it():
    sets = [(140, 5), (145, 5)] + [(145, 5)] * STALL_SESSIONS
    result = classify_exercise("Barbell Squat", "quads", series(*sets))
    assert result.status != "stalled", "repeating a best is holding the level, not stalling"


def test_a_single_session_cannot_be_judged():
    result = classify_exercise("Deadlift", "back", series((180, 5)))
    assert result.status == "insufficient_data"


def test_sessions_are_ordered_before_being_judged():
    ordered = classify_exercise("Deadlift", "back", series((180, 5), (185, 5)))
    shuffled = classify_exercise("Deadlift", "back", list(reversed(series((180, 5), (185, 5)))))
    assert shuffled.status == ordered.status == "progressing"


# --- scope: the first question the course asks about a plateau ---------------------


def test_stalls_across_unrelated_muscle_groups_are_systemic():
    stalled = [
        progress("Barbell Bench Press", "chest", status="stalled"),
        progress("Barbell Squat", "quads", status="stalled"),
    ]
    assert classify_scope(stalled) == "systemic"


def test_stalls_within_one_movement_pattern_are_not_systemic():
    # Chest and triceps stall together in the same press; that is a local problem, not
    # a whole-body recovery failure.
    stalled = [
        progress("Barbell Bench Press", "chest", status="stalled"),
        progress("Triceps Pushdown", "triceps", status="stalled"),
    ]
    assert classify_scope(stalled) != "systemic"


def test_several_exercises_for_one_muscle_point_at_that_muscle():
    stalled = [
        progress("Barbell Bench Press", "chest", status="stalled"),
        progress("Incline Dumbbell Press", "chest", status="stalled"),
    ]
    assert classify_scope(stalled) == "local_muscle"


def test_a_lone_stalled_exercise_is_an_exercise_problem():
    assert classify_scope([progress("Lateral Raise", "shoulders", status="stalled")]) == "local_exercise"


def test_no_stalls_means_no_scope():
    assert classify_scope([]) is None


# --- program-level decision --------------------------------------------------------


def test_a_program_with_no_stalls_keeps_running_past_its_planned_end():
    # p.44: ending on a planned date is arbitrary. p.61: gaining strength excludes
    # overtraining.
    exercises = [progress("Barbell Squat", "quads"), progress("Barbell Bench Press", "chest")]
    decision = decide_program_continuation(exercises, total_weeks=8)
    assert decision.action == "extend"


def test_the_cap_ends_a_program_even_while_it_is_still_working():
    exercises = [progress("Barbell Squat", "quads")]
    decision = decide_program_continuation(exercises, total_weeks=MAX_PROGRAM_WEEKS)
    assert decision.action == "complete"


def test_a_systemic_stall_sends_the_user_to_recovery_not_to_a_new_program():
    exercises = [
        progress("Barbell Bench Press", "chest", status="stalled"),
        progress("Barbell Squat", "quads", status="stalled"),
    ]
    decision = decide_program_continuation(exercises, total_weeks=8)
    assert decision.action == "check_recovery"
    assert decision.scope == "systemic"


def test_one_stalled_exercise_changes_only_that_exercise():
    exercises = [
        progress("Lateral Raise", "shoulders", status="stalled"),
        progress("Barbell Squat", "quads"),
    ]
    decision = decide_program_continuation(exercises, total_weeks=8)
    assert decision.action == "adjust_exercise"
    assert decision.exercise_name == "Lateral Raise"


def test_a_stalled_muscle_group_changes_that_group_not_the_program():
    exercises = [
        progress("Barbell Bench Press", "chest", status="stalled"),
        progress("Incline Dumbbell Press", "chest", status="stalled"),
    ]
    decision = decide_program_continuation(exercises, total_weeks=8)
    assert decision.action == "adjust_muscle"
    assert decision.muscle_group == "chest"


def test_a_stall_blocks_extension_even_below_the_cap():
    exercises = [
        progress("Barbell Bench Press", "chest", status="stalled"),
        progress("Barbell Squat", "quads", status="stalled"),
    ]
    decision = decide_program_continuation(exercises, total_weeks=2)
    assert decision.action != "extend", "a stall is answered by changing the plan, not by more weeks"


# --- the two prescriptions the course gives ----------------------------------------


def test_intensification_lowers_the_rep_target_by_the_course_step():
    assert intensified_rep_target(12) == 12 - 4  # p.24: "by at least 4 points"


def test_intensification_refuses_to_go_below_the_growth_floor():
    # p.24: under 4 reps per set the repetition volume is too low for maximum growth,
    # so the course's next option is replacing the exercise instead.
    assert intensified_rep_target(MIN_REPS_PER_SET + 3) is None


def test_intensifying_a_range_keeps_it_as_wide_as_it_was():
    """The prescription is a range; intensifying moves it down, it does not narrow it."""
    low, high = intensified_rep_range(10, 15)
    assert high == intensified_rep_target(15)
    assert high - low == 15 - 10


def test_intensifying_never_prescribes_fewer_reps_than_the_growth_floor():
    low, high = intensified_rep_range(6, 8)
    assert low >= MIN_REPS_PER_SET
    assert high >= MIN_REPS_PER_SET


def test_a_range_that_cannot_be_lowered_has_no_intensified_form():
    # The top of the range is what decides; below it the exercise is replaced instead.
    assert intensified_rep_target(MIN_REPS_PER_SET + 3) is None
    assert intensified_rep_range(MIN_REPS_PER_SET, MIN_REPS_PER_SET + 3) is None


def test_a_plateau_breaker_is_heavier_than_the_session_that_stalled():
    assert plateau_breaker_weight(100, 10, is_isolation=False) > 100


def test_a_plateau_breaker_stays_below_a_max_attempt():
    # p.7 caps the breaker near a 3RM for compounds: a lifter grinding 100x10 has an
    # estimated max around 133, and the breaker must stay well under it.
    breaker = plateau_breaker_weight(100, 10, is_isolation=False)
    assert breaker < 133, "the breaker is a low-rep working session, not a 1RM attempt"


def test_an_exercise_already_at_low_reps_gets_no_ten_percent_jump():
    # At a 3RM there is no headroom left; +10% would just be a failed max attempt.
    near_max = plateau_breaker_weight(150, 3, is_isolation=False)
    assert near_max <= 150 * 1.1
    assert near_max < 150 * 1.05, "the cap, not the 10% rule, decides here"
