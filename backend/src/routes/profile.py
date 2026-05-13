from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from deps import get_current_user
from models import NutritionTarget, User, UserProfile
from schemas import NutritionTargetOut, ProfileCreate, ProfileOut
from services.calculators import run_all_calculators

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileOut)
async def get_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Profile not found")
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

    if data.bodyweight_kg and data.body_fat_pct and data.activity_level:
        try:
            user_dict = data.model_dump()
            user_dict["body_fat_pct"] = data.body_fat_pct or 20.0
            user_dict["lifts"] = {
                k: {"weight": v["weight"], "reps": v["reps"]} for k, v in (data.lifts or {}).items()
            }
            calc = run_all_calculators(user_dict)
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
            nt_result = await db.execute(select(NutritionTarget).where(NutritionTarget.user_id == user.id))
            nt = nt_result.scalar_one_or_none()
            if not nt:
                nt = NutritionTarget(user_id=user.id)
                db.add(nt)
            nt.calories = int(calc["energy"].target_kcal)
            nt.protein_g = int(calc["energy"].protein_g)
            nt.fat_g = int(calc["energy"].fat_g)
            nt.carbs_g = int(calc["energy"].carbs_g)
        except Exception:
            pass

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
        raise HTTPException(404, "No nutrition targets set. Complete your profile first.")
    return nt
