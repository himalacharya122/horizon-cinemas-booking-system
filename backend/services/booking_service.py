"""
backend/services/booking_service.py
Core business logic for bookings: availability, pricing, creation,
cancellation, and lookups.

Business rules enforced here:
  - Bookings up to 7 days in advance only
  - Cancellation allowed only if show_date > today (not on the day)
  - Cancellation fee = 50% of total_cost
  - Seat double-booking prevention via DB-level unique constraint
  - Pricing: upper gallery = lower hall * 1.20, VIP = lower hall * 1.44
"""

from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import func  # type: ignore
from sqlalchemy.orm import Session, joinedload  # type: ignore

from backend.core.exceptions import BookingError, NotFoundError, ValidationError
from backend.models.booking import BasePrice, BookedSeat, Booking
from backend.models.cinema import Cinema, Screen, Seat
from backend.models.film import Listing, Showing


# Reference generator
def _generate_booking_reference(db: Session) -> str:
    """
    Generate next booking reference in format HC-YYYY-#####.
    """
    year = date.today().year
    prefix = f"HC-{year}-"

    last = (
        db.query(Booking)
        .filter(Booking.booking_reference.like(f"{prefix}%"))
        .order_by(Booking.booking_id.desc())
        .first()
    )

    if last:
        last_num = int(last.booking_reference.split("-")[-1])
        next_num = last_num + 1
    else:
        next_num = 1

    return f"{prefix}{next_num:05d}"


# Price lookup
def get_price_for_showing(db: Session, showing: Showing, seat_type: str) -> float:
    """
    Look up the base price for a showing's city + time period,
    then return the correct price for the given seat type.
    """
    listing = showing.listing
    screen = listing.screen
    cinema = screen.cinema
    city_id = cinema.city_id

    bp = (
        db.query(BasePrice)
        .filter(BasePrice.city_id == city_id, BasePrice.show_period == showing.show_type)
        .first()
    )

    if not bp:
        raise BookingError(
            f"No base price configured for city_id={city_id}, period={showing.show_type}"
        )

    return bp.price_for_seat_type(seat_type)


# Availability
def check_availability(
    db: Session,
    showing_id: int,
    show_date: date,
    seat_type: str,
    num_tickets: int,
) -> dict:
    """
    Check seat availability and return pricing info.

    Returns:
        {
            "available": True/False,
            "seats_available": 42,
            "seats_total": 56,
            "unit_price": 9.60,
            "total_price": 19.20,
            "seat_type": "upper_gallery",
            "show_type": "evening"
        }
    """
    # Load showing with listing → screen → cinema chain
    showing = (
        db.query(Showing)
        .options(
            joinedload(Showing.listing)
            .joinedload(Listing.screen)
            .joinedload(Screen.cinema)
            .joinedload(Cinema.city)
        )
        .filter(Showing.showing_id == showing_id, Showing.is_active == True)  # noqa: E712
        .first()
    )
    if not showing:
        raise NotFoundError("Showing")

    listing = showing.listing
    if not (listing.start_date <= show_date <= listing.end_date):
        raise BookingError("Selected date is outside the listing window")

    screen = listing.screen

    # Total seats of the requested type
    if seat_type == "lower_hall":
        total = screen.lower_hall_seats
    elif seat_type == "upper_gallery":
        total = screen.upper_gallery_seats - screen.vip_seats  # non-VIP upper gallery
    elif seat_type == "vip":
        total = screen.vip_seats
    else:
        raise ValidationError(f"Invalid seat type: {seat_type}")

    # Count already booked seats of this type for this showing + date
    booked = (
        db.query(func.count(BookedSeat.booked_seat_id))
        .join(Booking, BookedSeat.booking_id == Booking.booking_id)
        .join(Seat, BookedSeat.seat_id == Seat.seat_id)
        .filter(
            Booking.showing_id == showing_id,
            Booking.show_date == show_date,
            Booking.booking_status == "confirmed",
            Seat.seat_type == seat_type,
        )
        .scalar()
    ) or 0

    available_count = total - booked
    unit_price = get_price_for_showing(db, showing, seat_type)

    return {
        "available": available_count >= num_tickets,
        "seats_available": available_count,
        "seats_total": total,
        "unit_price": unit_price,
        "total_price": round(unit_price * num_tickets, 2),
        "seat_type": seat_type,
        "show_type": showing.show_type,
    }


