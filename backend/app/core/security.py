import base64
import hashlib
import secrets
from datetime import datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

_BCRYPT_ROUNDS = 12

MIN_PASSWORD_LENGTH = 8


def password_problems(password: str) -> list[str]:
    """Which requirements a password fails: length, letter, digit, symbol.

    The account holds body photos, weight history and health answers, and "12345678"
    passes a length check on its own.

    Codes, not sentences: this module decides what a password must be, while how to say
    that to a user is Bulgarian prose and belongs with the rest of it in core/errors.
    """
    problems = []
    if len(password) < MIN_PASSWORD_LENGTH:
        problems.append("length")
    if not any(c.isalpha() for c in password):
        problems.append("letter")
    if not any(c.isdigit() for c in password):
        problems.append("digit")
    # A space is a typo in a password field, not a deliberate symbol, and it is invisible.
    if not any(not c.isalnum() and not c.isspace() for c in password):
        problems.append("symbol")
    return problems


def _prepare(password: str) -> bytes:
    """Reduce the password to a fixed 44-byte token before bcrypt.

    bcrypt only reads the first 72 bytes of its input and raises on longer secrets
    (bcrypt >= 4.1). Pre-hashing with SHA-256 and base64-encoding avoids both problems:
    the result is always 44 bytes and contains no NUL byte (bcrypt stops at the first
    NUL). Same construction Django and passlib's bcrypt_sha256 use, so no password is
    ever silently truncated.
    """
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    return base64.b64encode(digest)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_prepare(password), bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_prepare(plain), hashed.encode("utf-8"))
    except ValueError:
        # Malformed or truncated hash in the database — treat as a failed login.
        return False


def new_reset_token() -> tuple[str, str]:
    """A password-reset token and the hash to store for it.

    The raw token goes in the email and is never written down; the database only gets
    the hash, so a leaked table cannot be used to take over accounts. SHA-256 is enough
    here, unlike for passwords: this secret is 32 random bytes, not something a person
    chose, so there is nothing to brute-force.
    """
    raw = secrets.token_urlsafe(32)
    return raw, hash_reset_token(raw)


def hash_reset_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def create_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": user_id, "exp": expire},
        settings.SECRET_KEY,
        algorithm="HS256",
    )


def decode_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload.get("sub")
    except JWTError:
        return None
