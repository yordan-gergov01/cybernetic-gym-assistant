"""The API over HTTP: signing in, and who is allowed to touch what.

These go through the real app - routing, dependencies, error handlers - so they cover
the one thing service-level tests cannot: that a request from the wrong user, or with a
dead token, is refused before it reaches any of the logic.
"""
from app.core.security import create_access_token

from .factories import make_profile, make_program, make_user, prescribed

CREDENTIALS = {"email": "new@example.com", "password": "hunter2hunter2", "name": "Нов"}

UPPER = ("Upper", [("Barbell Bench Press", "chest", 4, 6, 8)])


def auth(user) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


async def test_registering_returns_a_token_that_identifies_the_account(client):
    registered = await client.post("/api/v1/auth/register", json=CREDENTIALS)
    assert registered.status_code == 201

    me = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {registered.json()['access_token']}"}
    )
    assert me.status_code == 200
    assert me.json()["email"] == CREDENTIALS["email"]


async def test_the_same_address_cannot_register_twice(client):
    await client.post("/api/v1/auth/register", json=CREDENTIALS)
    again = await client.post("/api/v1/auth/register", json=CREDENTIALS)
    assert again.status_code == 400
    assert again.json()["detail"], "the user has to be told why, in Bulgarian"


async def test_signing_in_with_the_wrong_password_is_refused(client):
    await client.post("/api/v1/auth/register", json=CREDENTIALS)
    denied = await client.post(
        "/api/v1/auth/login", json={"email": CREDENTIALS["email"], "password": "not-the-password"}
    )
    assert denied.status_code == 401


async def test_a_token_that_is_not_ours_is_refused(client):
    answer = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-token"})
    assert answer.status_code == 401


async def test_today_says_there_is_no_program_yet_rather_than_failing(client, db):
    """The Today screen turns this 404 into the "create a program" card."""
    user = await make_user(db)
    await make_profile(db, user)

    answer = await client.get("/api/v1/workouts/today", headers=auth(user))
    assert answer.status_code == 404
    assert answer.json()["detail"]


async def test_today_serves_the_first_session_of_the_program(client, db):
    user = await make_user(db)
    await make_profile(db, user, training_days_per_week=2)
    await make_program(db, user, [UPPER, ("Lower", [("Barbell Squat", "quads", 4, 6, 8)])])

    answer = await client.get("/api/v1/workouts/today", headers=auth(user))
    assert answer.status_code == 200
    assert answer.json()["day_name"] == "Upper"


async def test_one_user_cannot_edit_another_users_program(client, db):
    """An exercise id says nothing about who owns it, so the row is reached through the
    program - otherwise a guessed id is enough to rewrite somebody else's plan."""
    owner = await make_user(db, email="owner@example.com")
    program = await make_program(db, owner, [UPPER])
    exercise = (await prescribed(db, program, "Barbell Bench Press"))[0]

    intruder = await make_user(db, email="intruder@example.com")
    answer = await client.patch(
        f"/api/v1/programs/{program.id}/exercises/{exercise.id}",
        json={"sets_prescribed": 99},
        headers=auth(intruder),
    )

    assert answer.status_code == 404
    assert (await prescribed(db, program, "Barbell Bench Press"))[0].sets_prescribed == 4


async def test_a_program_change_is_refused_while_the_engine_asks_for_nothing(client, db):
    """The adjustments carry out a verdict; without one they would just be edits with a
    coaching name on them."""
    user = await make_user(db)
    await make_profile(db, user)
    program = await make_program(db, user, [UPPER])

    answer = await client.post(
        f"/api/v1/programs/{program.id}/exercises/intensify",
        json={"exercise_name": "Barbell Bench Press"},
        headers=auth(user),
    )
    assert answer.status_code == 409
    assert answer.json()["detail"]


async def test_a_swap_needs_an_exercise_from_the_course_library(client, db):
    user = await make_user(db)
    program = await make_program(db, user, [UPPER])

    answer = await client.post(
        f"/api/v1/programs/{program.id}/exercises/swap",
        json={"exercise_name": "Barbell Bench Press", "replacement_name": "Whatever I felt like"},
        headers=auth(user),
    )
    assert answer.status_code == 404


async def test_a_swap_through_the_api_rewrites_the_whole_program(client, db):
    user = await make_user(db)
    program = await make_program(db, user, [UPPER], weeks=3)

    answer = await client.post(
        f"/api/v1/programs/{program.id}/exercises/swap",
        json={"exercise_name": "Barbell Bench Press", "replacement_name": "Arnold Press"},
        headers=auth(user),
    )

    assert answer.status_code == 200
    assert answer.json()["rows_changed"] == 3
    assert len(await prescribed(db, program, "Arnold Press")) == 3
