"""Bulgarian -> English query rewriting for retrieval.

The course corpus is English while the user writes Bulgarian. Searching with an
English paraphrase in addition to the original question measurably lifts context
recall (+0.09 in the offline eval), so this runs on every retrieval by default.
"""
from __future__ import annotations

import logging

from app.core.config import settings
from app.core.llm import openai_client
from app.prompts.registry import get_prompt

logger = logging.getLogger(__name__)


async def rewrite_query(question: str) -> str | None:
    """Return a short English search query, or None if disabled or on failure."""
    if not settings.QUERY_REWRITE_ENABLED:
        return None
    try:
        prompt = get_prompt("rag_query_rewrite")(question)
        resp = await openai_client.chat.completions.create(
            model=settings.PRIMARY_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=30,
        )
        text = (resp.choices[0].message.content or "").strip().strip('"')
        return text or None
    except Exception:
        logger.warning("Query rewrite failed; using the original query only", exc_info=True)
        return None
