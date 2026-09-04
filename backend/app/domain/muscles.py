"""Bulgarian names for the muscle groups the rest of the code speaks in English.

Exercise names stay in English everywhere - they are what is written on the rack and in
the course - but a muscle group left in English inside a Bulgarian sentence is simply an
untranslated word: "Няколко упражнения за shoulders са в двоен застой".

The labels mirror frontend/src/constants/muscles.ts word for word. The same muscle must
not be called two different things depending on which screen shows it, so the two lists
are changed together and a test holds them to it.
"""
from __future__ import annotations

MUSCLE_BG: dict[str, str] = {
    "chest": "Гърди",
    "back": "Гръб",
    "lats": "Латисимус",
    "shoulders": "Рамене",
    "rear_delts": "Задно рамо",
    "front_delts": "Предно рамо",
    "traps": "Трапец",
    "biceps": "Бицепс",
    "triceps": "Трицепс",
    "forearms": "Предмишници",
    "quads": "Квадрицепс",
    "hamstrings": "Задно бедро",
    "glutes": "Глутеус",
    "calves": "Прасци",
    "adductors": "Аддуктор",
    "abs": "Корем",
    "neck": "Врат",
}


def muscle_bg(muscle: str | None) -> str:
    """The Bulgarian name of a muscle group as it belongs inside a sentence.

    Lowercase: these are common nouns, and "упражнения за Рамене" is a capital letter in
    the middle of a Bulgarian sentence. MUSCLE_BG keeps the capitalised form, which is
    what a chip or a heading needs when the word stands on its own.

    An unlabelled muscle falls back to its English key rather than to nothing: a
    generated program can name a group this list has never seen, and a hole in the
    sentence hides that while an English word shows it.
    """
    if not muscle:
        return ""
    return MUSCLE_BG.get(muscle.strip().lower(), muscle).lower()
