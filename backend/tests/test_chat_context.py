"""The facts the coach is handed about the user, before any model sees them.

These blocks are the only route by which the app's own numbers reach the chat, so what
matters is that they state what is known and say nothing when nothing is known - a blank
where a number should be is what the model fills in by itself.
"""
from app.prompts.registry import get_prompt

SESSION = dict(day_name="Горна част Б", is_rest_day=False, trained_today=False,
               week_number=3, total_weeks=8)
BENCH = {"name": "Barbell Bench Press", "sets": 4, "reps_min": 6, "reps_max": 8,
         "rir": 2, "target_weight_kg": 82.5, "note": None}


def today_block(**overrides):
    return get_prompt("chat_today_block")(**{**SESSION, "exercises": [BENCH], **overrides})


def nutrition_block(**overrides):
    defaults = dict(
        totals={"calories": 1450, "protein_g": 120, "fat_g": 40, "carbs_g": 150},
        targets={"calories": 2400, "protein_g": 180, "fat_g": 70, "carbs_g": 250},
        remaining={"calories": 950, "protein_g": 60, "fat_g": 30, "carbs_g": 100},
        has_targets=True,
    )
    return get_prompt("chat_nutrition_block")(**{**defaults, **overrides})


def test_the_session_is_listed_exercise_by_exercise():
    """The coach used to answer this from the course material and invent a workout, so
    what matters is that the real prescription arrives in full."""
    block = today_block()

    assert "Barbell Bench Press" in block
    assert "4 серии x 6-8 повт." in block
    assert "RIR 2" in block
    assert "82.5 кг" in block


def test_a_rest_day_says_so_instead_of_listing_nothing():
    """An empty block would leave the model to decide what a rest day means."""
    assert "почивен ден" in today_block(is_rest_day=True, exercises=[])


def test_a_session_already_logged_is_marked_as_done():
    assert "вече е записана" in today_block(trained_today=True)


def test_no_session_produces_no_block_at_all():
    """Silence is what triggers the "I do not have access" answer; a half-filled block
    would invite the model to complete it."""
    assert today_block(exercises=[], is_rest_day=False) == ""


def test_the_intake_block_states_eaten_target_and_remaining():
    block = nutrition_block()

    assert "1450" in block and "2400" in block and "950" in block


def test_food_logged_without_a_target_is_still_reported():
    """The app knows what was eaten even when nobody set a goal, and a number it holds
    must not reach the user as a guess."""
    block = nutrition_block(has_targets=False, targets={}, remaining={})

    assert "1450" in block
    assert "Няма зададена дневна цел" in block


def test_a_day_with_no_food_and_no_target_says_nothing():
    block = nutrition_block(
        has_targets=False, targets={}, remaining={},
        totals={"calories": 0, "protein_g": 0, "fat_g": 0, "carbs_g": 0},
    )

    assert block == ""
