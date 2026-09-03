"""Recording what the models were asked and what came back.

Without a trace a wrong coaching answer can only be re-read, never explained. One row
per model call carries the question, the query retrieval resolved it into, the passages
that came back, the live prompt version, and the latency and tokens the call spent.

The trace is written outside the request's own transaction on purpose. A conversation
that was answered must not be rolled back because its bookkeeping failed.
"""
from __future__ import annotations

import logging
from time import perf_counter

from sqlalchemy.ext.asyncio import AsyncSession

from app.components.retriever import RetrievedChunk
from app.models import AiInteraction

logger = logging.getLogger(__name__)


def ms_since(started: float) -> int:
    """Milliseconds elapsed since a perf_counter() reading."""
    return int((perf_counter() - started) * 1000)


def summarize_chunks(chunks: list[RetrievedChunk]) -> list[dict]:
    """Describe the retrieved passages by id and score, never by text.

    The ids rebuild the exact context from the FAISS index when a trace needs reading,
    while the course material itself stays in the index it is licensed into.
    """
    return [
        {
            "chunk_ids": c.metadata.get("merged_chunk_ids") or [c.metadata.get("chunk_id")],
            "source": c.source,
            "score": round(c.score, 4),
        }
        for c in chunks
    ]


async def record_interaction(db: AsyncSession, trace: AiInteraction) -> None:
    """Persist one trace, and never let it break the request it describes."""
    try:
        db.add(trace)
        await db.commit()
    except Exception:
        await db.rollback()
        logger.warning(
            "Could not record the %s interaction trace for user %s",
            trace.surface, trace.user_id, exc_info=True,
        )
