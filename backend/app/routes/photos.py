import asyncio
import logging
import uuid
from datetime import date as date_type

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.vision import VisionUnavailable
from app.db.database import get_db
from app.deps import get_current_user
from app.models import User, UserPhoto, UserProfile
from app.schemas import BFAssessmentOut, BFAssessRequest, UserPhotoOut
from app.services import storage
from app.services.bf_assessment import assess_from_r2_keys
from app.services.storage import StorageNotConfigured

router = APIRouter(prefix="/photos", tags=["photos"])
logger = logging.getLogger(__name__)

_ALLOWED_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
_MAX_BYTES = 15 * 1024 * 1024  # 15 MB


def _safe_presign(key: str | None) -> str | None:
    if not key:
        return None
    try:
        return storage.presigned_url(key)
    except Exception:
        logger.warning("Could not presign object %s", key, exc_info=True)
        return None


def _to_out(photo: UserPhoto) -> UserPhotoOut:
    out = UserPhotoOut.model_validate(photo)
    out.url = _safe_presign(photo.file_path)
    return out


@router.post("", response_model=UserPhotoOut, status_code=201)
async def upload_photo(
    file: UploadFile = File(...),
    taken_at: date_type = Form(...),
    photo_type: str = Form("progress"),
    angle: str | None = Form(None),
    notes: str | None = Form(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ext = _ALLOWED_TYPES.get(file.content_type)
    if not ext:
        raise HTTPException(400, "Unsupported image type; use JPEG, PNG or WebP")
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file")
    if len(data) > _MAX_BYTES:
        raise HTTPException(413, "Image too large (max 15 MB)")

    key = f"users/{user.id}/photos/{uuid.uuid4()}.{ext}"
    try:
        await asyncio.to_thread(storage.upload_bytes, data, key, file.content_type)
    except StorageNotConfigured as e:
        raise HTTPException(503, f"Photo storage unavailable: {e}")

    photo = UserPhoto(
        user_id=user.id, photo_type=photo_type, angle=angle,
        file_path=key, taken_at=taken_at, notes=notes,
    )
    db.add(photo)
    await db.commit()
    await db.refresh(photo)
    return _to_out(photo)


@router.get("", response_model=list[UserPhotoOut])
async def list_photos(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    r = await db.execute(
        select(UserPhoto).where(UserPhoto.user_id == user.id).order_by(UserPhoto.taken_at.desc())
    )
    return [_to_out(p) for p in r.scalars().all()]


@router.post("/assess-bf", response_model=BFAssessmentOut)
async def assess_body_fat(
    data: BFAssessRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Estimate body-fat % from stored photos, anchored to the course's visual rubric.

    Front/back/side photos of the same session should be assessed together — more angles
    means a better read. The estimate is written onto the photo rows; it is only applied
    to the profile when the caller asks AND confidence is not low, because the profile
    value drives the deterministic macro calculations.
    """
    r = await db.execute(
        select(UserPhoto).where(UserPhoto.id.in_(data.photo_ids), UserPhoto.user_id == user.id)
    )
    photos = r.scalars().all()
    if len(photos) != len(data.photo_ids):
        raise HTTPException(404, "One or more photos not found")
    keys = [p.file_path for p in photos if p.file_path]
    if not keys:
        raise HTTPException(400, "Selected photos have no stored image")

    pr = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = pr.scalar_one_or_none()

    # An unanchored rubric mixes the male and female reference points, so the caller's
    # answer stands in while the profile is still being filled in (onboarding).
    sex = (profile.sex if profile else None) or data.sex

    try:
        result = await assess_from_r2_keys(
            keys, sex=sex, angles=[p.angle for p in photos if p.angle]
        )
    except (StorageNotConfigured, VisionUnavailable) as e:
        raise HTTPException(503, f"Body-fat assessment unavailable: {e}")
    except ValueError as e:
        raise HTTPException(502, f"Vision model returned an unusable result: {e}")

    for p in photos:
        p.bf_pct_assessed = result.bf_pct

    applied = False
    if data.apply_to_profile and profile:
        if result.confidence == "low":
            logger.info("Not applying low-confidence BF estimate %.1f%% to user %s", result.bf_pct, user.id)
        else:
            profile.body_fat_pct = result.bf_pct
            profile.bf_assessment_method = f"visual ({result.model}, {result.confidence})"
            applied = True
    await db.commit()

    return BFAssessmentOut(**vars(result), applied_to_profile=applied)


@router.delete("/{photo_id}", status_code=204)
async def delete_photo(photo_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(UserPhoto).where(UserPhoto.id == photo_id, UserPhoto.user_id == user.id))
    photo = r.scalar_one_or_none()
    if not photo:
        raise HTTPException(404, "Photo not found")
    if photo.file_path:
        try:
            await asyncio.to_thread(storage.delete_object, photo.file_path)
        except Exception:
            logger.warning("Failed to delete R2 object %s; removing DB row anyway", photo.file_path, exc_info=True)
    await db.delete(photo)
    await db.commit()
