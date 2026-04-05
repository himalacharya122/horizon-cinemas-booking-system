"""
backend/api/v1/endpoints/bookings.py
Booking creation, cancellation, lookup, and availability checking.
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session # type: ignore

from backend.core.database import get_db
from backend.core.exceptions import HCBSException
from backend.api.deps import get_current_user

from backend.schemas.booking import (
    BookingCreate, BookingOut, BookedSeatOut,
    CancelRequest, CancelResponse,
    AvailabilityRequest, AvailabilityResponse,
)
from backend.services import booking_service

router = APIRouter(prefix="/bookings", tags=["Bookings"])


# Availability check
@router.post("/check-availability", response_model=AvailabilityResponse)
def check_availability(
    body: AvailabilityRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Check seat availability and pricing for a showing + date + seat type."""
    try:
        return booking_service.check_availability(
            db, body.showing_id, body.show_date, body.seat_type, body.num_tickets
        )
    except HCBSException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# Create booking
@router.post("", response_model=BookingOut, status_code=201)
def create_booking(
    body: BookingCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    Create a new booking.
    Validates all business rules (advance limit, availability, date range).
    Automatically assigns seats and calculates the total cost.
    """
    try:
        booking = booking_service.create_booking(
            db, body.model_dump(), booked_by=int(user["sub"])
        )
        return _serialise_booking(booking)
    except HCBSException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# Cancel booking
@router.post("/cancel", response_model=CancelResponse)
def cancel_booking(
    body: CancelRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """
    Cancel a booking by reference.
    Rules: not on the day of the show, 50% cancellation charge.
    """
    try:
        booking = booking_service.cancel_booking(db, body.booking_reference)
        return {
            "booking_reference": booking.booking_reference,
            "booking_status": booking.booking_status,
            "cancellation_fee": float(booking.cancellation_fee),
            "refund_amount": float(booking.refund_amount),
            "message": (
                f"Booking {booking.booking_reference} cancelled. "
                f"Cancellation fee: £{booking.cancellation_fee:.2f}, "
                f"Refund: £{booking.refund_amount:.2f}"
            ),
        }
    except HCBSException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# Lookup
@router.get("/reference/{reference}", response_model=BookingOut)
def get_booking_by_reference(
    reference: str,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Look up a booking by its reference code (e.g. HC-2025-00001)."""
    try:
        booking = booking_service.get_booking_by_reference(db, reference)
        return _serialise_booking(booking)
    except HCBSException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/search", response_model=list[BookingOut])
def search_bookings(
    cinema_id: Optional[int] = Query(default=None),
    customer_name: Optional[str] = Query(default=None),
    customer_email: Optional[str] = Query(default=None),
    customer_phone: Optional[str] = Query(default=None),
    show_date: Optional[date] = Query(default=None),
    booking_date: Optional[date] = Query(default=None),
    status: Optional[str] = Query(default=None),
    booked_by: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Search bookings with optional filters."""
    bookings = booking_service.search_bookings(
        db, cinema_id, customer_name, customer_email, show_date, status,
        customer_phone=customer_phone, booked_by=booked_by,
        booking_date=booking_date,
    )
    return [_serialise_booking(b) for b in bookings]


# Serialisation helper
def _serialise_booking(booking) -> dict:
    """Convert Booking ORM → dict matching BookingOut schema."""
    showing = booking.showing
    listing = showing.listing if showing else None
    film = listing.film if listing else None
    screen = listing.screen if listing else None
    cinema = screen.cinema if screen else None

    return {
        "booking_id": booking.booking_id,
        "booking_reference": booking.booking_reference,
        "showing_id": booking.showing_id,
        "show_date": booking.show_date,
        "film_title": film.title if film else "",
        "show_time": showing.show_time if showing else None,
        "screen_number": screen.screen_number if screen else 0,
        "cinema_name": cinema.cinema_name if cinema else "",
        "customer_name": booking.customer_name,
        "customer_phone": booking.customer_phone,
        "customer_email": booking.customer_email,
        "num_tickets": booking.num_tickets,
        "total_cost": float(booking.total_cost),
        "booking_status": booking.booking_status,
        "payment_simulated": booking.payment_simulated,
        "booking_date": booking.booking_date,
        "booked_seats": [
            {
                "seat_number": bs.seat.seat_number if bs.seat else "?",
                "seat_type": bs.seat.seat_type if bs.seat else "?",
                "unit_price": float(bs.unit_price),
            }
            for bs in booking.booked_seats
        ],
        "cancelled_at": booking.cancelled_at,
        "cancellation_fee": float(booking.cancellation_fee) if booking.cancellation_fee else 0.0,
        "refund_amount": float(booking.refund_amount) if booking.refund_amount else 0.0,
    }