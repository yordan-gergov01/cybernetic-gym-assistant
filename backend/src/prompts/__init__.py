"""Versioned prompt package. Import prompts via `from prompts.registry import get_prompt`."""
from prompts.registry import active_version, get_prompt

__all__ = ["get_prompt", "active_version"]
