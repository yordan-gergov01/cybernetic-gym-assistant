"""The PTC exercise library, parsed from the course guide.

Used to answer "what else could I do instead of this?" - which is what the plateau
engine asks for when a single exercise stalls and the course's advice is to replace it
(`domain/plateau.py`, action `adjust_exercise`).

The categories are the guide's own ("Overhead presses", "Hip hinges", ...), taken from
its contents page rather than invented here, so two exercises in the same category are
alternatives by the course's grouping, not by our guess.

Like the body-fat rubric in `bf_reference.py`, the guide is copyrighted course material
living in git-ignored data/, so the library is built at runtime from the extracted JSON
and cached in memory. There is no database table: this is static reference content that
nobody edits, and a table would need a migration and a seed step to hold exactly the
same rows.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from functools import lru_cache

from app.core.config import settings

logger = logging.getLogger(__name__)

_LIBRARY_FILE = "pdf_extracted/Exercise_Library_PTC.json"

_REGIONS = ("Upper body", "Lower body")

# Which muscle group a category trains, so the library lines up with the muscle_group
# values used on ProgramExercise. Our mapping, not the guide's - the guide groups by
# movement pattern and never states a muscle per category.
_CATEGORY_MUSCLE = {
    "Overhead presses": "shoulders",
    "Lateral raises": "shoulders",
    "Chest presses": "chest",
    "Chest flys": "chest",
    "Triceps isolation exercises": "triceps",
    "Pulls": "back",
    "Upper back exercises": "back",
    "Shrugs": "traps",
    "Lat exercises": "back",
    "Biceps isolation exercises": "biceps",
    "Ab work": "abs",
    "Neck exercises": "neck",
    "Forearm exercises": "forearms",
    "Squat type movements": "quads",
    "Quad isolation exercises": "quads",
    "Hip hinges": "hamstrings",
    "Leg curls": "hamstrings",
    "Erector spinae exercises": "back",
    "Calf exercises": "calves",
    "Glute exercises": "glutes",
    "Adduction exercises": "adductors",
}

# A heading longer than this is prose the extractor mistook for a title.
_MAX_NAME_LEN = 120


@dataclass(frozen=True)
class Exercise:
    name: str
    category: str # the guide's movement-pattern grouping
    region: str # "Upper body" | "Lower body"
    muscle_group: str | None
    cues: tuple[str, ...]  # technique bullets, verbatim from the guide
    page: int


def _normalize(text: str) -> str:
    """Curly quotes are normalized inconsistently between headings and body text."""
    return (
        text.replace("’", "'").replace("‘", "'")
        .replace("“", '"').replace("”", '"')
    )


def _is_exercise_name(heading: str, known: set[str]) -> bool:
    """Reject the fragments the PDF extractor promotes to headings.

    A bullet, a sentence that ends mid-thought, or anything with a sentence break in it
    is body text, not an exercise title.
    """
    if heading in known or heading.startswith("•"):
        return False
    if ". " in heading or heading.endswith("."):
        return False
    return len(heading) <= _MAX_NAME_LEN


def _read_taxonomy(contents_page: str) -> tuple[list[str], list[str]]:
    """Categories and regions, straight off the guide's contents page."""
    categories, regions = [], []
    for line in (ln.strip() for ln in contents_page.splitlines()):
        if not line or line.isdigit() or line == "Contents":
            continue
        (regions if line in _REGIONS else categories).append(line)
    return categories, regions


