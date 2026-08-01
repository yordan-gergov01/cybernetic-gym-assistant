"""Prompt registry — the single lookup point for prompts by name and version.

Route/business code calls `get_prompt("name")(...)` and never references template
functions directly. This keeps prompt selection (which version is live) in one place.

To roll a prompt forward: add `<name>_v2` in templates.py, register it under the
same name, and switch _ACTIVE_VERSIONS to "v2". The old version stays callable via
`get_prompt("name", version="v1")` for comparison/rollback.
"""
from __future__ import annotations

from typing import Callable

from app.prompts import templates

# name -> {version: builder}
_REGISTRY: dict[str, dict[str, Callable[..., str]]] = {
    "chat_system": {"v1": templates.chat_system_v1, "v2": templates.chat_system_v2},
    "chat_language_rules": {"v1": templates.chat_language_rules_v1},
    "chat_profile_block": {"v1": templates.chat_profile_block_v1},
    "rag_query_rewrite": {"v1": templates.rag_query_rewrite_v1},
    "bf_assessment": {"v1": templates.bf_assessment_v1},
    "program_generation": {"v1": templates.program_generation_v1},
    "program_week_template": {"v2": templates.program_week_template_v2, "v3": templates.program_week_template_v3},
    "fatigue_explanation": {"v1": templates.fatigue_explanation_v1},
    "food_extraction": {"v1": templates.food_extraction_v1},
    "food_llm_estimate": {"v1": templates.food_llm_estimate_v1},
}

# Which version is live per prompt.
_ACTIVE_VERSIONS: dict[str, str] = {name: "v1" for name in _REGISTRY}
_ACTIVE_VERSIONS["chat_system"] = "v2"  # grounded/citation variant
_ACTIVE_VERSIONS["program_week_template"] = "v3"  # split + frequency decided in code, not by the model


def get_prompt(name: str, version: str | None = None) -> Callable[..., str]:
    """Return the prompt builder for `name` (active version unless overridden)."""
    try:
        versions = _REGISTRY[name]
    except KeyError:
        raise KeyError(f"Unknown prompt '{name}'. Known: {sorted(_REGISTRY)}") from None
    resolved = version or _ACTIVE_VERSIONS[name]
    try:
        return versions[resolved]
    except KeyError:
        raise KeyError(f"Prompt '{name}' has no version '{resolved}'. Available: {sorted(versions)}") from None


def active_version(name: str) -> str:
    return _ACTIVE_VERSIONS[name]
