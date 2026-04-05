"""
backend/services/user_service.py
User management: list staff, reset passwords, activity logs.
"""

from typing import Optional

from sqlalchemy import func, desc  # type: ignore
from sqlalchemy.orm import Session, joinedload  # type: ignore

from backend.models.user import User, Role
from backend.models.cinema import Cinema
from backend.models.booking import Booking
from backend.core.security import hash_password
from backend.core.exceptions import NotFoundError, ValidationError


def get_all_users(
    db: Session,
    cinema_id: Optional[int] = None,
    role_name: Optional[str] = None,
    active_only: bool = True,
) -> list[dict]:
    """Return all users with their cinema and role info."""
    query = (
        db.query(User)
        .options(
            joinedload(User.role),
            joinedload(User.cinema),
        )
    )

    if cinema_id:
        query = query.filter(User.cinema_id == cinema_id)
    if role_name:
        query = query.join(Role, User.role_id == Role.role_id).filter(
            Role.role_name == role_name
        )
    if active_only:
        query = query.filter(User.is_active == True)  # noqa: E712

    users = query.order_by(User.user_id).all()

    return [
        {
            "user_id": u.user_id,
            "username": u.username,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role_name,
            "cinema_id": u.cinema_id,
            "cinema_name": u.cinema.cinema_name if u.cinema else "",
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login": u.last_login.isoformat() if u.last_login else None,
        }
        for u in users
    ]


def reset_user_password(
    db: Session,
    user_id: int,
    new_password: str = "Horizon@123",
) -> dict:
    """
    Reset a user's password.
    Default password: Horizon@123
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise NotFoundError("User")

    user.password_hash = hash_password(new_password)
    db.commit()

    return {
        "user_id": user.user_id,
        "username": user.username,
        "message": f"Password for '{user.username}' has been reset successfully.",
    }


def toggle_user_active(db: Session, user_id: int) -> dict:
    """Toggle a user's active status."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise NotFoundError("User")

    user.is_active = not user.is_active
    db.commit()

    status = "activated" if user.is_active else "deactivated"
    return {
        "user_id": user.user_id,
        "username": user.username,
        "is_active": user.is_active,
        "message": f"User '{user.username}' has been {status}.",
    }


def create_user(
    db: Session,
    username: str,
    first_name: str,
    last_name: str,
    email: str,
    role_name: str,
    cinema_id: int,
    password: str = "Horizon@123",
) -> dict:
    """
    Create a new staff user. (Manager only)
    Default password: Horizon@123
    """
    # Check unique username
    exists = db.query(User).filter(User.username == username).first()
    if exists:
        raise ValidationError(f"Username '{username}' is already taken.")

    # Check unique email
    exists = db.query(User).filter(User.email == email).first()
    if exists:
        raise ValidationError(f"Email '{email}' is already in use.")

    # Look up role
    role = db.query(Role).filter(Role.role_name == role_name).first()
    if not role:
        raise ValidationError(f"Invalid role: '{role_name}'")

    # Check cinema exists
    cinema = db.query(Cinema).filter(Cinema.cinema_id == cinema_id).first()
    if not cinema:
        raise NotFoundError("Cinema")

    user = User(
        username=username,
        first_name=first_name,
        last_name=last_name,
        email=email,
        role_id=role.role_id,
        cinema_id=cinema_id,
        password_hash=hash_password(password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "user_id": user.user_id,
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "role": role_name,
        "cinema_name": cinema.cinema_name,
        "message": f"User '{username}' created successfully with default password.",
    }


def get_user_activity(
    db: Session, user_id: int, limit: int = 50
) -> list[dict]:
    """
    Get recent booking activity for a specific staff member.
    Returns the most recent bookings they processed.
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise NotFoundError("User")

    bookings = (
        db.query(Booking)
        .filter(Booking.booked_by == user_id)
        .order_by(Booking.booking_date.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "booking_reference": b.booking_reference,
            "customer_name": b.customer_name,
            "num_tickets": b.num_tickets,
            "total_cost": float(b.total_cost),
            "booking_status": b.booking_status,
            "booking_date": b.booking_date.isoformat() if b.booking_date else None,
            "show_date": b.show_date.isoformat() if b.show_date else None,
        }
        for b in bookings
    ]