@lru_cache(maxsize=1)
def load_exercises() -> tuple[Exercise, ...]:
    """Parse the guide into exercises. Returns () when the guide is unavailable.

    The pages are joined into one stream before splitting, because an exercise's cues
    routinely continue past a page break; parsing page by page silently truncates them.
    """
    path = settings.backend_root / "data" / "processed" / _LIBRARY_FILE
    try:
        pages = json.loads(path.read_text(encoding="utf-8"))["pages"]
    except Exception:
        logger.warning(
            "Exercise library unavailable at %s; exercise alternatives will be empty",
            path, exc_info=True,
        )
        return ()

    categories, regions = _read_taxonomy(pages[1].get("text") or "")
    known = set(categories) | set(regions)

    stream_parts: list[str] = []
    headings: list[tuple[str, int, int]] = []
    offset = 0
    for page in pages[2:]:
        # Drop the leading page number so it cannot end up inside a cue.
        text = re.sub(r"^\s*\d+\s*\n", "", page.get("text") or "")
        stream_parts.append(text)
        for heading in page.get("headings") or []:
            headings.append((heading, offset, page.get("page_num", 0)))
        offset += len(text) + 1
    stream = _normalize("\n".join(stream_parts))

    marks: list[tuple[int, str, int]] = []
    cursor = 0
    dropped = 0
    for heading, hint, page_num in headings:
        if heading not in known and not _is_exercise_name(heading, known):
            dropped += 1
            continue
        key = _normalize(heading)
        # Search forward from the previous heading so a name repeated in body text
        # cannot pull the split backwards.
        index = stream.find(key, max(cursor, hint - 200))
        if index == -1:
            index = stream.find(key, cursor)
        if index == -1:
            logger.warning("Exercise library: heading %r (p.%s) not found in the text", heading, page_num)
            continue
        marks.append((index, heading, page_num))
        cursor = index + len(key)

    exercises: list[Exercise] = []
    region = category = None
    for i, (start, heading, page_num) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(stream)
        body = stream[start + len(heading):end]
        if heading in regions:
            region = heading
            continue
        if heading in categories:
            category = heading
            continue
        cues = tuple(
            cue for cue in (
                re.sub(r"\s+", " ", chunk).strip()
                for chunk in re.split(r"\n\s*•\s*", body)
            )
            if len(cue) > 3
        )
        exercises.append(
            Exercise(
                name=heading,
                category=category or "",
                region=region or "",
                muscle_group=_CATEGORY_MUSCLE.get(category or ""),
                cues=cues,
                page=page_num,
            )
        )

    # Some entries are a bare name in the guide, with the technique shown on video only.
    # That is the source, not a parse failure, but it should be visible either way.
    without_cues = sum(1 for e in exercises if not e.cues)
    logger.info(
        "Exercise library: %d exercises in %d categories (%d headings dropped as prose, "
        "%d entries have no technique cues in the guide)",
        len(exercises), len(categories), dropped, without_cues,
    )
    return tuple(exercises)


def find(name: str) -> Exercise | None:
    """Look an exercise up by name, case- and whitespace-insensitively."""
    key = _normalize(name).strip().casefold()
    for exercise in load_exercises():
        if _normalize(exercise.name).strip().casefold() == key:
            return exercise
    return None


def alternatives(name: str) -> tuple[Exercise, ...]:
    """Other exercises the guide files under the same movement pattern.

    An unknown name yields nothing rather than a guess: swapping a stalled exercise for
    something from an unrelated category would change what the program trains.
    """
    exercise = find(name)
    if not exercise or not exercise.category:
        return ()
    return tuple(e for e in load_exercises() if e.category == exercise.category and e.name != exercise.name)


def by_category(category: str) -> tuple[Exercise, ...]:
    key = category.strip().casefold()
    return tuple(e for e in load_exercises() if e.category.casefold() == key)


def by_muscle(muscle_group: str) -> tuple[Exercise, ...]:
    key = muscle_group.strip().casefold()
    return tuple(e for e in load_exercises() if (e.muscle_group or "").casefold() == key)


def categories() -> tuple[str, ...]:
    """Movement patterns present in the library, in the guide's own order."""
    seen: dict[str, None] = {}
    for exercise in load_exercises():
        if exercise.category:
            seen.setdefault(exercise.category, None)
    return tuple(seen)
