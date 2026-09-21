"""A chat answer has to leave a trace behind, and so does one that never arrived.

The database is the point here: the trace is written on its own transaction, after the
conversation is committed, so only a real session can show that the row survives - and
that a failed generation still produces one.

The route answers over SSE, so these tests read the event stream the browser reads. The
turn is only written down on `done`; everything before that is text on a screen.
"""
import json
from types import SimpleNamespace

from sqlalchemy import select

from app.components.retriever import RetrievedChunk
from app.models import AiInteraction, ChatMessage
from app.routes import chat as chat_route
from app.services.rag_pipeline import Retrieval

from .factories import make_profile, make_program, make_user
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


def _delta(text: str) -> SimpleNamespace:
    return SimpleNamespace(usage=None, choices=[SimpleNamespace(delta=SimpleNamespace(content=text))])


def _usage(prompt_tokens=1200, completion_tokens=180) -> SimpleNamespace:
    """The last chunk of a stream: token counts and no choices at all."""
    return SimpleNamespace(
        usage=SimpleNamespace(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens),
        choices=[],
    )


def _stub_model(monkeypatch, pieces=("2.0-2.2 ", "г на кг."), fail_after=None):
    """Replace the model with a stream of `pieces`.

    `fail_after` breaks the stream once that many pieces have been sent, which is the
    case that decides whether a half-finished answer can reach the history.
    """

    async def fake_create(**kwargs):
        async def stream():
            for sent, piece in enumerate(pieces, start=1):
                if fail_after is not None and sent > fail_after:
                    raise RuntimeError("upstream model timeout")
                yield _delta(piece)
            if fail_after is not None:
                raise RuntimeError("upstream model timeout")
            yield _usage()

        return stream()

    monkeypatch.setattr(chat_route.openai_client.chat.completions, "create", fake_create)


def _events(response) -> list[tuple[str, dict]]:
    """The SSE body as [(event name, payload)], in the order it was sent."""
    out: list[tuple[str, dict]] = []
    for block in response.text.split("\n\n"):
        name, data = None, None
        for line in block.splitlines():
            if line.startswith("event: "):
                name = line[len("event: "):]
            elif line.startswith("data: "):
                data = json.loads(line[len("data: "):])
        if name:
            out.append((name, data))
    return out


async def _ask(client, user, question="Колко протеин?") -> list[tuple[str, dict]]:
    response = await client.post("/api/v1/chat", json={"content": question}, headers=auth(user))
    assert response.status_code == 200
    return _events(response)


def _text(events) -> str:
    return "".join(payload["text"] for name, payload in events if name == "delta")


def _done(events) -> dict | None:
    return next((payload for name, payload in events if name == "done"), None)


async def test_an_answer_records_what_it_was_built_from(client, db, monkeypatch):
    user = await make_user(db)
    _stub_retrieval(monkeypatch)
    _stub_model(monkeypatch)

    events = await _ask(client, user, "А за жени?")

    trace = (await db.execute(select(AiInteraction))).scalar_one()
    assert trace.query == "А за жени?"
    assert trace.resolved_query == "protein intake for women per kg"
    assert trace.retrieved[0]["chunk_ids"] == PASSAGE.metadata["merged_chunk_ids"]
    assert trace.prompt_name == "chat_system" and trace.prompt_version
    # Streaming hides usage behind a final chunk of its own; losing it would leave every
    # answer with no recorded cost.
    assert (trace.input_tokens, trace.output_tokens) == (1200, 180)
    assert trace.error is None
    # The trace has to point at the answer the user was shown, or it explains nothing.
    assert trace.message_id == _done(events)["message_id"]


async def test_the_answer_arrives_in_pieces_and_is_stored_whole(client, db, monkeypatch):
    """The point of the stream: reading starts on the first words, and what the history
    keeps afterwards is the same answer, not the fragments it arrived in."""
    user = await make_user(db)
    _stub_retrieval(monkeypatch)
    _stub_model(monkeypatch, pieces=("Протеинът ", "е ", "2.0-2.2 г на кг."))

    events = await _ask(client, user)

    assert len([1 for name, _ in events if name == "delta"]) == 3, "arrived in one piece"
    assert _text(events) == "Протеинът е 2.0-2.2 г на кг."
    stored = (await db.execute(select(ChatMessage).where(ChatMessage.role == "assistant"))).scalar_one()
    assert stored.content == _text(events)


