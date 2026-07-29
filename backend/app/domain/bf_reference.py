"""Body-fat visual reference rubric, derived from the Henselmans PTC guide.

The guide pairs DXA-verified body-fat percentages with descriptions of the visual
markers at that level ("striated glutes", "start of ab definition", ...). We parse
those captions into a compact rubric and give it to the vision model, so an estimate
is anchored to the course's own calibrated examples rather than the model's general
impression of what "lean" looks like.

The guide itself is copyrighted course material and lives in git-ignored data/, so the
rubric is built at runtime from the extracted JSON and cached in memory.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from functools import lru_cache

from app.core.config import settings

logger = logging.getLogger(__name__)

_GUIDE_FILE = "pdf_extracted/Body_fat_percentage_visual_reference_guide_PTC.json"

# Caption headings look like "6.2% (DXA): Alberto Nuñez" or "6.3 - 16.7% (DXA)".
_PCT_RE = re.compile(r"(\d{1,2}(?:\.\d)?)\s*%")
_SECTION_RE = re.compile(r"^\s*(Men|Women)\s*$", re.M)


@dataclass(frozen=True)
class ReferencePoint:
    bf_pct: float
    sex: str          # "male" | "female" | "unknown"
    markers: str      # visual markers described in the guide


def _clean(text: str) -> str:
    """Drop the leading page number and collapse whitespace."""
    body = re.sub(r"^\s*\d+\s*\n", "", text or "")
    return re.sub(r"\s+", " ", body).strip()


@lru_cache(maxsize=1)
def load_reference_points() -> tuple[ReferencePoint, ...]:
    """Parse (bf%, sex, visual markers) triples out of the extracted guide."""
    path = settings.backend_root / "data" / "processed" / _GUIDE_FILE
    try:
        pages = json.loads(path.read_text(encoding="utf-8"))["pages"]
    except Exception:
        logger.warning("BF visual reference guide unavailable at %s; assessment will run unanchored",
                       path, exc_info=True)
        return ()

    points: list[ReferencePoint] = []
    sex = "unknown"
    for page in pages:
        raw = page.get("text") or ""
        section = _SECTION_RE.search(raw)
        if section:
            sex = "male" if section.group(1) == "Men" else "female"
        body = _clean(raw)
        if not body or len(body) < 25:
            continue
        # Take the percentages from the page HEADINGS (the labelled examples), not from
        # the prose — a caption may mention other figures in passing ("below ~5%"), and
        # attaching those to this page's markers would misdescribe them.
        heading_text = " ".join(page.get("headings") or [])
        pcts = [float(p) for p in _PCT_RE.findall(heading_text) if 2.0 <= float(p) <= 60.0]
        if not pcts:
            first = _PCT_RE.search(body)
            pcts = [float(first.group(1))] if first and 2.0 <= float(first.group(1)) <= 60.0 else []
        if not pcts:
            continue
        markers = body if len(body) <= 400 else body[:400] + "…"
        for pct in dict.fromkeys(pcts):
            points.append(ReferencePoint(bf_pct=pct, sex=sex, markers=markers))
    return tuple(points)


def build_rubric(sex: str | None = None, max_points: int = 24) -> str:
    """Render the rubric for the prompt, preferring points matching the user's sex."""
    points = load_reference_points()
    if not points:
        return ""
    wanted = sex if sex in ("male", "female") else None
    selected = [p for p in points if p.sex == wanted] if wanted else list(points)
    if not selected:
        selected = list(points)

    # One entry per distinct percentage, ascending, so the rubric spans the range.
    by_pct: dict[float, ReferencePoint] = {}
    for p in selected:
        by_pct.setdefault(p.bf_pct, p)
    ordered = [by_pct[k] for k in sorted(by_pct)]
    if len(ordered) > max_points:
        step = len(ordered) / max_points
        ordered = [ordered[int(i * step)] for i in range(max_points)]

    lines = [f"- {p.bf_pct}% ({p.sex}): {p.markers}" for p in ordered]
    return "\n".join(lines)
