# ============================================
# Author: Himal Acharya
# Student ID: 22085619
# Last Edited: 2026-04-25
# ============================================

"""
backend/services/report_service.py
Admin report queries: revenue, top films, staff booking counts, etc.
"""

from typing import Optional

from sqlalchemy import case, desc, extract, func  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from backend.models.booking import Booking
from backend.models.cinema import Cinema, City, Screen
from backend.models.film import Film, Listing, Showing
from backend.models.user import User


def monthly_revenue_by_cinema(
    db: Session, year: int, month: int, cinema_id: Optional[int] = None
) -> list[dict]:
    """Total monthly revenue per cinema."""
    query = (
        db.query(
            City.city_name,
            Cinema.cinema_name,
            func.count(Booking.booking_id).label("total_bookings"),
            func.coalesce(func.sum(Booking.total_cost), 0).label("total_revenue"),
            func.sum(case((Booking.booking_status == "cancelled", 1), else_=0)).label(
                "cancellations"
            ),
            func.coalesce(func.sum(Booking.cancellation_fee), 0).label("cancellation_fees"),
        )
        .join(Showing, Booking.showing_id == Showing.showing_id)
        .join(Listing, Showing.listing_id == Listing.listing_id)
        .join(Screen, Listing.screen_id == Screen.screen_id)
        .join(Cinema, Screen.cinema_id == Cinema.cinema_id)
        .join(City, Cinema.city_id == City.city_id)
        .filter(
            extract("year", Booking.booking_date) == year,
            extract("month", Booking.booking_date) == month,
        )
    )

    if cinema_id:
        query = query.filter(Cinema.cinema_id == cinema_id)

    rows = query.group_by(City.city_name, Cinema.cinema_name).order_by(desc("total_revenue")).all()

    return [
        {
            "city_name": r.city_name,
            "cinema_name": r.cinema_name,
            "total_bookings": r.total_bookings,
            "total_revenue": float(r.total_revenue),
            "cancellations": int(r.cancellations),
            "cancellation_fees": float(r.cancellation_fees),
        }
        for r in rows
    ]


def bookings_per_listing(db: Session, cinema_id: Optional[int] = None) -> list[dict]:
    """Number of confirmed bookings per active listing."""
    query = (
        db.query(
            Film.title,
            Screen.screen_number,
            Cinema.cinema_name,
            Listing.start_date,
            Listing.end_date,
            func.count(Booking.booking_id).label("booking_count"),
            func.coalesce(func.sum(Booking.num_tickets), 0).label("tickets_sold"),
        )
        .join(Showing, Booking.showing_id == Showing.showing_id)
        .join(Listing, Showing.listing_id == Listing.listing_id)
        .join(Film, Listing.film_id == Film.film_id)
        .join(Screen, Listing.screen_id == Screen.screen_id)
        .join(Cinema, Screen.cinema_id == Cinema.cinema_id)
        .filter(Booking.booking_status == "confirmed")
    )

    if cinema_id:
        query = query.filter(Cinema.cinema_id == cinema_id)

    rows = (
        query.group_by(
            Film.title,
            Screen.screen_number,
            Cinema.cinema_name,
            Listing.start_date,
            Listing.end_date,
        )
        .order_by(desc("booking_count"))
        .all()
    )

    return [
        {
            "film_title": r.title,
            "screen_number": r.screen_number,
            "cinema_name": r.cinema_name,
            "start_date": r.start_date.isoformat(),
            "end_date": r.end_date.isoformat(),
            "booking_count": r.booking_count,
            "tickets_sold": int(r.tickets_sold),
        }
        for r in rows
    ]


def top_revenue_films(db: Session, year: int, month: int, limit: int = 10) -> list[dict]:
    """Top revenue-generating films for a given month."""
    rows = (
        db.query(
            Film.title,
            func.coalesce(func.sum(Booking.total_cost), 0).label("revenue"),
            func.count(Booking.booking_id).label("bookings"),
        )
        .join(Showing, Booking.showing_id == Showing.showing_id)
        .join(Listing, Showing.listing_id == Listing.listing_id)
        .join(Film, Listing.film_id == Film.film_id)
        .filter(
            Booking.booking_status == "confirmed",
            extract("year", Booking.booking_date) == year,
            extract("month", Booking.booking_date) == month,
        )
        .group_by(Film.title)
        .order_by(desc("revenue"))
        .limit(limit)
        .all()
    )

    return [
        {"film_title": r.title, "revenue": float(r.revenue), "bookings": r.bookings} for r in rows
    ]


