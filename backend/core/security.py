# core/security.py
"""
Password hashing and JWT token utilities.

All auth logic routes through here - nothing else should import
jose or passlib directly.
"""

import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from core.logger import get_logger

logger = get_logger(__name__)

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Secret used to sign tokens. Must be set in .env for production.
_SECRET = os.getenv("JWT_SECRET", "")
_ALGORITHM = "HS256"
_TOKEN_EXPIRE_DAYS = 30


def validate_secret() -> None:
    """Call at startup - warns if JWT_SECRET is not set in .env."""
    if not _SECRET:
        logger.warning(
            "JWT_SECRET not set in .env - safe for local dev only, required for production"
        )


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def create_token(user_id: str, email: str) -> str:
    """Create a signed JWT that expires in 30 days."""
    expire = datetime.now(timezone.utc) + timedelta(days=_TOKEN_EXPIRE_DAYS)
    payload = {"sub": user_id, "email": email, "exp": expire}
    return jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)


def decode_token(token: str) -> dict | None:
    """
    Decode and verify a JWT. Returns the payload dict on success,
    None if the token is invalid or expired.
    """
    try:
        return jwt.decode(token, _SECRET, algorithms=[_ALGORITHM])
    except JWTError:
        return None
