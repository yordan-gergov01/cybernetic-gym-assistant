"""Tests for the retrieval pipeline: the relevance floor and history-aware rewriting.

FAISS, the embedding API and the rewriter are replaced with stubs — what is under test
is what the pipeline does with their results: which chunks it is willing to call course
context, and which query the rest of the pipeline sees for a follow-up question.
"""
from app.core.config import settings
from app.services import rag_pipeline
from app.services.query_rewriter import _HISTORY_TURNS, format_history

FLOOR = settings.RETRIEVAL_MIN_SCORE


def _chunk(chunk_id: str, text: str = "course text") -> dict:
    return {"chunk_id": chunk_id, "text": text, "source": "Protein PTC 2022.pdf"}


def _install(monkeypatch, *, hits_per_query, rewritten="protein intake per kg"):
    """Stub out the index, the embedder, the rewriter and the reranker.

    `hits_per_query` is one list of (similarity, chunk) per query variant, in call order.
    Returns a dict that records what the rewriter and the reranker were called with.
    """
    calls: dict = {}
    remaining = list(hits_per_query)

    async def fake_rewrite(question, history=None):
        calls["rewrite"] = {"question": question, "history": history}
        return rewritten

    async def fake_embed(q):
        calls.setdefault("embedded", []).append(q)
        return q

    async def fake_rerank(query, pool):
        calls["rerank_query"] = query
        return pool

    monkeypatch.setattr(rag_pipeline, "load_index", lambda: ("index", [_chunk("seed")]))
    monkeypatch.setattr(rag_pipeline, "rewrite_query", fake_rewrite)
    monkeypatch.setattr(rag_pipeline, "embed", fake_embed)
    monkeypatch.setattr(rag_pipeline, "rerank", fake_rerank)
    monkeypatch.setattr(
        rag_pipeline, "search",
        lambda emb, index, meta, candidates, filters: remaining.pop(0) if remaining else [],
    )
    return calls


async def test_a_question_the_course_does_not_cover_returns_no_context(monkeypatch):
    """Every hit is below the floor, so the honest answer is "no course context" rather
    than the nearest unrelated page."""
    off_topic = [(FLOOR - 0.1, _chunk("c1")), (FLOOR - 0.25, _chunk("c2"))]
    assert all(sim < FLOOR for sim, _ in off_topic)  # precondition
    _install(monkeypatch, hits_per_query=[off_topic, off_topic])

    assert await rag_pipeline.retrieve("коя е столицата на Австралия?") == []
    assert await rag_pipeline.retrieve_context("коя е столицата на Австралия?") == ""


async def test_only_the_chunks_above_the_floor_are_kept(monkeypatch):
    mixed = [
        (FLOOR + 0.2, _chunk("relevant")),
        (FLOOR + 0.01, _chunk("borderline")),
        (FLOOR - 0.01, _chunk("noise")),
    ]
    _install(monkeypatch, hits_per_query=[mixed, []])

    chunks = await rag_pipeline.retrieve("колко протеин на килограм?", top_n=10)

    assert [c.metadata["chunk_id"] for c in chunks] == ["relevant", "borderline"]


async def test_a_chunk_found_by_both_query_variants_keeps_its_best_similarity(monkeypatch):
    """The rewritten query is a second shot at the same corpus; a chunk that both find
    should be ranked by whichever variant matched it better, not by the last one seen."""
    _install(
        monkeypatch,
        hits_per_query=[
            [(FLOOR + 0.05, _chunk("shared"))],
            [(FLOOR + 0.30, _chunk("shared"))],
        ],
    )

    chunks = await rag_pipeline.retrieve("колко протеин?")

    assert len(chunks) == 1
    assert chunks[0].score == FLOOR + 0.30


async def test_a_follow_up_question_is_resolved_against_the_conversation(monkeypatch):
    """The subject of "а за жени?" lives in the previous turn, so both the rewriter and
    the reranker must see the conversation, not just the fragment."""
    calls = _install(
        monkeypatch,
        hits_per_query=[[(FLOOR + 0.1, _chunk("c1"))], [(FLOOR + 0.1, _chunk("c2"))]],
        rewritten="protein intake for women per kg bodyweight",
    )
    history = [
        {"role": "user", "content": "Колко протеин на килограм?"},
        {"role": "assistant", "content": "2.0-2.2 г на кг чиста телесна маса."},
    ]

    await rag_pipeline.retrieve("а за жени?", history=history)

    assert calls["rewrite"]["history"] == history
    assert "а за жени?" in calls["embedded"]
    assert "protein intake for women per kg bodyweight" in calls["embedded"]
    assert calls["rerank_query"] == "protein intake for women per kg bodyweight"


def test_history_transcript_keeps_only_the_recent_turns():
    history = [{"role": "user", "content": f"turn {i}"} for i in range(_HISTORY_TURNS + 3)]

    transcript = format_history(history)

    assert "turn 0" not in transcript
    assert f"turn {_HISTORY_TURNS + 2}" in transcript
    assert len(transcript.splitlines()) == _HISTORY_TURNS


def test_history_transcript_skips_empty_messages():
    transcript = format_history([{"role": "user", "content": "   "}, {"role": "assistant", "content": "ok"}])

    assert transcript == "assistant: ok"


def test_no_history_means_no_transcript():
    assert format_history(None) == ""
    assert format_history([]) == ""
