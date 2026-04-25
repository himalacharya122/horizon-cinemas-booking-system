# ============================================
# Author: Ridesha khadka
# Student ID: 23002960
# Last Edited: 2026-04-25
# ============================================

"""
backend/schemas/booking.py
Pydantic models for booking creation, receipts, and cancellation.
"""

from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel, Field


# Seat map
class SeatOut(BaseModel):
    seat_id: int
    seat_number: str
    row_label: str
    seat_type: str
    is_available: bool

    model_config = {"from_attributes": True}


class SeatMapResponse(BaseModel):
    seats: list[SeatOut]
    showing_id: int
    show_date: date
    seat_type: str


# Booking creation
class BookingCreate(BaseModel):
    showing_id: int
    show_date: date
    customer_name: str = Field(..., min_length=1, max_length=255)
    customer_phone: Optional[str] = Field(default=None, max_length=20)
    customer_email: Optional[str] = Field(default=None, max_length=255)
    seat_type: str = Field(..., pattern="^(lower_hall|upper_gallery|vip)$")
    num_tickets: int = Field(..., ge=1)
    payment_simulated: bool = False
    seat_ids: Optional[list[int]] = None  # specific seats chosen via seat map


# Booked seat detail
class BookedSeatOut(BaseModel):
    seat_number: str
    seat_type: str
    unit_price: float

    model_config = {"from_attributes": True}


# Booking receipt / response
class BookingOut(BaseModel):
    booking_id: int
    booking_reference: str
    showing_id: int
    show_date: date
    film_title: str = ""
    show_time: Optional[time] = None
    screen_number: int = 0
    cinema_name: str = ""
    customer_name: str
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    num_tickets: int
    total_cost: float
    booking_status: str
    payment_simulated: bool
    booking_date: Optional[datetime] = None
    booked_seats: list[BookedSeatOut] = []
    cancelled_at: Optional[datetime] = None
    cancellation_fee: float = 0.00
    refund_amount: float = 0.00

    model_config = {"from_attributes": True}


# Cancellation
class CancelRequest(BaseModel):
    booking_reference: str = Field(..., min_length=1)


class CancelResponse(BaseModel):
    booking_reference: str
    booking_status: str
    cancellation_fee: float
    refund_amount: float
    message: str


# Availability check
class AvailabilityRequest(BaseModel):
    showing_id: int
    show_date: date
    seat_type: str = Field(..., pattern="^(lower_hall|upper_gallery|vip)$")
    num_tickets: int = Field(..., ge=1)


class AvailabilityResponse(BaseModel):
    available: bool
    seats_available: int
    seats_total: int
    unit_price: float
    total_price: float
    seat_type: str
    show_type: str
