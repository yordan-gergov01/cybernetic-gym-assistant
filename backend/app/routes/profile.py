import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.deps import get_current_user
from app.models import NutritionTarget, User, UserProfile
from app.schemas import NutritionTargetOut, ProfileCreate, ProfileOut
from app.domain.calculators import run_all_calculators

router = APIRouter(prefix="/profile", tags=["profile"])
logger = logging.getLogger(__name__)


async def _apply_calculators(db: AsyncSession, profile: UserProfile, source: dict) -> bool:
    """Run the deterministic calculators and store their output on the profile.

    Returns True on success. Failure is logged and reported to the caller rather than
    swallowed - a profile without macros looks fine but silently breaks nutrition
    targets and program generation.
    """
    try:
        payload = dict(source)
        payload["body_fat_pct"] = payload.get("body_fat_pct") or 20.0
        calc = run_all_calculators(payload)

        profile.goal_validated = calc["goal_validation"].recommended_goal
        profile.calculator_results = {
            "energy": {
                "tdee_kcal": calc["energy"].tdee_kcal,
                "target_kcal": calc["energy"].target_kcal,
                "protein_g": calc["energy"].protein_g,
                "fat_g": calc["energy"].fat_g,
                "carbs_g": calc["energy"].carbs_g,
                "lbm_kg": calc["energy"].lbm_kg,
            },
            "volume": calc["volume"].muscle_groups,
            "lifts": {k: v.estimated_1rm for k, v in calc["lifts"].items()},
            "goal_override": calc["goal_validation"].override,
            "goal_override_reason": calc["goal_validation"].override_reason,
        }

        nt_result = await db.execute(select(NutritionTarget).where(NutritionTarget.user_id == profile.user_id))
        nt = nt_result.scalar_one_or_none()
        if not nt:
            nt = NutritionTarget(user_id=profile.user_id)
            db.add(nt)
        nt.calories = int(calc["energy"].target_kcal)
        nt.protein_g = int(calc["energy"].protein_g)
        nt.fat_g = int(calc["energy"].fat_g)
        nt.carbs_g = int(calc["energy"].carbs_g)
        return True
    except Exception:
        logger.error(
            "Calculator pipeline failed for user %s; profile saved WITHOUT macros/nutrition targets",
            profile.user_id, exc_info=True,
        )
        return False


@router.get("", response_model=ProfileOut)
async def get_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Още нямаш профил - попълни настройката, за да продължим.")
    return profile


@router.put("", response_model=ProfileOut)
async def update_profile(
    data: ProfileCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    # model_dump() converts nested LiftEntry models into plain dicts; reaching into
    # data.lifts instead would hand the calculators Pydantic objects.
    if data.bodyweight_kg and data.body_fat_pct and data.activity_level:
        await _apply_calculators(db, profile, data.model_dump())

    await db.commit()
    await db.refresh(profile)
    return profile


@router.post("/recalculate", response_model=ProfileOut)
async def recalculate(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Re-run the calculators from the stored profile.

    Needed when the numbers are missing or stale - e.g. after a body-fat assessment
    updates the profile, or when an earlier save failed to compute them.
    """
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Още нямаш профил - попълни настройката, за да продължим.")
    if not (profile.bodyweight_kg and profile.activity_level and profile.goal):
        raise HTTPException(400, "Профилът е непълен - довърши настройката, за да изчислим макросите.")

    source = {c.name: getattr(profile, c.name) for c in UserProfile.__table__.columns}
    if not await _apply_calculators(db, profile, source):
        raise HTTPException(500, "Изчисленията не успяха. Провери данните в профила си.")

    await db.commit()
    await db.refresh(profile)
    return profile


@router.get("/nutrition-targets", response_model=NutritionTargetOut)
async def get_nutrition_targets(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(NutritionTarget).where(NutritionTarget.user_id == user.id))
    nt = result.scalar_one_or_none()
    if not nt:
        raise HTTPException(404, "Още нямаш изчислени хранителни цели - попълни профила си.")
    return nt
