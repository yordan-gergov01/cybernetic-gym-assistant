"""Tests for the retrieval pipeline: the relevance floor and history-aware rewriting.

FAISS, the embedding API and the rewriter are replaced with stubs — what is under test
is what the pipeline does with their results: which chunks it is willing to call course
context, and which query the rest of the pipeline sees for a follow-up question.
"""
from app.components.retriever import _MIN_OVERLAP, chunk_position, join_overlapping, merge_adjacent
from app.core.config import settings
from app.services import rag_pipeline
from app.services.query_rewriter import _HISTORY_TURNS, format_history

FLOOR = settings.RETRIEVAL_MIN_SCORE


def _chunk(chunk_id: str, text: str = "course text") -> dict:
    source = chunk_position(chunk_id)
    return {"chunk_id": chunk_id, "text": text, "source": f"{source[0]}.pdf" if source else chunk_id}


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

    assert (await rag_pipeline.retrieve("коя е столицата на Австралия?")).chunks == []
    assert await rag_pipeline.retrieve_context("коя е столицата на Австралия?") == ""


async def test_only_the_chunks_above_the_floor_are_kept(monkeypatch):
    mixed = [
        (FLOOR + 0.2, _chunk("relevant")),
        (FLOOR + 0.01, _chunk("borderline")),
        (FLOOR - 0.01, _chunk("noise")),
    ]
    _install(monkeypatch, hits_per_query=[mixed, []])

    chunks = (await rag_pipeline.retrieve("колко протеин на килограм?", top_n=10)).chunks

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

    chunks = (await rag_pipeline.retrieve("колко протеин?")).chunks

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


# SPAN MERGING


def test_neighbouring_chunks_come_back_as_one_passage():
    """Two chunks that follow one another in the document are one passage, not two
    entries competing for the same context budget."""
    tail = "protein intake stays high while dieting, "  # the part the cut repeats
    spans = merge_adjacent([
        (0.6, _chunk("Protein PTC 2022__00007", "Because muscle is lost first, " + tail)),
        (0.5, _chunk("Protein PTC 2022__00008", tail + "up to 2.4 g per kg.")),
    ])

    assert len(spans) == 1
    assert spans[0][1]["text"] == "Because muscle is lost first, " + tail + "up to 2.4 g per kg."
    assert spans[0][1]["merged_chunk_ids"] == ["Protein PTC 2022__00007", "Protein PTC 2022__00008"]


def test_a_fused_passage_keeps_the_best_score_of_its_parts():
    """Merging must never push a passage below a weaker one it was fused with."""
    spans = merge_adjacent([
        (FLOOR + 0.30, _chunk("Energy PTC 2022__00002", "strong ")),
        (FLOOR + 0.01, _chunk("Energy PTC 2022__00003", "weak")),
        (FLOOR + 0.20, _chunk("Volume PTC 2022__00010", "other document")),
    ])

    assert [round(score, 4) for score, _ in spans] == [round(FLOOR + 0.30, 4), round(FLOOR + 0.20, 4)]


def test_chunks_from_different_documents_are_never_fused():
    spans = merge_adjacent([
        (0.6, _chunk("Protein PTC 2022__00007")),
        (0.5, _chunk("Energy PTC 2022__00008")),
    ])

    assert len(spans) == 2


def test_a_gap_in_the_numbering_ends_the_passage():
    """00007 and 00009 are not neighbours - the chunk between them was not retrieved, so
    joining them would invent a continuity the document does not have."""
    spans = merge_adjacent([
        (0.6, _chunk("Protein PTC 2022__00007", "first")),
        (0.5, _chunk("Protein PTC 2022__00009", "third")),
    ])

    assert len(spans) == 2


def test_a_chunk_without_an_ordinal_is_returned_untouched():
    """The calculator chunks are not part of any document sequence."""
    spans = merge_adjacent([(0.6, _chunk("calculator__one_rep_max__description", "1RM tool"))])

    assert len(spans) == 1
    assert "merged_chunk_ids" not in spans[0][1]


def test_the_text_two_chunks_share_is_written_once():
    shared = "the overlap that both chunks carry, long enough to be no coincidence"

    joined = join_overlapping("opening sentence. " + shared, shared + " closing sentence.")

    assert joined.count(shared) == 1
    assert joined == "opening sentence. " + shared + " closing sentence."


async def test_fusing_neighbours_frees_the_slot_for_another_document(monkeypatch):
    """Merging two neighbours must not shrink the answer to one passage: the freed slot
    goes to the next candidate, so the same budget carries more of the course."""
    shared = "and the overlap the chunker repeated in both "
    _install(monkeypatch, hits_per_query=[[
        (FLOOR + 0.20, _chunk("Protein PTC 2022__00007", "first half " + shared)),
        (FLOOR + 0.15, _chunk("Protein PTC 2022__00008", shared + "second half")),
        (FLOOR + 0.10, _chunk("Energy PTC 2022__00003", "another document")),
    ], []])

    chunks = (await rag_pipeline.retrieve("колко протеин?", top_n=2)).chunks

    assert [c.source for c in chunks] == ["Protein PTC 2022.pdf", "Energy PTC 2022.pdf"]
    assert chunks[0].text == "first half " + shared + "second half"


def test_a_short_coincidental_match_is_not_treated_as_an_overlap():
    """A few characters in common are chance, not the chunker's repeated tail; joining on
    them would silently delete the start of the second chunk."""
    coincidence = "e " * 8  # shorter than the minimum overlap
    assert len(coincidence) < _MIN_OVERLAP  # precondition

    joined = join_overlapping("first chunk ends with " + coincidence, coincidence + "second chunk")

    assert joined.count("second chunk") == 1
    assert joined.count(coincidence) == 2
