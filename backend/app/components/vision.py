"""Gemini vision component.

Thin wrapper over the Google GenAI SDK for image+text prompts returning JSON. The
client is created lazily so the app boots without a Gemini key; callers get a clear
error instead of a crash at import time.
"""
from __future__ import annotations

import asyncio
import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

_client = None


class VisionUnavailable(RuntimeError):
    pass


def _get_client():
    global _client
    if not settings.GEMINI_API_KEY:
        raise VisionUnavailable("GEMINI_API_KEY is not set.")
    if _client is None:
        try:
            from google import genai

            _client = genai.Client(api_key=settings.GEMINI_API_KEY)
        except ImportError as e:
            raise VisionUnavailable("google-genai is not installed.") from e
    return _client


def _generate(images: list[tuple[bytes, str]], prompt: str, model: str) -> str:
    from google.genai import types

    parts = [types.Part.from_bytes(data=data, mime_type=mime) for data, mime in images]
    parts.append(prompt)
    resp = _get_client().models.generate_content(
        model=model,
        contents=parts,
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.2),
    )
    return resp.text or ""


async def analyze_images_json(images: list[tuple[bytes, str]], prompt: str, model: str | None = None) -> dict:
    """Send images + prompt to the vision model and parse the JSON response.

    `images` is a list of (bytes, mime_type). Raises VisionUnavailable when the model
    cannot be reached, and ValueError when the reply is not usable JSON.
    """
    model = model or settings.GEMINI_VISION_MODEL
    if not images:
        raise ValueError("No images supplied for analysis")
    raw = await asyncio.to_thread(_generate, images, prompt, model)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning("Vision model returned non-JSON output (%s): %.200s", model, raw)
        raise ValueError("Vision model did not return valid JSON") from e
