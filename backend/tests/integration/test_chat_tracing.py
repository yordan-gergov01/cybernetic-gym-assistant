"""A chat answer has to leave a trace behind, and so does one that never arrived.

The database is the point here: the trace is written on its own transaction, after the
conversation is committed, so only a real session can show that the row survives - and
that a failed generation still produces one.
"""
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.components.retriever import RetrievedChunk
from app.models import AiInteraction, ChatMessage
from app.routes import chat as chat_route
from app.services.rag_pipeline import Retrieval

from .factories import make_user
from .test_routes import auth

PASSAGE = RetrievedChunk(
    text="Protein intake stays high while dieting.",
    source="Protein PTC 2022.pdf",
    score=0.66,
    metadata={"chunk_id": "Protein PTC 2022__00115", "merged_chunk_ids": [
        "Protein PTC 2022__00115", "Protein PTC 2022__00116",
    ]},
)


def _stub_retrieval(monkeypatch, resolved="protein intake for women per kg"):
    async def fake_retrieve(query, **kwargs):
        return Retrieval([PASSAGE], resolved)

    monkeypatch.setattr(chat_route, "retrieve", fake_retrieve)


def _stub_model(monkeypatch, answer="2.0-2.2 г на кг.", fail=False):
    async def fake_create(**kwargs):
        if fail:
            raise RuntimeError("upstream model timeout")
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=answer))],
            usage=SimpleNamespace(prompt_tokens=1200, completion_tokens=180),
        )

    monkeypatch.setattr(chat_route.openai_client.chat.completions, "create", fake_create)


async def test_an_answer_records_what_it_was_built_from(client, db, monkeypatch):
    user = await make_user(db)
    _stub_retrieval(monkeypatch)
    _stub_model(monkeypatch)

    answered = await client.post(
        "/api/v1/chat", json={"content": "А за жени?"}, headers=auth(user)
    )
    assert answered.status_code == 200

    trace = (await db.execute(select(AiInteraction))).scalar_one()
    assert trace.query == "А за жени?"
    assert trace.resolved_query == "protein intake for women per kg"
    assert trace.retrieved[0]["chunk_ids"] == PASSAGE.metadata["merged_chunk_ids"]
    assert trace.prompt_name == "chat_system" and trace.prompt_version
    assert (trace.input_tokens, trace.output_tokens) == (1200, 180)
    assert trace.error is None
    # The trace has to point at the answer the user was shown, or it explains nothing.
    assert trace.message_id == answered.json()["message_id"]


async def test_a_failed_generation_is_recorded_and_leaves_no_half_conversation(
    client, db, monkeypatch
):
    """The calls worth reading later are the ones that broke."""
    user = await make_user(db)
    _stub_retrieval(monkeypatch)
    _stub_model(monkeypatch, fail=True)

    # The test transport re-raises instead of rendering the 500 the app would return.
    with pytest.raises(RuntimeError):
        await client.post("/api/v1/chat", json={"content": "Колко протеин?"}, headers=auth(user))

    trace = (await db.execute(select(AiInteraction))).scalar_one()
    assert "timeout" in trace.error
    assert trace.message_id is None
    assert trace.retrieval_ms is not None, "retrieval finished, so its cost is known"

    messages = (await db.execute(select(ChatMessage))).scalars().all()
    assert not messages, "nothing was answered, so nothing belongs in the history"
