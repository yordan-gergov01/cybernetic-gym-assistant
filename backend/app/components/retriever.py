"""Vector retrieval component: FAISS index access, embeddings and metadata filtering.

Owns the index/metadata cache (loaded once per process) and knows nothing about
prompts, rewriting or reranking — those live one layer up in services/rag_pipeline.py.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass

import faiss
import numpy as np

from app.core.config import settings
from app.core.llm import openai_client

logger = logging.getLogger(__name__)

_index = None
_meta: list | None = None


@dataclass
class RetrievedChunk:
    text: str
    source: str
    score: float
    metadata: dict


def load_index():
    """Return (index, metadata), loading and caching them on first use."""
    global _index, _meta
    if _index is None:
        _index = faiss.read_index(str(settings.faiss_index_path))
        _meta = json.loads(settings.faiss_metadata_path.read_text(encoding="utf-8"))
        logger.info("Loaded FAISS index (%d vectors) and %d metadata chunks", _index.ntotal, len(_meta))
    return _index, _meta


def passes_filters(m: dict, filters: dict | None) -> bool:
    """A chunk passes if, for each filter key, its value matches the requested value
    or either side is 'all' (course chunks tagged as universally applicable)."""
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


async def embed(query: str) -> np.ndarray:
    resp = await openai_client.embeddings.create(model=settings.EMBEDDING_MODEL, input=[query])
    emb = np.array(resp.data[0].embedding, dtype="float32").reshape(1, -1)
    faiss.normalize_L2(emb)
    return emb


def search(emb: np.ndarray, index, meta: list, candidates: int, filters: dict | None) -> list[tuple[float, dict]]:
    """Vector search returning [(similarity, chunk_metadata)] passing the filters."""
    k = min(candidates, len(meta))
    sims, ids = index.search(emb, k)
    out: list[tuple[float, dict]] = []
    for sim, i in zip(sims[0], ids[0]):
        if i == -1 or i >= len(meta):
            continue
        m = meta[i]
        if passes_filters(m, filters):
            out.append((float(sim), m))
    return out
