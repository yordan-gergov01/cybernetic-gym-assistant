"""RAG orchestration: rewrite -> dual vector retrieval -> rerank -> format.

The single entry point for grounded course context, shared by chat, program
generation and fatigue explanations. Each stage lives in its own module
(components/retriever, components/reranker, services/query_rewriter); this file only
sequences them and merges results.

Every stage degrades gracefully and loudly: a missing index,
a failed embedding or an unavailable reranker logs a warning and falls back rather
than failing the user's request.
"""
from __future__ import annotations

import logging

from app.components.reranker import rerank
from app.components.retriever import RetrievedChunk, embed, load_index, search
from app.core.config import settings
from app.services.query_rewriter import rewrite_query

logger = logging.getLogger(__name__)

__all__ = ["RetrievedChunk", "retrieve", "retrieve_context"]


async def retrieve(
    query: str,
    *,
    top_n: int | None = None,
    candidates: int | None = None,
    filters: dict | None = None,
    rewrite: bool = True,
) -> list[RetrievedChunk]:
    """Return the top-N most relevant course chunks for `query`."""
    try:
        index, meta = load_index()
    except Exception:
        logger.warning("FAISS index/metadata unavailable; retrieving no context", exc_info=True)
        return []
    if not meta:
        return []

    top_n = top_n or settings.RERANKING_TOP_N
    candidates = candidates or settings.RETRIEVAL_CANDIDATES

    queries = [query]
    if rewrite:
        rewritten = await rewrite_query(query)
        if rewritten and rewritten.lower() != query.lower():
            queries.append(rewritten)

    # Dual retrieval: merge hits from every query variant, keeping the best similarity
    # per chunk (dedup by chunk_id).
    merged: dict[str, tuple[float, dict]] = {}
    for q in queries:
        try:
            emb = await embed(q)
        except Exception:
            logger.warning("Embedding failed for a query variant; skipping it", exc_info=True)
            continue
        for sim, m in search(emb, index, meta, candidates, filters):
            cid = m.get("chunk_id") or str(id(m))
            if cid not in merged or sim > merged[cid][0]:
                merged[cid] = (sim, m)
    if not merged:
        return []

    pool = sorted(merged.values(), key=lambda x: x[0], reverse=True)[:candidates]
    ranked = await rerank(query, pool)

    return [
        RetrievedChunk(text=m["text"], source=m.get("source", ""), score=float(score), metadata=m)
        for score, m in ranked[:top_n]
    ]


async def retrieve_context(
    query: str,
    *,
    top_n: int | None = None,
    candidates: int | None = None,
    filters: dict | None = None,
) -> str:
    """Retrieve and format chunks as one string with source tags for citation.

    Returns "" when nothing relevant is found, so callers can tell the model there is
    no course context rather than letting it answer ungrounded.
    """
    chunks = await retrieve(query, top_n=top_n, candidates=candidates, filters=filters)
    if not chunks:
        return ""
    return "\n\n".join(f"[Източник: {c.source}]\n{c.text}" for c in chunks)
