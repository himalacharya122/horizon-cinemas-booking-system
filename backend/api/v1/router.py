"""
backend/api/v1/router.py
Collects all v1 endpoint routers under the /api/v1 prefix.
"""

from fastapi import APIRouter

from backend.api.v1.endpoints.ai import router as ai_router
from backend.api.v1.endpoints.ai_sessions import router as ai_sessions_router
from backend.api.v1.endpoints.auth import router as auth_router
from backend.api.v1.endpoints.bookings import router as bookings_router
from backend.api.v1.endpoints.cinemas import router as cinemas_router
from backend.api.v1.endpoints.films import router as films_router
from backend.api.v1.endpoints.reports import router as reports_router
from backend.api.v1.endpoints.users import router as users_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(films_router)
api_router.include_router(bookings_router)
api_router.include_router(cinemas_router)
api_router.include_router(reports_router)
api_router.include_router(users_router)
api_router.include_router(ai_router)
api_router.include_router(ai_sessions_router)