# Seat map
def get_seat_map(
    db: Session,
    showing_id: int,
    show_date: date,
    seat_type: str,
) -> dict:
    """Return all seats of the requested type with their availability status."""
    showing = (
        db.query(Showing)
        .options(joinedload(Showing.listing).joinedload(Listing.screen))
        .filter(Showing.showing_id == showing_id, Showing.is_active == True)  # noqa: E712
        .first()
    )
    if not showing:
        raise NotFoundError("Showing")

    screen = showing.listing.screen

    all_seats = (
        db.query(Seat)
        .filter(Seat.screen_id == screen.screen_id, Seat.seat_type == seat_type)
        .order_by(Seat.row_label, Seat.seat_number)
        .all()
    )

    booked_seat_ids = set(
        row[0]
        for row in db.query(BookedSeat.seat_id)
        .join(Booking, BookedSeat.booking_id == Booking.booking_id)
        .filter(
            Booking.showing_id == showing_id,
            Booking.show_date == show_date,
            Booking.booking_status == "confirmed",
        )
        .all()
    )

    return {
        "seats": [
            {
                "seat_id": s.seat_id,
                "seat_number": s.seat_number,
                "row_label": s.row_label,
                "seat_type": s.seat_type,
                "is_available": s.seat_id not in booked_seat_ids,
            }
            for s in all_seats
        ],
        "showing_id": showing_id,
        "show_date": show_date,
        "seat_type": seat_type,
    }


# Validate and fetch specific seats chosen by staff
def _get_seats_by_ids(
    db: Session,
    screen_id: int,
    showing_id: int,
    show_date: date,
    seat_type: str,
    seat_ids: list[int],
) -> list[Seat]:
    seats = (
        db.query(Seat)
        .filter(
            Seat.seat_id.in_(seat_ids),
            Seat.screen_id == screen_id,
            Seat.seat_type == seat_type,
        )
        .all()
    )

    if len(seats) != len(seat_ids):
        raise BookingError("One or more selected seats are invalid for this screen/type")

    booked_seat_ids = set(
        row[0]
        for row in db.query(BookedSeat.seat_id)
        .join(Booking, BookedSeat.booking_id == Booking.booking_id)
        .filter(
            Booking.showing_id == showing_id,
            Booking.show_date == show_date,
            Booking.booking_status == "confirmed",
        )
        .all()
    )

    for seat in seats:
        if seat.seat_id in booked_seat_ids:
            raise BookingError(f"Seat {seat.seat_number} has just been booked by someone else")

    return seats


# Find available seats
def _find_available_seats(
    db: Session,
    screen_id: int,
    showing_id: int,
    show_date: date,
    seat_type: str,
    num_tickets: int,
) -> list[Seat]:
    """
    Return a list of available Seat objects for the requested type.
    Picks the first N unbooked seats.
    """
    # All seats of this type on the screen
    all_seats = (
        db.query(Seat)
        .filter(Seat.screen_id == screen_id, Seat.seat_type == seat_type)
        .order_by(Seat.seat_id)
        .all()
    )

    # IDs of seats already booked for this showing + date
    booked_seat_ids = set(
        row[0]
        for row in db.query(BookedSeat.seat_id)
        .join(Booking, BookedSeat.booking_id == Booking.booking_id)
        .filter(
            Booking.showing_id == showing_id,
            Booking.show_date == show_date,
            Booking.booking_status == "confirmed",
        )
        .all()
    )

    available = [s for s in all_seats if s.seat_id not in booked_seat_ids]

    if len(available) < num_tickets:
        raise BookingError(
            f"Only {len(available)} {seat_type} seat(s) available, but {num_tickets} requested"
        )

    return available[:num_tickets]


# Create booking
def create_booking(db: Session, data: dict, booked_by: int) -> Booking:
    """
    Create a full booking: validate rules, assign seats, calculate cost.

    Args:
        data: {
            "showing_id": int,
            "show_date": date,
            "customer_name": str,
            "customer_phone": str | None,
            "customer_email": str | None,
            "seat_type": str,
            "num_tickets": int,
            "payment_simulated": bool
        }
        booked_by: user_id of the staff member processing the booking

    Returns:
        The created Booking ORM object with booked_seats loaded.
    """
    showing_id = data["showing_id"]
    show_date = data["show_date"]
    seat_type = data["seat_type"]
    num_tickets = data["num_tickets"]
    today = date.today()

    # Rule: show_date must be today or in the future
    if show_date < today:
        raise BookingError("Cannot book for a past date")

    # Rule: bookings up to 7 days in advance
    days_ahead = (show_date - today).days
    if days_ahead > 7:
        raise BookingError("Bookings can only be made up to 7 days in advance")

    # Load showing
    showing = (
        db.query(Showing)
        .options(joinedload(Showing.listing).joinedload(Listing.screen).joinedload(Screen.cinema))
        .filter(Showing.showing_id == showing_id, Showing.is_active == True)  # noqa: E712
        .first()
    )
    if not showing:
        raise NotFoundError("Showing")

    listing = showing.listing
    if not listing.is_active:
        raise BookingError("This listing is no longer active")

    if not (listing.start_date <= show_date <= listing.end_date):
        raise BookingError("Selected date is outside the listing window")

    screen = listing.screen

    # Get seats — use staff-selected IDs if provided, otherwise auto-assign
    seat_ids = data.get("seat_ids")
    if seat_ids:
        if len(seat_ids) != num_tickets:
            raise BookingError(
                f"Selected {len(seat_ids)} seat(s) but num_tickets is {num_tickets}"
            )
        seats = _get_seats_by_ids(
            db, screen.screen_id, showing_id, show_date, seat_type, seat_ids
        )
    else:
        seats = _find_available_seats(
            db, screen.screen_id, showing_id, show_date, seat_type, num_tickets
        )

    # Calculate price
    unit_price = get_price_for_showing(db, showing, seat_type)
    total_cost = round(unit_price * num_tickets, 2)

    # Generate reference
    reference = _generate_booking_reference(db)

    # Create booking
    booking = Booking(
        booking_reference=reference,
        showing_id=showing_id,
        show_date=show_date,
        booked_by=booked_by,
        customer_name=data["customer_name"],
        customer_phone=data.get("customer_phone"),
        customer_email=data.get("customer_email"),
        num_tickets=num_tickets,
        total_cost=total_cost,
        booking_status="confirmed",
        payment_simulated=data.get("payment_simulated", False),
    )
    db.add(booking)
    db.flush()

    # Create booked seat records
    for seat in seats:
        bs = BookedSeat(
            booking_id=booking.booking_id,
            seat_id=seat.seat_id,
            unit_price=unit_price,
        )
        db.add(bs)

    db.commit()
    db.refresh(booking)
    return booking


