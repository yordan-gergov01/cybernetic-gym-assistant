"""Central retrieval service: FAISS vector search + cross-encoder reranking.

Single source of truth for RAG, shared by chat and program generation. The FAISS
index, metadata, embedding client and reranker are loaded once and cached at module
level. Retrieval pulls a wide candidate pool by vector similarity, then a cross-encoder
reranks it to the final top-N — this lifts context recall over pure vector search,
especially for Bulgarian queries against the English course corpus.

Everything degrades gracefully and loudly (see CLAUDE.md rule #12): if the index or
the reranker is unavailable, retrieval logs a warning and falls back rather than
crashing the request.
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass

import faiss
import numpy as np
from openai import AsyncOpenAI

from core.config import settings

logger = logging.getLogger(__name__)

_openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

_index = None
_meta: list | None = None
_reranker = None
_reranker_failed = False


@dataclass
class RetrievedChunk:
    text: str
    source: str
    score: float
    metadata: dict


def _load_index():
    global _index, _meta
    if _index is None:
        _index = faiss.read_index(str(settings.faiss_index_path))
        _meta = json.loads(settings.faiss_metadata_path.read_text(encoding="utf-8"))
        logger.info("Loaded FAISS index (%d vectors) and %d metadata chunks", _index.ntotal, len(_meta))
    return _index, _meta


def _get_reranker():
    """Lazy-load the cross-encoder reranker. Returns None (once) if unavailable."""
    global _reranker, _reranker_failed
    if not settings.RERANK_ENABLED or _reranker_failed:
        return None
    if _reranker is None:
        try:
            from FlagEmbedding import FlagReranker

            _reranker = FlagReranker(settings.RERANKER_MODEL, use_fp16=True)
            logger.info("Loaded reranker %s", settings.RERANKER_MODEL)
        except Exception:
            _reranker_failed = True
            logger.warning(
                "Reranker '%s' unavailable; falling back to vector similarity order",
                settings.RERANKER_MODEL, exc_info=True,
            )
            return None
    return _reranker


def _passes_filters(m: dict, filters: dict | None) -> bool:
    """Metadata filter. A chunk passes if, for each filter key, its value matches the
    requested value or the chunk's value is 'all' (course chunks tagged as universal)."""
    if not filters:
        return True
    for key, wanted in filters.items():
        if wanted is None:
            continue
        actual = m.get(key)
        if actual is None:
            continue
        if actual == "all" or wanted == "all":
            continue
        if actual != wanted:
            return False
    return True


async def _embed(query: str) -> np.ndarray:
    resp = await _openai.embeddings.create(model=settings.EMBEDDING_MODEL, input=[query])
    emb = np.array(resp.data[0].embedding, dtype="float32").reshape(1, -1)
    faiss.normalize_L2(emb)
    return emb


async def retrieve(
    query: str,
    *,
    top_n: int | None = None,
    candidates: int | None = None,
    filters: dict | None = None,
) -> list[RetrievedChunk]:
    """Return the top-N most relevant chunks for `query` after reranking."""
    try:
        index, meta = _load_index()
    except Exception:
        logger.warning("FAISS index/metadata unavailable; retrieving no context", exc_info=True)
        return []
    if not meta:
        return []

    top_n = top_n or settings.RERANKING_TOP_N
    candidates = candidates or settings.RETRIEVAL_CANDIDATES

    try:
        emb = await _embed(query)
    except Exception:
        logger.warning("Query embedding failed; retrieving no context", exc_info=True)
        return []

    k = min(candidates, len(meta))
    sims, ids = index.search(emb, k)
    pool: list[tuple[float, dict]] = []
    for sim, i in zip(sims[0], ids[0]):
        if i == -1 or i >= len(meta):
            continue
        m = meta[i]
        if _passes_filters(m, filters):
            pool.append((float(sim), m))
    if not pool:
        return []

    reranker = _get_reranker()
    if reranker is not None:
        try:
            pairs = [[query, m["text"]] for _, m in pool]
            scores = await asyncio.to_thread(reranker.compute_score, pairs, normalize=True)
            if not isinstance(scores, list):
                scores = [scores]
            ranked = sorted(zip(scores, (m for _, m in pool)), key=lambda x: x[0], reverse=True)
        except Exception:
            logger.warning("Reranking failed; using vector similarity order", exc_info=True)
            ranked = [(sim, m) for sim, m in pool]
    else:
        ranked = [(sim, m) for sim, m in pool]  # already sorted by FAISS similarity

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
    """Retrieve and format chunks as a single string with source tags for citation.

    Returns "" when nothing relevant is found, so callers can tell the model there is
    no course context rather than letting it answer ungrounded.
    """
    chunks = await retrieve(query, top_n=top_n, candidates=candidates, filters=filters)
    if not chunks:
        return ""
    return "\n\n".join(f"[Източник: {c.source}]\n{c.text}" for c in chunks)
