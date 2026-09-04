"""The rules for choosing a password, and who they apply to.

The account holds body photos, weight history and health answers, so "12345678" passing
a length check is the failure worth testing for. What each case asserts is the rule, not
the wording: the message is checked only where the user has to act on it.
"""
import pytest
from pydantic import ValidationError

from app.core.errors import _label, _reason
from app.schemas import ChangePasswordRequest, ResetPasswordRequest, UserLogin, UserRegister

STRONG = "Parola1!"


def _rejection(schema, password: str) -> str:
    """The sentence the user would read, assembled the way the API assembles it."""
    with pytest.raises(ValidationError) as raised:
        if schema is UserRegister:
            schema(email="lifter@example.com", password=password, name="Lifter")
        elif schema is ResetPasswordRequest:
            schema(token="t", new_password=password)
        else:
            schema(current_password=STRONG, new_password=password)
    error = raised.value.errors()[0]
    return f"{_label(tuple(error['loc']))} {_reason(error)}"


@pytest.mark.parametrize("schema", [UserRegister, ResetPasswordRequest, ChangePasswordRequest])
@pytest.mark.parametrize("weak", ["12345678", "password", "Password1", "krat1!"])
def test_every_place_a_password_is_set_applies_the_same_rule(schema, weak):
    """Registration, the reset link and the change form - a rule enforced on two of the
    three leaves a way to set the password it rejects."""
    assert _rejection(schema, weak)


@pytest.mark.parametrize("schema", [UserRegister, ResetPasswordRequest, ChangePasswordRequest])
def test_a_password_with_a_letter_a_digit_and_a_symbol_is_accepted(schema):
    if schema is UserRegister:
        assert schema(email="lifter@example.com", password=STRONG, name="Lifter")
    elif schema is ResetPasswordRequest:
        assert schema(token="t", new_password=STRONG)
    else:
        assert schema(current_password="whatever", new_password=STRONG)


def test_signing_in_is_not_held_to_the_new_rule():
    """Every account created under the old rule would otherwise be locked out of an app
    it already owns."""
    assert UserLogin(email="lifter@example.com", password="12345678")


def test_the_rejection_says_which_rule_was_broken():
    """"Невалиден формат" makes the user guess; they retry blindly and give up."""
    assert "цифра" in _rejection(UserRegister, "password!")
    assert "специален знак" in _rejection(UserRegister, "Password1")
    assert "поне 8 знака" in _rejection(UserRegister, "krat1!")


def test_a_space_alone_does_not_pass_for_a_special_character():
    """A trailing space is a typo, not a deliberate symbol, and it is invisible in a
    password field."""
    assert "специален знак" in _rejection(UserRegister, "parola 1234")


def test_the_password_field_is_named_in_bulgarian():
    """Without a label the user reads "new_password трябва да съдържа...", which is the
    schema talking, not the app."""
    assert _rejection(ChangePasswordRequest, "12345678").startswith("Новата парола")
    assert _rejection(UserRegister, "12345678").startswith("Паролата")
