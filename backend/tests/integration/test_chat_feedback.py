"""Who may judge an answer, and what a judgement replaces.

These rules only exist in the database: whose message it is, and whether the message is
one the coach wrote. A stub cannot show that another user's answer is out of reach.
"""
from app.models import ChatMessage

from .factories import make_user
from .test_routes import auth


async def _exchange(db, user, answer: str = "2.0-2.2 г на кг.") -> tuple[ChatMessage, ChatMessage]:
    question = ChatMessage(user_id=user.id, role="user", content="Колко протеин?")
    reply = ChatMessage(user_id=user.id, role="assistant", content=answer)
    db.add_all([question, reply])
    await db.flush()
    return question, reply


async def test_a_verdict_on_an_answer_is_stored_and_visible_in_the_history(client, db):
    user = await make_user(db)
    _, reply = await _exchange(db, user)

    rated = await client.post(
        f"/api/v1/chat/messages/{reply.id}/rating",
        json={"rating": -1, "comment": "Отговори за мъже, а питах за жени."},
        headers=auth(user),
    )
    assert rated.status_code == 204

    history = await client.get("/api/v1/chat/history", headers=auth(user))
    answer = [m for m in history.json() if m["id"] == reply.id][0]
    assert answer["rating"] == -1
    await db.refresh(reply)
    assert reply.rating_comment == "Отговори за мъже, а питах за жени."
    assert reply.rated_at is not None


async def test_another_users_answer_cannot_be_rated(client, db):
    """The rating is a judgement of someone's own coaching, and reaching a stranger's
    message would also confirm that it exists."""
    owner = await make_user(db, email="owner@example.com")
    stranger = await make_user(db, email="stranger@example.com")
    _, reply = await _exchange(db, owner)

    refused = await client.post(
        f"/api/v1/chat/messages/{reply.id}/rating", json={"rating": 1}, headers=auth(stranger)
    )

    assert refused.status_code == 404
    await db.refresh(reply)
    assert reply.rating is None


async def test_rating_your_own_question_is_refused(client, db):
    """Only the coach's answers carry a verdict; a rated question would pollute the very
    set of examples the ratings exist to collect."""
    user = await make_user(db)
    question, _ = await _exchange(db, user)

    refused = await client.post(
        f"/api/v1/chat/messages/{question.id}/rating", json={"rating": 1}, headers=auth(user)
    )

    assert refused.status_code == 400
    await db.refresh(question)
    assert question.rating is None


async def test_a_second_verdict_replaces_the_first(client, db):
    """People change their minds after reading an answer again; the current opinion is
    the one that counts, not both."""
    user = await make_user(db)
    _, reply = await _exchange(db, user)

    await client.post(
        f"/api/v1/chat/messages/{reply.id}/rating",
        json={"rating": -1, "comment": "Грешно."}, headers=auth(user),
    )
    await client.post(
        f"/api/v1/chat/messages/{reply.id}/rating", json={"rating": 1}, headers=auth(user)
    )

    await db.refresh(reply)
    assert reply.rating == 1
    assert reply.rating_comment is None, "the old reason does not belong to the new verdict"


async def test_only_a_thumb_up_or_down_is_accepted(client, db):
    user = await make_user(db)
    _, reply = await _exchange(db, user)

    refused = await client.post(
        f"/api/v1/chat/messages/{reply.id}/rating", json={"rating": 3}, headers=auth(user)
    )

    assert refused.status_code == 422
