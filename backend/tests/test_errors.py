"""Tests for the API's error responses.

What matters is that a non-technical user can read the message and know what to do, so
these assert the shape and language of the response - never the English text Pydantic
produced underneath.
"""
import re

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import BaseModel, EmailStr, Field
from typing import Literal

from app.core.errors import unhandled_exception_handler, validation_exception_handler

CYRILLIC = re.compile(r"[А-Яа-я]")


class Payload(BaseModel):
    age: int = Field(ge=14, le=100)
    sex: Literal["male", "female"]
    bodyweight_kg: float = Field(gt=30, lt=300)
    email: EmailStr
    name: str = Field(min_length=1, max_length=10)


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    @app.post("/echo")
    async def echo(payload: Payload):
        return {"ok": True}

    @app.get("/boom")
    async def boom():
        raise RuntimeError("database connection lost")

    return TestClient(app, raise_server_exceptions=False)


def valid() -> dict:
    return {"age": 30, "sex": "male", "bodyweight_kg": 82.5, "email": "a@b.bg", "name": "Дан"}


def test_a_valid_payload_still_passes(client):
    assert client.post("/echo", json=valid()).status_code == 200


def test_a_validation_error_is_a_readable_bulgarian_sentence(client):
    r = client.post("/echo", json={**valid(), "age": 8})
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert isinstance(detail, str), "the UI shows detail directly; a list would be dumped as JSON"
    assert CYRILLIC.search(detail), f"the user must not read English: {detail}"
    assert "Input should be" not in detail


def test_the_message_names_the_field_and_the_limit(client):
    # "Възрастта не може да е под 14." - the user has to know which input and why.
    detail = client.post("/echo", json={**valid(), "age": 8}).json()["detail"]
    assert "Възраст" in detail
    assert "14" in detail


def test_an_out_of_range_upper_bound_is_explained_too(client):
    detail = client.post("/echo", json={**valid(), "bodyweight_kg": 500}).json()["detail"]
    assert "Тегло" in detail
    assert "300" in detail


def test_a_missing_field_says_it_is_missing(client):
    body = valid()
    del body["sex"]
    detail = client.post("/echo", json=body).json()["detail"]
    assert "Полът" in detail and "липсва" in detail


def test_a_wrong_type_does_not_leak_the_english_type_name(client):
    detail = client.post("/echo", json={**valid(), "age": "трийсет"}).json()["detail"]
    assert CYRILLIC.search(detail)
    assert "int_parsing" not in detail and "integer" not in detail.lower()


def test_an_unaccepted_option_lists_what_is_accepted(client):
    detail = client.post("/echo", json={**valid(), "sex": "helicopter"}).json()["detail"]
    assert "male" in detail and "female" in detail


def test_every_failing_field_is_reported_not_just_the_first(client):
    r = client.post("/echo", json={**valid(), "age": 8, "bodyweight_kg": 5})
    detail = r.json()["detail"]
    assert "Възраст" in detail and "Тегло" in detail


def test_failing_fields_are_listed_for_the_form_to_highlight(client):
    fields = client.post("/echo", json={**valid(), "age": 8}).json()["fields"]
    assert fields == ["age"]


def test_an_unexpected_crash_never_reaches_the_user_as_a_stack_trace(client):
    r = client.get("/boom")
    assert r.status_code == 500
    detail = r.json()["detail"]
    assert CYRILLIC.search(detail)
    assert "RuntimeError" not in detail and "database" not in detail
