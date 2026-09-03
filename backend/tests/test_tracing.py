"""What a trace records about a retrieval, and what it deliberately leaves out."""
from app.components.retriever import RetrievedChunk
from app.services.tracing import summarize_chunks


def _chunk(chunk_id: str, text: str = "course text", **extra) -> RetrievedChunk:
    return RetrievedChunk(
        text=text, source="Protein PTC 2022.pdf", score=0.6123456,
        metadata={"chunk_id": chunk_id, "text": text, **extra},
    )


def test_a_trace_names_every_chunk_behind_a_fused_passage():
    """A span is several chunks joined; recording only the first would point a later
    reader at a third of the text the model saw."""
    ids = ["Protein PTC 2022__00007", "Protein PTC 2022__00008"]

    recorded = summarize_chunks([_chunk(ids[0], merged_chunk_ids=ids)])

    assert recorded[0]["chunk_ids"] == ids


def test_a_single_chunk_is_recorded_as_a_one_element_run():
    recorded = summarize_chunks([_chunk("Protein PTC 2022__00007")])

    assert recorded[0]["chunk_ids"] == ["Protein PTC 2022__00007"]
    assert recorded[0]["source"] == "Protein PTC 2022.pdf"


def test_the_course_text_itself_is_never_written_into_a_trace():
    """The ids rebuild the context from the index; copying the passages would put
    licensed course material into the application database."""
    recorded = summarize_chunks([_chunk("Protein PTC 2022__00007", text="a licensed paragraph")])

    assert "a licensed paragraph" not in str(recorded)
    assert set(recorded[0]) == {"chunk_ids", "source", "score"}
