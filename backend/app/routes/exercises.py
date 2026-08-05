from fastapi import APIRouter, Depends, HTTPException, Query

from app.deps import get_current_user
from app.domain import exercise_library
from app.models import User
from app.schemas import ExerciseOut

router = APIRouter(prefix="/exercises", tags=["exercises"])


def _to_out(exercise: exercise_library.Exercise) -> ExerciseOut:
    return ExerciseOut(
        name=exercise.name,
        category=exercise.category,
        region=exercise.region,
        muscle_group=exercise.muscle_group,
        cues=list(exercise.cues),
    )


@router.get("", response_model=list[ExerciseOut])
async def list_exercises(
    category: str | None = Query(None, description="Movement pattern, e.g. 'Hip hinges'"),
    muscle_group: str | None = Query(None, description="e.g. 'quads'"),
    search: str | None = Query(None, min_length=2),
    user: User = Depends(get_current_user),
):
    """The course exercise library, optionally filtered."""
    _ = user
    if category:
        results = exercise_library.by_category(category)
    elif muscle_group:
        results = exercise_library.by_muscle(muscle_group)
    else:
        results = exercise_library.load_exercises()

    if search:
        needle = search.strip().casefold()
        results = tuple(e for e in results if needle in e.name.casefold())
    return [_to_out(e) for e in results]


@router.get("/categories", response_model=list[str])
async def list_categories(user: User = Depends(get_current_user)):
    """Movement patterns, in the order the course guide lists them."""
    _ = user
    return list(exercise_library.categories())


@router.get("/alternatives", response_model=list[ExerciseOut])
async def list_alternatives(
    name: str = Query(..., description="Exact exercise name to replace"),
    user: User = Depends(get_current_user),
):
    """Swaps for one exercise: everything the guide files under the same pattern.

    This is what the plateau engine's `adjust_exercise` verdict needs - an exercise that
    stalled and cannot be intensified any further is replaced by a sibling, so the
    program keeps training the same movement.
    """
    _ = user
    if not exercise_library.find(name):
        raise HTTPException(404, f"Упражнението „{name}“ не е в библиотеката на курса.")
    return [_to_out(e) for e in exercise_library.alternatives(name)]
