"""Vector retrieval component: FAISS index access, embeddings and metadata filtering.

Owns the index/metadata cache (loaded once per process) and knows nothing about
prompts, rewriting or reranking - those live one layer up in services/rag_pipeline.py.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

import faiss
import numpy as np

from app.core.config import settings
from app.core.llm import openai_client

logger = logging.getLogger(__name__)

_index = None
_meta: list | None = None

# Chunk ids are "<source document>__<00042>", numbered in reading order, so a chunk's
# neighbour in the document is one step away in this number. Four calculator chunks are
# named differently and simply never have a neighbour.
_CHUNK_ID = re.compile(r"^(.*)__(\d+)$")

# Consecutive chunks were cut with CHUNK_OVERLAP, so each one repeats the tail of the
# previous - a median of 300 characters. These bound the search for that repeated part:
# below the minimum a match is coincidence, above the maximum it is not an overlap.
_MIN_OVERLAP = 30
_MAX_OVERLAP = 600


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


def chunk_position(chunk_id: str) -> tuple[str, int] | None:
    """Return (source document, ordinal) for a chunk id, or None if it is not numbered."""
    m = _CHUNK_ID.match(chunk_id or "")
    return (m.group(1), int(m.group(2))) if m else None


def join_overlapping(first: str, second: str) -> str:
    """Concatenate two consecutive chunks without repeating the part they share."""
    limit = min(len(first), len(second), _MAX_OVERLAP)
    for size in range(limit, _MIN_OVERLAP, -1):
        if first[-size:] == second[:size]:
            return first + second[size:]
    return first + "\n" + second


def merge_adjacent(items: list[tuple[float, dict]]) -> list[tuple[float, dict]]:
    """Fuse chunks that are consecutive in the same document into one continuous span.

    Retrieval regularly returns neighbouring chunks for the same question; handing the
    model both means handing it the overlap twice and spending a context slot on text it
    already has. A span keeps the best score of its parts, so merging never promotes a
    weaker passage above a stronger one.
    """
    ordered: dict[str, dict[int, tuple[float, dict]]] = {}
    loose: list[tuple[float, dict]] = []
    for score, m in items:
        pos = chunk_position(m.get("chunk_id", ""))
        if pos is None:
            loose.append((score, m))
            continue
        source, ordinal = pos
        ordered.setdefault(source, {})[ordinal] = (score, m)

    spans: list[tuple[float, dict]] = list(loose)
    for by_ordinal in ordered.values():
        run: list[int] = []
        for ordinal in sorted(by_ordinal) + [None]:
            if run and ordinal == run[-1] + 1:
                run.append(ordinal)
                continue
            if run:
                spans.append(_span([by_ordinal[o] for o in run]))
            run = [ordinal] if ordinal is not None else []
    return sorted(spans, key=lambda x: x[0], reverse=True)


def _span(run: list[tuple[float, dict]]) -> tuple[float, dict]:
    """Collapse one run of consecutive chunks into a single (score, chunk)."""
    if len(run) == 1:
        return run[0]
    text = run[0][1]["text"]
    for _, m in run[1:]:
        text = join_overlapping(text, m["text"])
    merged = {**run[0][1], "text": text, "merged_chunk_ids": [m["chunk_id"] for _, m in run]}
    return max(score for score, _ in run), merged


async def embed_many(queries: list[str]) -> list[np.ndarray]:
    """Embed several queries in one call, in the order they were given.

    The query variants are known at the same moment, so embedding them one at a time only
    buys an extra round trip to the API per variant. Results are ordered by the index the
    API reports rather than by arrival, which is what pairs a vector with its query.
    """
    resp = await openai_client.embeddings.create(model=settings.EMBEDDING_MODEL, input=queries)
    embeddings = []
    for item in sorted(resp.data, key=lambda d: d.index):
        emb = np.array(item.embedding, dtype="float32").reshape(1, -1)
        faiss.normalize_L2(emb)
        embeddings.append(emb)
    return embeddings


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
