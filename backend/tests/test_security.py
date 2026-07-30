"""Tests for password hashing and JWT handling.

Password hashing broke once already (passlib 1.7.4 is unmaintained and raises with
bcrypt >= 4.1), and it broke at runtime on the register endpoint rather than in CI.
These tests exercise the primitives directly so a dependency bump cannot silently
take authentication down again.
"""
import pytest

from app.core.security import create_access_token, decode_token, hash_password, verify_password


def test_correct_password_verifies():
    assert verify_password("mypassword123", hash_password("mypassword123"))


def test_wrong_password_is_rejected():
    assert not verify_password("wrongpassword", hash_password("mypassword123"))


def test_hash_is_salted():
    """Two hashes of the same password must differ, or the salt is not being applied."""
    assert hash_password("same-password") != hash_password("same-password")


def test_hash_is_not_the_plaintext():
    h = hash_password("mypassword123")
    assert "mypassword123" not in h
    assert h.startswith("$2b$")


@pytest.mark.parametrize("password", ["парола123", "pässwörd!", "🏋️lift🏋️", "a" * 200])
def test_unicode_and_long_passwords_round_trip(password):
    assert verify_password(password, hash_password(password))


def test_passwords_differing_after_72_bytes_are_distinguished():
    """bcrypt alone ignores everything past 72 bytes, so these two would collide.

    The SHA-256 pre-hash is what keeps them distinct; if it is ever removed, this test
    fails instead of the app silently accepting the wrong password.
    """
    stored = hash_password("x" * 199 + "y")
    assert not verify_password("x" * 199 + "z", stored)


def test_malformed_stored_hash_fails_closed():
    assert not verify_password("anything", "not-a-real-hash")


def test_jwt_round_trip():
    assert decode_token(create_access_token("user-42")) == "user-42"


def test_tampered_token_is_rejected():
    token = create_access_token("user-42")
    assert decode_token(token[:-3] + "aaa") is None


def test_garbage_token_is_rejected():
    assert decode_token("not.a.token") is None
