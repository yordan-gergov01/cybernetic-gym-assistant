"""Getting back into an account, and changing the password from inside one.

A reset link is a temporary key to somebody's account, so what is tested here is mostly
what it must *not* do: work twice, work after it expires, work after a newer one was
asked for, or tell a stranger which addresses are registered.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.security import hash_reset_token, verify_password
from app.models import PasswordResetToken, User

from .factories import make_user

PASSWORD = "hunter2hunter2"
NEW_PASSWORD = "correct-horse-battery"


async def issued_token(db, client, email: str) -> str:
    """Run the forgot-password flow and read back the raw token from the sent link.

    The raw token never reaches the database, so the test regenerates it the only way a
    caller could: by asking for a reset and capturing what the mailer was handed.
    """
    sent: list[str] = []

    import app.routes.auth as auth_routes

    original = auth_routes.send_password_reset

    async def capture(_email, link, _minutes):
        sent.append(link.split("token=")[1])
        return True

    auth_routes.send_password_reset = capture
    try:
        answer = await client.post("/api/v1/auth/forgot-password", json={"email": email})
        assert answer.status_code == 200
    finally:
        auth_routes.send_password_reset = original

    return sent[0] if sent else ""


async def test_a_reset_link_sets_a_new_password_and_signs_the_user_in(client, db):
    user = await make_user(db, email="forgetful@example.com")
    token = await issued_token(db, client, user.email)

    answer = await client.post(
        "/api/v1/auth/reset-password", json={"token": token, "new_password": NEW_PASSWORD}
    )

    assert answer.status_code == 200
    assert answer.json()["access_token"], "proving you own the mailbox is enough to be let in"
    await db.refresh(user)
    assert verify_password(NEW_PASSWORD, user.hashed_password)


async def test_a_reset_link_works_only_once(client, db):
    user = await make_user(db, email="twice@example.com")
    token = await issued_token(db, client, user.email)

    first = await client.post(
        "/api/v1/auth/reset-password", json={"token": token, "new_password": NEW_PASSWORD}
    )
    second = await client.post(
        "/api/v1/auth/reset-password", json={"token": token, "new_password": "another-one-entirely"}
    )

    assert first.status_code == 200
    assert second.status_code == 400
    await db.refresh(user)
    assert verify_password(NEW_PASSWORD, user.hashed_password), "the replay must not take effect"


async def test_an_expired_link_is_refused(client, db):
    user = await make_user(db, email="slow@example.com")
    token = await issued_token(db, client, user.email)

    row = (
        await db.execute(
            select(PasswordResetToken).where(PasswordResetToken.token_hash == hash_reset_token(token))
        )
    ).scalar_one()
    row.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    await db.flush()

    answer = await client.post(
        "/api/v1/auth/reset-password", json={"token": token, "new_password": NEW_PASSWORD}
    )
    assert answer.status_code == 400


async def test_asking_again_kills_the_previous_link(client, db):
    """A forwarded or shoulder-surfed email stops working the moment the owner retries."""
    user = await make_user(db, email="again@example.com")
    first_token = await issued_token(db, client, user.email)
    await issued_token(db, client, user.email)

    answer = await client.post(
        "/api/v1/auth/reset-password", json={"token": first_token, "new_password": NEW_PASSWORD}
    )
    assert answer.status_code == 400


async def test_an_unknown_address_gets_the_same_answer_as_a_known_one(client, db):
    """Otherwise this endpoint tells a stranger who has an account here."""
    user = await make_user(db, email="known@example.com")

    known = await client.post("/api/v1/auth/forgot-password", json={"email": user.email})
    unknown = await client.post("/api/v1/auth/forgot-password", json={"email": "nobody@example.com"})

    assert known.status_code == unknown.status_code == 200
    assert known.json() == unknown.json()

    issued = (await db.execute(select(PasswordResetToken))).scalars().all()
    assert all(token.user_id == user.id for token in issued), "no token for an address we do not have"


async def test_a_token_is_never_stored_in_the_clear(client, db):
    user = await make_user(db, email="hashed@example.com")
    token = await issued_token(db, client, user.email)

    stored = (await db.execute(select(PasswordResetToken.token_hash))).scalars().all()
    assert token not in stored
    assert hash_reset_token(token) in stored


async def test_changing_the_password_requires_the_current_one(client, db):
    """A phone left unlocked on a bench is the attacker this guards against."""
    from app.core.security import create_access_token

    user = await make_user(db, email="inside@example.com")
    headers = {"Authorization": f"Bearer {create_access_token(user.id)}"}

    refused = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "not-it", "new_password": NEW_PASSWORD},
        headers=headers,
    )
    assert refused.status_code == 400

    accepted = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
        headers=headers,
    )
    assert accepted.status_code == 200
    await db.refresh(user)
    assert verify_password(NEW_PASSWORD, user.hashed_password)


async def test_the_new_password_has_to_be_a_different_one(client, db):
    from app.core.security import create_access_token

    user = await make_user(db, email="same@example.com")
    answer = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": PASSWORD, "new_password": PASSWORD},
        headers={"Authorization": f"Bearer {create_access_token(user.id)}"},
    )
    assert answer.status_code == 400


async def test_a_short_password_is_refused_before_it_reaches_the_database(client, db):
    user = await make_user(db, email="short@example.com")
    token = await issued_token(db, client, user.email)

    answer = await client.post(
        "/api/v1/auth/reset-password", json={"token": token, "new_password": "short"}
    )

    assert answer.status_code == 422
    assert answer.json()["detail"], "the validation handler answers in Bulgarian"
    unchanged = (await db.execute(select(User).where(User.id == user.id))).scalar_one()
    assert verify_password(PASSWORD, unchanged.hashed_password)
