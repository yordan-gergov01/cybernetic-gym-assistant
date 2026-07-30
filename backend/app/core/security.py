import base64
import hashlib
from datetime import datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

_BCRYPT_ROUNDS = 12


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
