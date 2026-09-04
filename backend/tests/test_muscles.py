"""The muscle names the coaching text puts in front of the user.

The risk this guards is not translation quality but coverage: a muscle the engines can
name and the dictionary cannot leaves an English word in a Bulgarian sentence, which is
exactly the bug these labels exist to remove.
"""
import re
from pathlib import Path

import pytest

from app.domain.calculators import calculate_optimal_volume
from app.domain.exercise_library import _CATEGORY_MUSCLE
from app.domain.muscles import MUSCLE_BG, muscle_bg
from app.domain.plateau import _MUSCLE_REGION

FRONTEND_LABELS = Path(__file__).resolve().parents[2] / "frontend" / "src" / "constants" / "muscles.ts"


def _muscles_the_engines_can_name() -> set[str]:
    """Every muscle group a user-facing engine can produce, from the engines themselves."""
    volume = calculate_optimal_volume(training_status=2, is_female=False)
    return set(volume.muscle_groups) | set(_MUSCLE_REGION) | set(_CATEGORY_MUSCLE.values())


def test_every_muscle_the_engines_can_name_has_a_bulgarian_label():
    missing = sorted(_muscles_the_engines_can_name() - set(MUSCLE_BG))

    assert not missing, f"these would appear in Bulgarian text in English: {missing}"


def test_a_muscle_inside_a_sentence_is_not_capitalised():
    """The screens show "Рамене" on a chip; a Bulgarian sentence says "за рамене"."""
    assert muscle_bg("shoulders") == "рамене"
    assert MUSCLE_BG["shoulders"] == "Рамене"


def test_an_unknown_muscle_keeps_its_english_name_instead_of_disappearing():
    """A generated program can name a group nobody has labelled yet. An English word in
    the sentence is visible and fixable; a hole in the sentence is neither."""
    assert muscle_bg("serratus") == "serratus"


def test_a_missing_muscle_produces_no_text_at_all():
    assert muscle_bg(None) == ""
    assert muscle_bg("") == ""


def test_the_label_survives_the_casing_the_api_uses():
    assert muscle_bg("Rear_Delts") == muscle_bg("rear_delts")


def test_the_backend_and_the_screens_call_each_muscle_the_same_thing():
    """Two dictionaries for one vocabulary drift the moment one of them is edited alone,
    and the user sees the same muscle under two names on two screens."""
    if not FRONTEND_LABELS.exists():
        pytest.skip("the frontend is not checked out next to the backend")

    block = FRONTEND_LABELS.read_text(encoding="utf-8").split("MUSCLE_LABELS")[1].split("}")[0]
    frontend = dict(re.findall(r"(\w+):\s*'([^']+)'", block))

    assert frontend == MUSCLE_BG
