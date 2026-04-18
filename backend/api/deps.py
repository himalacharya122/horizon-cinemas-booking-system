"""
backend/api/deps.py
FastAPI dependencies for authentication and role-based access control.

Usage in endpoints:
    from backend.api.deps import require_role

    @router.get("/admin-only")
    def admin_endpoint(current_user: dict = Depends(require_role("admin", "manager"))):
        ...
"""

from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.core.security import decode_access_token

_bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> dict:
    """
    Decode JWT from the Authorization header and return the payload.

    Raises 401 if the token is missing, expired, or invalid.
    """
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def require_role(*allowed_roles: str) -> Callable:
    """
    Returns a dependency that checks the current user has one of the
    allowed roles.

    Example:
        Depends(require_role("admin", "manager"))
    """

    def _role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted to: {', '.join(allowed_roles)}",
            )
        return current_user

    return _role_checker
