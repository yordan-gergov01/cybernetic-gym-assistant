"""Cross-encoder reranking component.

A cross-encoder scores (query, passage) pairs jointly and is far more accurate than
vector similarity, at the cost of a local model (~2.3 GB RAM for bge-reranker-v2-m3).
It is therefore optional: disabled by default via RERANK_ENABLED, lazily loaded, and
any failure degrades to the caller's existing order instead of breaking the request.
"""
from __future__ import annotations

import asyncio
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

_reranker = None
_load_failed = False


def get_reranker():
    """Lazy-load the cross-encoder. Returns None (and stops retrying) if unavailable."""
    global _reranker, _load_failed
    if not settings.RERANK_ENABLED or _load_failed:
        return None
    if _reranker is None:
        try:
            from FlagEmbedding import FlagReranker

            _reranker = FlagReranker(settings.RERANKER_MODEL, use_fp16=True)
            logger.info("Loaded reranker %s", settings.RERANKER_MODEL)
        except Exception:
            _load_failed = True
            logger.warning(
                "Reranker '%s' unavailable; falling back to vector similarity order",
                settings.RERANKER_MODEL, exc_info=True,
            )
            return None
    return _reranker


async def rerank(query: str, pool: list[tuple[float, dict]]) -> list[tuple[float, dict]]:
    """Rerank [(score, chunk)] for `query`. Returns `pool` unchanged when disabled or on failure."""
    reranker = get_reranker()
    if reranker is None or not pool:
        return pool
    try:
        pairs = [[query, m["text"]] for _, m in pool]
        scores = await asyncio.to_thread(reranker.compute_score, pairs, normalize=True)
        if not isinstance(scores, list):
            scores = [scores]
        return sorted(zip(scores, (m for _, m in pool)), key=lambda x: x[0], reverse=True)
    except Exception:
        logger.warning("Reranking failed; using vector similarity order", exc_info=True)
        return pool
