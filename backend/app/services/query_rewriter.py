"""Bulgarian -> English query rewriting for retrieval.

Searching with an English paraphrase in addition to the original question measurably
lifts context recall (0.47 -> 0.54 on the golden dataset), so this runs on every
retrieval by default. When chat history is supplied, the paraphrase is also resolved
against it: a follow-up question then retrieves on its actual subject instead of on a
pronoun.
"""
from __future__ import annotations

import logging

from app.core.config import settings
from app.core.llm import openai_client
from app.prompts.registry import get_prompt

logger = logging.getLogger(__name__)

# Enough turns to resolve a pronoun, few enough that an older topic cannot hijack a
# genuinely new question (and that the rewrite call stays cheap).
_HISTORY_TURNS = 4
_HISTORY_CHARS = 400


def format_history(history: list[dict] | None) -> str:
    """Render the last few turns as a plain transcript for the rewrite prompt."""
    if not history:
        return ""
    lines = []
    for msg in history[-_HISTORY_TURNS:]:
        content = (msg.get("content") or "").strip()
        if not content:
            continue
        lines.append(f"{msg.get('role') or 'user'}: {content[:_HISTORY_CHARS]}")
    return "\n".join(lines)


async def rewrite_query(question: str, history: list[dict] | None = None) -> str | None:
    """Return a short, self-contained English search query, or None if disabled or on failure."""
    if not settings.QUERY_REWRITE_ENABLED:
        return None
    try:
        prompt = get_prompt("rag_query_rewrite")(question, format_history(history))
        resp = await openai_client.chat.completions.create(
            model=settings.PRIMARY_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=40,
        )
        text = (resp.choices[0].message.content or "").strip().strip('"')
        return text or None
    except Exception:
        logger.warning("Query rewrite failed; using the original query only", exc_info=True)
        return None
