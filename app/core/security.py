"""
Step 3 — Password hashing (bcrypt) and JWT create/decode.
Never store plain passwords; never put secrets in the JWT payload beyond what's needed.
We use bcrypt directly (not passlib) to avoid version compatibility issues.
"""
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import settings


def hash_password(password: str) -> str:
    """Hash a plain password for storage. One-way — we never reverse it."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check that plain_password matches the stored hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def _create_token(sub: str, token_type: str, expire_delta: timedelta) -> str:
    """Create a JWT with sub (subject = user id), type, and expiry."""
    expire = datetime.now(timezone.utc) + expire_delta
    payload = {"sub": str(sub), "type": token_type, "exp": expire}
    return jwt.encode(
        payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )


def create_access_token(user_id: int) -> str:
    """Short-lived token for API auth (e.g. 15 min)."""
    return _create_token(
        str(user_id), "access", timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)
    )


def create_refresh_token(user_id: int) -> str:
    """Long-lived token to get a new access token (e.g. 7 days)."""
    return _create_token(
        str(user_id), "refresh", timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
    )


def decode_token(token: str) -> dict | None:
    """Decode and validate JWT. Returns payload dict or None if invalid/expired."""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None
