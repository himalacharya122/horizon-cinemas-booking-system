# ============================================
# Author: Himal Acharya
# Student ID: 22085619
# Last Edited: 2026-04-25
# ============================================

"""
backend/api/v1/endpoints/reports.py
Admin report endpoints: revenue, bookings per listing, top films, staff stats.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session  # type: ignore

from backend.api.deps import require_role
from backend.core.database import get_db
from backend.services import report_service

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/revenue")
def monthly_revenue(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    cinema_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "manager")),
):
    """Total monthly revenue per cinema. (Admin/Manager)"""
    return report_service.monthly_revenue_by_cinema(db, year, month, cinema_id)


@router.get("/bookings-per-listing")
def bookings_per_listing(
    cinema_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "manager")),
):
    """Number of confirmed bookings per listing. (Admin/Manager)"""
    return report_service.bookings_per_listing(db, cinema_id)


@router.get("/top-films")
def top_films(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "manager")),
):
    """Top revenue-generating films for a month. (Admin/Manager)"""
    return report_service.top_revenue_films(db, year, month, limit)


@router.get("/staff-bookings")
def staff_bookings(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    cinema_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "manager")),
):
    """Monthly staff booking activity sorted by count. (Admin/Manager)"""
    return report_service.staff_booking_report(db, year, month, cinema_id)


@router.get("/occupancy")
def occupancy(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    cinema_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "manager")),
):
    """Screen occupancy report for a month. (Admin/Manager)"""
    return report_service.occupancy_report(db, year, month, cinema_id)


@router.get("/cancellation-rate")
def cancellation_rate(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    cinema_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "manager")),
):
    """Cancellation rate per cinema for a month. (Admin/Manager)"""
    return report_service.cancellation_rate_report(db, year, month, cinema_id)
