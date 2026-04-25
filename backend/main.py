# ============================================
# Author: Himal Acharya
# Student ID: 22085619
# Last Edited: 2026-04-25
# ============================================

"""
backend/main.py
FastAPI application entry point.

Run with:
    uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.v1.router import api_router
from backend.core.exceptions import HCBSException
from config.settings import DEBUG

app = FastAPI(
    title="Horizon Cinemas Booking System",
    description="Staff-facing API for managing film listings, bookings, and cinemas.",
    version="1.0.0",
    debug=DEBUG,
)

# CORS (allows PyQt6 desktop client to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler for business errors
@app.exception_handler(HCBSException)
async def hcbs_exception_handler(request: Request, exc: HCBSException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


# Register routers
app.include_router(api_router)


# Health check
@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "hcbs-api"}