# Cancel booking
def cancel_booking(db: Session, booking_reference: str) -> Booking:
    """
    Cancel a booking.

    Rules:
      - Cannot cancel an already-cancelled booking
      - Cannot cancel on the day of the show (show_date must be > today)
      - Cancellation fee = 50% of total_cost
      - Refund = total_cost - cancellation_fee
    """
    booking = (
        db.query(Booking)
        .options(joinedload(Booking.booked_seats))
        .filter(Booking.booking_reference == booking_reference)
        .first()
    )
    if not booking:
        raise NotFoundError("Booking")

    if booking.booking_status == "cancelled":
        raise BookingError("This booking has already been cancelled")

    today = date.today()
    if booking.show_date <= today:
        raise BookingError(
            "Cancellation is not allowed on the day of the show or after. "
            "No refund for missed shows."
        )

    # Calculate fees
    total = float(booking.total_cost)
    fee = round(total * 0.50, 2)
    refund = round(total - fee, 2)

    booking.booking_status = "cancelled"
    booking.cancelled_at = datetime.now(timezone.utc)
    booking.cancellation_fee = fee
    booking.refund_amount = refund

    db.commit()
    db.refresh(booking)
    return booking


# Lookup
def get_booking_by_reference(db: Session, reference: str) -> Booking:
    """Look up a booking by its reference code."""
    booking = (
        db.query(Booking)
        .options(
            joinedload(Booking.booked_seats).joinedload(BookedSeat.seat),
            joinedload(Booking.showing).joinedload(Showing.listing).joinedload(Listing.film),
            joinedload(Booking.showing)
            .joinedload(Showing.listing)
            .joinedload(Listing.screen)
            .joinedload(Screen.cinema),
        )
        .filter(Booking.booking_reference == reference)
        .first()
    )
    if not booking:
        raise NotFoundError("Booking")
    return booking


def get_bookings_for_showing(db: Session, showing_id: int, show_date: date) -> list[Booking]:
    """All confirmed bookings for a particular showing on a date."""
    return (
        db.query(Booking)
        .options(joinedload(Booking.booked_seats).joinedload(BookedSeat.seat))
        .filter(
            Booking.showing_id == showing_id,
            Booking.show_date == show_date,
            Booking.booking_status == "confirmed",
        )
        .all()
    )


def search_bookings(
    db: Session,
    cinema_id: Optional[int] = None,
    customer_name: Optional[str] = None,
    customer_email: Optional[str] = None,
    show_date: Optional[date] = None,
    status: Optional[str] = None,
    customer_phone: Optional[str] = None,
    booked_by: Optional[int] = None,
    booking_date: Optional[date] = None,
) -> list[Booking]:
    """Flexible booking search for staff."""
    query = (
        db.query(Booking)
        .join(Showing, Booking.showing_id == Showing.showing_id)
        .join(Listing, Showing.listing_id == Listing.listing_id)
        .join(Screen, Listing.screen_id == Screen.screen_id)
        .options(
            joinedload(Booking.booked_seats).joinedload(BookedSeat.seat),
            joinedload(Booking.showing).joinedload(Showing.listing).joinedload(Listing.film),
            joinedload(Booking.showing).joinedload(Showing.listing).joinedload(Listing.screen),
        )
    )

    if cinema_id:
        query = query.filter(Screen.cinema_id == cinema_id)
    if customer_name:
        query = query.filter(Booking.customer_name.ilike(f"%{customer_name}%"))
    if customer_email:
        query = query.filter(Booking.customer_email.ilike(f"%{customer_email}%"))
    if customer_phone:
        query = query.filter(Booking.customer_phone.ilike(f"%{customer_phone}%"))
    if show_date:
        query = query.filter(Booking.show_date == show_date)
    if booking_date:
        query = query.filter(func.date(Booking.booking_date) == booking_date)
    if status:
        query = query.filter(Booking.booking_status == status)
    if booked_by:
        query = query.filter(Booking.booked_by == booked_by)

    return query.order_by(Booking.booking_date.desc()).all()
