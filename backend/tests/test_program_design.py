"""Split selection and the ≥2x/week frequency rule.

The model, left to choose a split, produced Push/Pull/Legs over 3 days — every muscle
trained once a week, which the course explicitly rules out. These tests pin the rule so
it cannot quietly regress into "whatever the model felt like".
"""
import pytest

from app.domain.program_design import (
    MAJOR_MUSCLES,
    MIN_WEEKLY_FREQUENCY,
    frequency_violations,
    plan_muscle_adjustment,
    recommend_split,
    weekly_frequency,
)


def day(*muscles: str) -> dict:
    return {"exercises": [{"muscle_group": m} for m in muscles]}


def training_day(number: int, *exercises: tuple[str, str, int]) -> dict:
    """A day of (exercise name, muscle, sets), in the order they are performed."""
    return {
        "day_number": number,
        "is_rest_day": False,
        "exercises": [
            {"exercise_name": name, "muscle_group": muscle, "sets_prescribed": sets, "order_index": i}
            for i, (name, muscle, sets) in enumerate(exercises)
        ],
    }


@pytest.mark.parametrize("days", [1, 2, 3, 4, 5, 6, 7])
def test_every_schedule_gets_a_split(days):
    assert recommend_split(days).name


def test_three_days_is_not_push_pull_legs():
    """PPL on 3 days trains everything once a week — the exact bug this rule prevents."""
    split = recommend_split(3)
    assert split.name == "full_body"
    assert "ppl" not in split.name


def test_ppl_only_appears_when_it_can_hit_the_frequency_rule():
    """PPL reaches 2x/week only at six sessions."""
    assert recommend_split(6).name == "ppl"
    assert all(recommend_split(d).name != "ppl" for d in range(1, 6))


def test_four_days_uses_upper_lower():
    assert recommend_split(4).name == "upper_lower"


def test_split_explains_itself():
    """The rationale is shown to the user, so it must not be empty."""
    split = recommend_split(3)
    assert split.description_bg and split.rationale_bg


def test_frequency_counts_days_not_exercises():
    """Three chest exercises in one day is still one session of chest."""
    counts = weekly_frequency([day("chest", "chest", "chest")])
    assert counts["chest"] == 1


def test_push_pull_legs_over_three_days_is_flagged():
    days = [day("chest", "shoulders", "triceps"), day("back", "biceps"), day("quads", "hamstrings", "glutes")]
    violations = frequency_violations(days)
    assert set(violations) == {"back", "biceps", "chest", "glutes", "hamstrings", "quads", "shoulders", "triceps"}


def test_upper_lower_twice_a_week_passes():
    upper = day("chest", "back", "shoulders", "biceps", "triceps")
    lower = day("quads", "hamstrings", "glutes")
    assert frequency_violations([upper, lower, upper, lower]) == []


def test_full_body_three_times_passes():
    full = day("chest", "back", "shoulders", "quads", "hamstrings", "glutes", "biceps", "triceps")
    assert frequency_violations([full, full, full]) == []


def test_accessory_muscles_are_not_held_to_the_rule():
    """Calves and abs are commonly programmed less often; the course calls the
    per-muscle frequency a minimum, not a rigid target."""
    upper = day("chest", "back", "shoulders", "biceps", "triceps")
    lower = day("quads", "hamstrings", "glutes", "calves", "abs")
    violations = frequency_violations([upper, lower, upper, day("quads", "hamstrings", "glutes")])
    assert "calves" not in violations and "abs" not in violations


def test_a_missing_muscle_is_not_a_frequency_violation():
    """Omitting direct work (e.g. the user asked not to grow it) is a different concern."""
    assert "biceps" not in frequency_violations([day("chest"), day("chest")])


def test_frequency_is_raised_before_volume():
    """The course's order: another session first, more sets only if it cannot fit."""
    days = [
        training_day(1, ("Barbell Bench Press", "chest", 4), ("Cable Fly", "chest", 3)),
        training_day(2, ("Barbell Squat", "quads", 4)),
    ]
    adjustment = plan_muscle_adjustment(days, "chest", target_weekly_sets=16)
    assert adjustment.action == "move_exercise"
    assert adjustment.to_day == 2, "the day that does not train chest gains the work"


def test_raising_frequency_does_not_raise_the_weekly_sets():
    """Moving, not copying: the change under test is the frequency on its own."""
    days = [
        training_day(1, ("Barbell Bench Press", "chest", 4), ("Cable Fly", "chest", 3)),
        training_day(2, ("Barbell Squat", "quads", 4)),
    ]
    adjustment = plan_muscle_adjustment(days, "chest", target_weekly_sets=16)
    assert adjustment.from_day == 1 and adjustment.exercise_name == "Cable Fly"


def test_the_only_exercise_for_a_muscle_is_not_moved():
    """Relocating the single chest session leaves the frequency exactly where it was."""
    days = [
        training_day(1, ("Barbell Bench Press", "chest", 4)),
        training_day(2, ("Barbell Squat", "quads", 4)),
    ]
    adjustment = plan_muscle_adjustment(days, "chest", target_weekly_sets=16)
    assert adjustment.action == "add_sets"


def test_sets_are_added_when_every_day_already_trains_the_muscle():
    days = [
        training_day(1, ("Barbell Bench Press", "chest", 4), ("Cable Fly", "chest", 3)),
        training_day(2, ("Incline Press", "chest", 3)),
    ]
    adjustment = plan_muscle_adjustment(days, "chest", target_weekly_sets=16)
    assert adjustment.action == "add_sets"
    assert adjustment.exercise_name == "Barbell Bench Press", "the first exercise of the group"


def test_volume_stops_at_the_optimum_instead_of_climbing_forever():
    """At the profile's optimal weekly volume the plateau is not a volume problem."""
    days = [
        training_day(1, ("Barbell Bench Press", "chest", 5), ("Cable Fly", "chest", 5)),
        training_day(2, ("Incline Press", "chest", 6)),
    ]
    at_optimum = plan_muscle_adjustment(days, "chest", target_weekly_sets=16)
    assert at_optimum.action == "none"
    assert at_optimum.reason_bg

    below_optimum = plan_muscle_adjustment(days, "chest", target_weekly_sets=20)
    assert below_optimum.action == "add_sets", "the same program below the optimum still has room"


def test_a_muscle_the_program_does_not_train_gets_no_change():
    days = [training_day(1, ("Barbell Squat", "quads", 4))]
    assert plan_muscle_adjustment(days, "chest").action == "none"


def test_rest_days_never_receive_the_moved_exercise():
    days = [
        training_day(1, ("Barbell Bench Press", "chest", 4), ("Cable Fly", "chest", 3)),
        {"day_number": 2, "is_rest_day": True, "exercises": []},
        training_day(3, ("Barbell Squat", "quads", 4)),
    ]
    adjustment = plan_muscle_adjustment(days, "chest", target_weekly_sets=16)
    assert adjustment.to_day == 3


def test_threshold_comes_from_the_module():
    """Retuning the constant must change the rule, not silently invalidate the tests."""
    trained_once = [day(m) for m in ["chest"]]
    assert MIN_WEEKLY_FREQUENCY > 1
    assert ("chest" in frequency_violations(trained_once)) is (MIN_WEEKLY_FREQUENCY > 1)
    assert "chest" in MAJOR_MUSCLES
