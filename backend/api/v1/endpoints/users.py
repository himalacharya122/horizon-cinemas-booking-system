"""
backend/api/v1/endpoints/users.py
User management endpoints for admin: list staff, reset passwords, activity logs.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from backend.core.database import get_db
from backend.core.exceptions import HCBSException
from backend.api.deps import require_role
from backend.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])


class CreateUserRequest(BaseModel):
    username: str
    first_name: str
    last_name: str
    email: str
    role: str  # booking_staff, admin, manager
    cinema_id: int


@router.post("", status_code=201)
def create_user(
    body: CreateUserRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("manager")),
):
    """Create a new staff user account. (Manager only)"""
    try:
        return user_service.create_user(
            db,
            username=body.username,
            first_name=body.first_name,
            last_name=body.last_name,
            email=body.email,
            role_name=body.role,
            cinema_id=body.cinema_id,
        )
    except HCBSException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("")
def list_users(
    cinema_id: Optional[int] = Query(default=None),
    role: Optional[str] = Query(default=None),
    active_only: bool = Query(default=True),
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "manager")),
):
    """List all users, optionally filtered by cinema or role. (Admin/Manager)"""
    return user_service.get_all_users(db, cinema_id, role, active_only)


@router.post("/{user_id}/reset-password")
def reset_password(
    user_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "manager")),
):
    """Reset a user's password to the default (Horizon@123). (Admin/Manager)"""
    try:
        return user_service.reset_user_password(db, user_id)
    except HCBSException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/{user_id}/toggle-active")
def toggle_active(
    user_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "manager")),
):
    """Activate or deactivate a user account. (Admin/Manager)"""
    try:
        return user_service.toggle_user_active(db, user_id)
    except HCBSException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/{user_id}/activity")
def user_activity(
    user_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "manager")),
):
    """Get recent booking activity for a staff member. (Admin/Manager)"""
    try:
        return user_service.get_user_activity(db, user_id, limit)
    except HCBSException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
