"""
backend/api/v1/endpoints/auth.py
POST /api/v1/auth/login
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session  # type: ignore

from backend.core.database import get_db
from backend.core.exceptions import AuthenticationError
from backend.schemas.auth import LoginRequest, LoginResponse
from backend.services.auth_service import authenticate_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate a staff member and return a JWT access token.

    The token should be sent as `Authorization: Bearer <token>` on
    all subsequent requests.
    """
    try:
        result = authenticate_user(db, body.username, body.password)
        return result
    except AuthenticationError as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=exc.status_code, detail=exc.message)
