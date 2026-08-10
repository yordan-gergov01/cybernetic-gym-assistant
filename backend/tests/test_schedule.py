"""Tests for the scheduling and volume rules behind the Today screen.

They assert the coaching-visible behaviour - which session comes next, when a day reads
as rest, what counts towards volume - not the arithmetic that produces it.
"""
from datetime import date, timedelta

from app.domain.schedule import (
    DEFAULT_REST_SECONDS,
    WORK_SECONDS_PER_SET,
    calendar_week,
    estimate_session,
    is_rest_today,
    next_day_index,
    week_number,
)
from app.domain.training_volume import (
    sets_per_muscle,
    tonnage_kg,
    weekly_volume,
    working_set_count,
)

MONDAY = date(2026, 8, 3)  # a Monday
WEDNESDAY = MONDAY + timedelta(days=2)


# --- where in the program -----------------------------------------------------------


def test_the_first_week_is_week_one():
    assert week_number(MONDAY, MONDAY, 8) == 1


def test_the_week_advances_with_the_calendar():
    assert week_number(MONDAY, MONDAY + timedelta(days=14), 8) == 3


def test_the_week_never_runs_past_the_program():
    assert week_number(MONDAY, MONDAY + timedelta(weeks=40), 8) == 8


def test_a_program_with_no_start_date_still_reports_a_week():
    assert week_number(None, MONDAY, 8) == 1


# --- which session is next ----------------------------------------------------------


def test_the_next_session_is_the_one_after_the_last_logged():
    # Two sessions done in a four-day rotation -> the third day is next.
    assert next_day_index(sessions_completed=2, training_day_count=4) == 2


def test_the_rotation_wraps_around_instead_of_ending():
    assert next_day_index(sessions_completed=4, training_day_count=4) == 0


def test_missing_a_day_does_not_strand_the_plan():
    # The schedule follows what was logged, so a skipped week simply carries on from
    # where the user actually is - it never leaves them permanently a day behind.
    assert next_day_index(sessions_completed=5, training_day_count=4) == 1


def test_a_program_with_no_training_days_has_no_next_session():
    assert next_day_index(sessions_completed=3, training_day_count=0) is None


# --- rest days ----------------------------------------------------------------------


def test_today_is_rest_once_it_has_been_trained():
    assert is_rest_today(trained_today=True, sessions_this_week=1, weekly_target=4)


def test_today_is_rest_once_the_week_is_complete():
    assert is_rest_today(trained_today=False, sessions_this_week=4, weekly_target=4)


def test_an_unfinished_week_is_not_a_rest_day():
    assert not is_rest_today(trained_today=False, sessions_this_week=2, weekly_target=4)


def test_no_weekly_target_never_forces_a_rest_day():
    assert not is_rest_today(trained_today=False, sessions_this_week=9, weekly_target=0)


# --- the week strip -----------------------------------------------------------------


def test_the_week_starts_on_monday_and_has_seven_days():
    week = calendar_week(WEDNESDAY, set())
    assert len(week) == 7
    assert week[0].date == MONDAY
    assert week[0].date.weekday() == 0


def test_the_strip_marks_the_days_that_were_trained_and_today():
    week = calendar_week(WEDNESDAY, {MONDAY})
    assert [d.trained for d in week] == [True, False, False, False, False, False, False]
    assert [d.is_today for d in week] == [False, False, True, False, False, False, False]


# --- session estimate ---------------------------------------------------------------


def test_a_longer_session_is_estimated_as_longer():
    short = estimate_session([{"sets_prescribed": 3, "rest_seconds": 120}])
    long = estimate_session([{"sets_prescribed": 6, "rest_seconds": 120}])
    assert long.minutes > short.minutes
    assert long.total_sets == 6


def test_longer_rests_make_for_a_longer_session():
    quick = estimate_session([{"sets_prescribed": 4, "rest_seconds": 60}])
    slow = estimate_session([{"sets_prescribed": 4, "rest_seconds": 180}])
    assert slow.minutes > quick.minutes


def test_an_exercise_without_a_prescription_still_counts():
    # A missing set count must not silently make the session look empty.
    estimate = estimate_session([{}])
    assert estimate.exercise_count == 1
    assert estimate.total_sets > 0
    assert estimate.minutes >= (DEFAULT_REST_SECONDS + WORK_SECONDS_PER_SET) // 60


# --- volume -------------------------------------------------------------------------


def working(**overrides) -> dict:
    return {"weight_kg": 100, "reps": 8, "is_warmup": False, "muscle_group": "chest", **overrides}


def test_warmups_do_not_count_as_volume():
    assert working_set_count([working(), working(is_warmup=True)]) == 1
    assert sets_per_muscle([working(), working(is_warmup=True)]) == {"chest": 1}


def test_a_set_with_no_reps_logged_is_not_counted():
    assert working_set_count([working(reps=None)]) == 0


def test_tonnage_is_the_load_actually_moved():
    assert tonnage_kg([working(weight_kg=100, reps=10)]) == 1000
    assert tonnage_kg([working(weight_kg=100, reps=10), working(weight_kg=50, reps=10)]) == 1500


def test_bodyweight_work_is_not_guessed_into_the_tonnage():
    # Inventing a load from the user's bodyweight would inflate the number silently.
    assert tonnage_kg([working(weight_kg=None, reps=10)]) == 0


def test_weekly_volume_reports_done_against_target():
    volume = weekly_volume([working(), working()], {"chest": 18})
    chest = next(v for v in volume if v.muscle_group == "chest")
    assert chest.sets_done == 2
    assert chest.sets_target == 18


def test_a_muscle_with_a_target_but_no_work_still_appears():
    volume = weekly_volume([], {"back": 16})
    assert [(v.muscle_group, v.sets_done, v.sets_target) for v in volume] == [("back", 0, 16)]


def test_work_outside_the_plan_is_shown_rather_than_dropped():
    # Training something the plan never targeted is exactly what the user should see.
    volume = weekly_volume([working(muscle_group="calves")], {"chest": 18})
    calves = next(v for v in volume if v.muscle_group == "calves")
    assert calves.sets_done == 1
    assert calves.sets_target is None


# --- strength trend -----------------------------------------------------------------


def bench(day_offset: int, weight: float, reps: int):
    from app.domain.plateau import BenchmarkSet

    return BenchmarkSet(date=MONDAY + timedelta(days=day_offset), weight_kg=weight, reps=reps)


def test_strength_change_is_measured_from_the_start_of_the_window():
    from app.domain.plateau import strength_trend

    trend = strength_trend([bench(0, 100, 5), bench(7, 105, 5)])
    assert trend.change_kg > 0
    assert trend.points[0] < trend.points[-1]


def test_the_headline_max_is_the_best_lifted_not_the_latest():
    from app.domain.plateau import strength_trend

    # A bad session after a real best must not erase the best.
    trend = strength_trend([bench(0, 100, 5), bench(7, 110, 5), bench(14, 100, 5)])
    assert trend.best_e1rm == max(trend.points)
    assert trend.best_e1rm > trend.points[-1]


def test_sessions_out_of_order_are_sorted_before_being_compared():
    from app.domain.plateau import strength_trend

    forward = strength_trend([bench(0, 100, 5), bench(7, 110, 5)])
    backward = strength_trend([bench(7, 110, 5), bench(0, 100, 5)])
    assert forward.change_kg == backward.change_kg


def test_no_sessions_yields_no_trend_rather_than_an_error():
    from app.domain.plateau import strength_trend

    trend = strength_trend([])
    assert trend.points == () and trend.change_kg == 0