async def test_a_failed_generation_is_recorded_and_leaves_no_half_conversation(
    client, db, monkeypatch
):
    """The calls worth reading later are the ones that broke."""
    user = await make_user(db)
    _stub_retrieval(monkeypatch)
    _stub_model(monkeypatch, fail_after=0)

    events = await _ask(client, user)

    # The stream is already open when generation fails, so the failure has to be an
    # event; there is no status code left to carry it.
    assert [name for name, _ in events] == ["error"]
    assert events[0][1]["detail"] == chat_route.GENERATION_FAILED

    trace = (await db.execute(select(AiInteraction))).scalar_one()
    assert "timeout" in trace.error
    assert trace.message_id is None
    assert trace.retrieval_ms is not None, "retrieval finished, so its cost is known"

    messages = (await db.execute(select(ChatMessage))).scalars().all()
    assert not messages, "nothing was answered, so nothing belongs in the history"


async def test_an_answer_cut_off_midway_is_not_kept(client, db, monkeypatch):
    """Half a coaching answer saved as if it were whole is worse than none: nothing in
    the history would say where it stopped."""
    user = await make_user(db)
    _stub_retrieval(monkeypatch)
    _stub_model(monkeypatch, pieces=("Трябва да ядеш ", "поне "), fail_after=1)

    events = await _ask(client, user)

    assert _text(events) == "Трябва да ядеш ", "precondition: part of the answer was sent"
    assert [name for name, _ in events][-1] == "error"
    assert not (await db.execute(select(ChatMessage))).scalars().all()


async def test_an_empty_answer_is_a_failure_not_a_message(client, db, monkeypatch):
    """A call that succeeds and says nothing would otherwise leave a blank coach bubble
    that cannot be told apart from a lost one."""
    user = await make_user(db)
    _stub_retrieval(monkeypatch)
    _stub_model(monkeypatch, pieces=("",))

    events = await _ask(client, user)

    assert [name for name, _ in events] == ["error"]
    assert not (await db.execute(select(ChatMessage))).scalars().all()
    trace = (await db.execute(select(AiInteraction))).scalar_one()
    assert trace.error and trace.message_id is None


async def test_a_question_is_stored_before_the_answer_to_it(client, db, monkeypatch):
    """Both used to be stamped when the answer was saved, so a pair shared one timestamp
    and the history was free to show the answer above the question that caused it."""
    user = await make_user(db)
    _stub_retrieval(monkeypatch)
    _stub_model(monkeypatch)

    await _ask(client, user)

    history = await client.get("/api/v1/chat/history", headers=auth(user))
    roles = [m["role"] for m in history.json()]
    assert roles == ["user", "assistant"]


async def test_clearing_the_conversation_takes_its_traces_with_it(client, db, monkeypatch):
    """The foreign key to chat_messages made the delete fail outright, and a trace keeps
    the question verbatim - leaving it behind would contradict what the screen promises."""
    user = await make_user(db)
    _stub_retrieval(monkeypatch)
    _stub_model(monkeypatch)
    await _ask(client, user)
    assert (await db.execute(select(AiInteraction))).scalars().all(), "precondition: a trace exists"

    cleared = await client.delete("/api/v1/chat/history", headers=auth(user))

    assert cleared.status_code == 204
    assert not (await db.execute(select(ChatMessage))).scalars().all()
    assert not (await db.execute(select(AiInteraction))).scalars().all()


async def test_a_failed_turn_leaves_nothing_behind_either(client, db, monkeypatch):
    """Its trace has no message to be deleted along with, and it holds the question."""
    user = await make_user(db)
    _stub_retrieval(monkeypatch)
    _stub_model(monkeypatch, fail_after=0)
    await _ask(client, user)

    await client.delete("/api/v1/chat/history", headers=auth(user))

    assert not (await db.execute(select(AiInteraction))).scalars().all()


async def test_the_answer_is_given_the_session_the_program_prescribes(client, db, monkeypatch):
    """Asked what to train, the coach used to answer from the course material and invent
    a workout. The prescription has to reach the model as text it can only read out."""
    user = await make_user(db)
    await make_profile(db, user)
    program = await make_program(db, user, [("Горна част Б", [("Overhead Press", "shoulders", 4, 5, 8)])])
    _stub_retrieval(monkeypatch)

    seen = {}

    async def capture(**kwargs):
        seen["system"] = kwargs["messages"][0]["content"]

        async def stream():
            yield _delta("ok")
            yield _usage(10, 5)

        return stream()

    monkeypatch.setattr(chat_route.openai_client.chat.completions, "create", capture)

    await _ask(client, user, "Какво тренирам днес?")

    assert "Overhead Press" in seen["system"], "the prescribed exercise never reached the model"
    assert "ДНЕШНАТА ТРЕНИРОВКА" in seen["system"]
    assert program
