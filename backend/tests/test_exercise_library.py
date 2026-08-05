"""Tests for the parsed PTC exercise library.

The library is parsed out of a PDF extraction, so the risk is not arithmetic but silent
loss: a heading that stops being recognised drops an exercise, and nothing would notice.
These assert the properties that must hold for a swap suggestion to be trustworthy.

They are skipped when the course guide is not present, since it is git-ignored material.
"""
import pytest

from app.domain.exercise_library import (
    alternatives,
    by_category,
    by_muscle,
    categories,
    find,
    load_exercises,
)

pytestmark = pytest.mark.skipif(
    not load_exercises(), reason="course exercise guide not available in data/processed"
)


def test_the_guides_own_categories_are_all_represented():
    # The guide's contents page lists 21 movement patterns; a parser that stops
    # recognising one would quietly lose every exercise under it.
    assert len(categories()) == 21


def test_every_exercise_is_filed_under_a_category_and_region():
    orphans = [e.name for e in load_exercises() if not e.category or not e.region]
    assert not orphans, f"exercises with nowhere to belong: {orphans}"


def test_every_category_maps_to_a_muscle_group():
    # Without a muscle group an exercise cannot be matched against the program's
    # muscle_group values, so a stalled muscle would find no candidates.
    unmapped = sorted({e.category for e in load_exercises() if not e.muscle_group})
    assert not unmapped, f"categories with no muscle: {unmapped}"


def test_names_are_unique_so_a_swap_is_unambiguous():
    names = [e.name for e in load_exercises()]
    assert len(names) == len(set(names))


def test_prose_is_not_parsed_as_an_exercise():
    # The extractor promotes stray sentences to headings; they must not become
    # exercises the user can be told to perform.
    for exercise in load_exercises():
        assert ". " not in exercise.name
        assert not exercise.name.startswith("•")
        assert not exercise.name.endswith(".")


def test_technique_cues_survive_a_page_break():
    # The Arnold Press heading sits at the bottom of one page and its bullets on the
    # next; parsing page by page truncates it to nothing.
    arnold = find("Arnold Press")
    assert arnold is not None
    assert len(arnold.cues) >= 2


def test_alternatives_share_the_movement_pattern():
    bench = find("Barbell bench press [2, 3]")
    assert bench is not None, "precondition: the bench press is in the library"
    swaps = alternatives(bench.name)
    assert swaps, "a compound press must have alternatives to swap to"
    assert all(s.category == bench.category for s in swaps)


def test_an_exercise_is_never_offered_as_its_own_alternative():
    for name in ("Barbell bench press [2, 3]", "Barbell overhead press"):
        assert all(s.name != name for s in alternatives(name))


def test_an_unknown_exercise_yields_no_alternatives_rather_than_a_guess():
    # Swapping in something from an unrelated pattern would change what the program
    # trains, which is worse than offering nothing.
    assert alternatives("Totally Made Up Lift") == ()


def test_lookup_ignores_case_and_surrounding_space():
    assert find("  barbell OVERHEAD press  ") is not None


def test_filters_agree_with_the_exercises_own_fields():
    hinges = by_category("Hip hinges")
    assert hinges
    assert all(e.category == "Hip hinges" for e in hinges)
    quads = by_muscle("quads")
    assert quads
    assert all(e.muscle_group == "quads" for e in quads)
