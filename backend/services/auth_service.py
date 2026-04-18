"""
backend/services/auth_service.py
Business logic for user authentication.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session  # type: ignore

from backend.core.exceptions import AuthenticationError
from backend.core.security import create_access_token, verify_password
from backend.models.user import User


def authenticate_user(db: Session, username: str, password: str) -> dict:
    """
    Validate credentials, update last_login, and return a JWT + user info.

    Returns:
        {
            "access_token": "eyJ...",
            "token_type": "bearer",
            "user": {
                "user_id": 9,
                "username": "himal",
                "full_name": "Himal Acharya",
                "role": "booking_staff",
                "cinema_id": 1,
                "cinema_name": "Horizon Birmingham Central"
            }
        }

    Raises:
        AuthenticationError - on bad username, bad password, or inactive account.
    """
    user: User | None = db.query(User).filter(User.username == username).first()

    if user is None:
        raise AuthenticationError("Invalid username or password")

    if not user.is_active:
        raise AuthenticationError("Account is deactivated — contact your manager")

    if not verify_password(password, user.password_hash):
        raise AuthenticationError("Invalid username or password")

    # Update last login timestamp
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    # Build JWT
    token = create_access_token(
        user_id=user.user_id,
        username=user.username,
        role_name=user.role.role_name,
        cinema_id=user.cinema_id,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "user_id": user.user_id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role.role_name,
            "cinema_id": user.cinema_id,
            "cinema_name": user.cinema.cinema_name,
        },
    }
