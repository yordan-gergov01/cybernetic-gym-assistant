"""Body-fat percentage assessment from progress photos.

Estimating body fat by eye is a judgment call, so a vision model does it — but it is
anchored to the course's DXA-verified visual rubric (app/domain/bf_reference.py) rather
than the model's general impression, and the result always carries a range plus a
confidence so an uncertain read stays visible.

The estimate feeds `UserProfile.body_fat_pct`, which drives the deterministic
calculators (LBM → BMR → macros), so a low-confidence read must never be silently
promoted to a profile value — the caller decides.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from app.components.vision import analyze_images_json
from app.domain.bf_reference import build_rubric
from app.prompts.registry import get_prompt
from app.services import storage

logger = logging.getLogger(__name__)

_VALID_CONFIDENCE = {"high", "medium", "low"}
# Plausible human range; anything outside means the model misread the photo.
_MIN_BF, _MAX_BF = 2.0, 70.0


@dataclass
class BFAssessment:
    bf_pct: float
    range_low: float
    range_high: float
    confidence: str
    observed_markers: list[str]
    closest_reference: str
    limitations: str
    reasoning_bg: str
    model: str
    photo_count: int


def _coerce_float(value, field: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Vision model returned no usable '{field}'") from e


async def assess_from_images(
    images: list[tuple[bytes, str]],
    *,
    sex: str | None,
    angles: list[str] | None = None,
    model: str | None = None,
) -> BFAssessment:
    """Estimate BF% from raw image bytes. Raises ValueError on an unusable response."""
    from app.core.config import settings

    sex_label = sex if sex in ("male", "female") else "неуточнен"
    rubric = build_rubric(sex)
    if not rubric:
        logger.warning("BF rubric unavailable; assessment will be less calibrated")

    prompt = get_prompt("bf_assessment")(sex=sex_label, angles=angles or [], rubric=rubric)
    data = await analyze_images_json(images, prompt, model=model)

    bf = _coerce_float(data.get("bf_pct"), "bf_pct")
    if not _MIN_BF <= bf <= _MAX_BF:
        raise ValueError(f"Vision model returned an implausible body-fat value: {bf}")

    low = data.get("bf_range_low")
    high = data.get("bf_range_high")
    low = _coerce_float(low, "bf_range_low") if low is not None else bf
    high = _coerce_float(high, "bf_range_high") if high is not None else bf
    if low > high:
        low, high = high, low

    confidence = str(data.get("confidence", "")).lower()
    if confidence not in _VALID_CONFIDENCE:
        logger.warning("Vision model returned unknown confidence %r; treating as low", confidence)
        confidence = "low"

    markers = data.get("observed_markers") or []
    if not isinstance(markers, list):
        markers = [str(markers)]

    return BFAssessment(
        bf_pct=round(bf, 1),
        range_low=round(low, 1),
        range_high=round(high, 1),
        confidence=confidence,
        observed_markers=[str(m) for m in markers],
        closest_reference=str(data.get("closest_reference") or ""),
        limitations=str(data.get("limitations") or ""),
        reasoning_bg=str(data.get("reasoning_bg") or ""),
        model=model or settings.GEMINI_VISION_MODEL,
        photo_count=len(images),
    )


async def assess_from_r2_keys(
    keys: list[str],
    *,
    sex: str | None,
    angles: list[str] | None = None,
    model: str | None = None,
) -> BFAssessment:
    """Download photos from R2 by object key, then assess them together."""
    images: list[tuple[bytes, str]] = []
    for key in keys:
        data = await asyncio.to_thread(storage.download_bytes, key)
        mime = "image/png" if key.lower().endswith(".png") else (
            "image/webp" if key.lower().endswith(".webp") else "image/jpeg"
        )
        images.append((data, mime))
    return await assess_from_images(images, sex=sex, angles=angles, model=model)