def staff_booking_report(
    db: Session, year: int, month: int, cinema_id: Optional[int] = None
) -> list[dict]:
    """Monthly list of staff members sorted by number of bookings (descending)."""
    query = (
        db.query(
            User.user_id,
            User.username,
            User.first_name,
            User.last_name,
            Cinema.cinema_name,
            func.count(Booking.booking_id).label("total_bookings"),
            func.coalesce(func.sum(Booking.total_cost), 0).label("total_revenue"),
        )
        .join(User, Booking.booked_by == User.user_id)
        .join(Cinema, User.cinema_id == Cinema.cinema_id)
        .filter(
            extract("year", Booking.booking_date) == year,
            extract("month", Booking.booking_date) == month,
        )
    )

    if cinema_id:
        query = query.filter(Cinema.cinema_id == cinema_id)

    rows = (
        query.group_by(
            User.user_id,
            User.username,
            User.first_name,
            User.last_name,
            Cinema.cinema_name,
        )
        .order_by(desc("total_bookings"))
        .all()
    )

    return [
        {
            "user_id": r.user_id,
            "username": r.username,
            "staff_name": f"{r.first_name} {r.last_name}",
            "cinema_name": r.cinema_name,
            "total_bookings": r.total_bookings,
            "total_revenue": float(r.total_revenue),
        }
        for r in rows
    ]


def occupancy_report(
    db: Session, year: int, month: int, cinema_id: Optional[int] = None
) -> list[dict]:
    """
    Screen occupancy report: for each screen, percentage of seats sold
    vs total capacity for the month.
    """
    # Total booked seats per screen for confirmed bookings in the month
    query = (
        db.query(
            Cinema.cinema_name,
            Screen.screen_number,
            Screen.total_seats,
            func.count(func.distinct(Booking.booking_id)).label("total_bookings"),
            func.coalesce(func.sum(Booking.num_tickets), 0).label("tickets_sold"),
        )
        .join(Showing, Booking.showing_id == Showing.showing_id)
        .join(Listing, Showing.listing_id == Listing.listing_id)
        .join(Screen, Listing.screen_id == Screen.screen_id)
        .join(Cinema, Screen.cinema_id == Cinema.cinema_id)
        .filter(
            Booking.booking_status == "confirmed",
            extract("year", Booking.booking_date) == year,
            extract("month", Booking.booking_date) == month,
        )
    )

    if cinema_id:
        query = query.filter(Cinema.cinema_id == cinema_id)

    rows = (
        query.group_by(
            Cinema.cinema_name,
            Screen.screen_number,
            Screen.total_seats,
        )
        .order_by(Cinema.cinema_name, Screen.screen_number)
        .all()
    )

    results = []
    for r in rows:
        total_capacity = r.total_seats  # per showing
        tickets = int(r.tickets_sold)
        bookings = r.total_bookings
        # Approximate occupancy: tickets sold / (capacity * number of bookings)
        # Simpler: just show raw numbers and a percentage if capacity known
        occ_pct = (
            round((tickets / (total_capacity * max(bookings, 1))) * 100, 1) if total_capacity else 0
        )
        results.append(
            {
                "cinema_name": r.cinema_name,
                "screen_number": r.screen_number,
                "total_seats": r.total_seats,
                "total_bookings": bookings,
                "tickets_sold": tickets,
                "occupancy_pct": min(occ_pct, 100.0),
            }
        )

    return results


def cancellation_rate_report(
    db: Session, year: int, month: int, cinema_id: Optional[int] = None
) -> list[dict]:
    """
    Cancellation rate per cinema for a given month.
    Shows total bookings, cancelled count, cancellation rate %, fees collected.
    """
    query = (
        db.query(
            Cinema.cinema_name,
            func.count(Booking.booking_id).label("total_bookings"),
            func.sum(case((Booking.booking_status == "cancelled", 1), else_=0)).label("cancelled"),
            func.coalesce(
                func.sum(
                    case(
                        (Booking.booking_status == "cancelled", Booking.cancellation_fee),
                        else_=0,
                    )
                ),
                0,
            ).label("fees_collected"),
            func.coalesce(
                func.sum(
                    case(
                        (Booking.booking_status == "cancelled", Booking.refund_amount),
                        else_=0,
                    )
                ),
                0,
            ).label("total_refunded"),
        )
        .join(Showing, Booking.showing_id == Showing.showing_id)
        .join(Listing, Showing.listing_id == Listing.listing_id)
        .join(Screen, Listing.screen_id == Screen.screen_id)
        .join(Cinema, Screen.cinema_id == Cinema.cinema_id)
        .filter(
            extract("year", Booking.booking_date) == year,
            extract("month", Booking.booking_date) == month,
        )
    )

    if cinema_id:
        query = query.filter(Cinema.cinema_id == cinema_id)

    rows = query.group_by(Cinema.cinema_name).order_by(desc("cancelled")).all()

    return [
        {
            "cinema_name": r.cinema_name,
            "total_bookings": r.total_bookings,
            "cancelled": int(r.cancelled),
            "cancellation_rate": round((int(r.cancelled) / r.total_bookings * 100), 1)
            if r.total_bookings > 0
            else 0.0,
            "fees_collected": float(r.fees_collected),
            "total_refunded": float(r.total_refunded),
        }
        for r in rows
    ]
