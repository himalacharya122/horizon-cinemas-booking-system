"""
backend/core/security.py
Password hashing (bcrypt) and JWT token creation / verification.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt  # type: ignore
from passlib.context import CryptContext  # type: ignore

from config.settings import JWT_ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, JWT_SECRET_KEY

# Password hashing

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash of the given plain-text password."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plain-text password against its bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# JWT tokens


def create_access_token(
    user_id: int,
    username: str,
    role_name: str,
    cinema_id: int,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT containing the user's identity and role.

    Payload example:
        {
            "sub": "42",
            "username": "himal",
            "role": "booking_staff",
            "cinema_id": 1,
            "exp": 1717000000
        }
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role_name,
        "cinema_id": cinema_id,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT.

    Returns the payload dict on success, or None if the token is
    invalid / expired.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
