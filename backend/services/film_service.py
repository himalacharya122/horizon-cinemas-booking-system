"""
backend/services/film_service.py
Business logic for films, listings, and showings.
"""

from datetime import date
from typing import Optional

from sqlalchemy.orm import Session, joinedload  # type: ignore

from backend.core.exceptions import NotFoundError, ValidationError
from backend.models.booking import BasePrice
from backend.models.cinema import Cinema, Screen
from backend.models.film import Film, Listing, Showing


# Films
def get_all_films(db: Session, active_only: bool = True) -> list[Film]:
    """Return all films, optionally filtered to active only."""
    query = db.query(Film)
    if active_only:
        query = query.filter(Film.is_active)
    return query.order_by(Film.title).all()


def get_film(db: Session, film_id: int) -> Film:
    film = db.query(Film).filter(Film.film_id == film_id).first()
    if not film:
        raise NotFoundError("Film")
    return film


def create_film(db: Session, data: dict) -> Film:
    """Create a new film in the shared catalogue."""
    film = Film(**data)
    db.add(film)
    db.commit()
    db.refresh(film)
    return film


def update_film(db: Session, film_id: int, data: dict) -> Film:
    film = get_film(db, film_id)
    for key, value in data.items():
        if value is not None:
            setattr(film, key, value)
    db.commit()
    db.refresh(film)
    return film


def delete_film(db: Session, film_id: int) -> Film:
    """Soft-delete: sets is_active = False."""
    film = get_film(db, film_id)
    film.is_active = False
    db.commit()
    db.refresh(film)
    return film


# Listings
def get_listings_for_cinema(
    db: Session,
    cinema_id: int,
    target_date: Optional[date] = None,
    active_only: bool = True,
) -> list[Listing]:
    """
    Return listings for a given cinema, optionally filtered by date.
    Eagerly loads film, screen, and showings.
    """
    query = (
        db.query(Listing)
        .join(Screen, Listing.screen_id == Screen.screen_id)
        .options(
            joinedload(Listing.film),
            joinedload(Listing.screen).joinedload(Screen.cinema),
            joinedload(Listing.showings),
        )
        .filter(Screen.cinema_id == cinema_id)
    )

    if active_only:
        query = query.filter(Listing.is_active, Film.is_active)
        query = query.join(Film, Listing.film_id == Film.film_id)

    if target_date:
        query = query.filter(
            Listing.start_date <= target_date,
            Listing.end_date >= target_date,
        )

    return query.order_by(Listing.start_date).all()


def get_all_listings(
    db: Session,
    target_date: Optional[date] = None,
    city_id: Optional[int] = None,
    active_only: bool = True,
) -> list[Listing]:
    """
    Return listings across all cinemas — used by admins who can browse
    listings from any HC cinema.
    """
    query = (
        db.query(Listing)
        .join(Screen, Listing.screen_id == Screen.screen_id)
        .join(Cinema, Screen.cinema_id == Cinema.cinema_id)
        .options(
            joinedload(Listing.film),
            joinedload(Listing.screen).joinedload(Screen.cinema).joinedload(Cinema.city),
            joinedload(Listing.showings),
        )
    )

    if active_only:
        query = query.join(Film, Listing.film_id == Film.film_id).filter(
            Listing.is_active, Film.is_active
        )

    if target_date:
        query = query.filter(
            Listing.start_date <= target_date,
            Listing.end_date >= target_date,
        )

    if city_id:
        query = query.filter(Cinema.city_id == city_id)

    return query.order_by(Cinema.cinema_name, Listing.start_date).all()


def get_listing(db: Session, listing_id: int) -> Listing:
    listing = (
        db.query(Listing)
        .options(
            joinedload(Listing.film),
            joinedload(Listing.screen).joinedload(Screen.cinema),
            joinedload(Listing.showings),
        )
        .filter(Listing.listing_id == listing_id)
        .first()
    )
    if not listing:
        raise NotFoundError("Listing")
    return listing


def create_listing(db: Session, data: dict, showings_data: list[dict], created_by: int) -> Listing:
    """
    Create a listing with its showings.
    Validates: end >= start, screen exists, no overlapping listing on the same screen.
    """
    start = data["start_date"]
    end = data["end_date"]

    if end < start:
        raise ValidationError("End date cannot be before start date")

    # Check screen exists
    screen = db.query(Screen).filter(Screen.screen_id == data["screen_id"]).first()
    if not screen:
        raise NotFoundError("Screen")

    # Check film exists
    film = db.query(Film).filter(Film.film_id == data["film_id"]).first()
    if not film:
        raise NotFoundError("Film")

    # Check for overlapping active listings on this screen
    overlap = (
        db.query(Listing)
        .filter(
            Listing.screen_id == data["screen_id"],
            Listing.is_active,
            Listing.start_date <= end,
            Listing.end_date >= start,
        )
        .first()
    )
    if overlap:
        raise ValidationError(
            f"Screen {screen.screen_number} already has an active listing "
            f"({overlap.listing_id}) overlapping these dates"
        )

    listing = Listing(
        film_id=data["film_id"],
        screen_id=data["screen_id"],
        start_date=start,
        end_date=end,
        created_by=created_by,
    )
    db.add(listing)
    db.flush()  # get listing_id

    for s in showings_data:
        showing = Showing(
            listing_id=listing.listing_id,
            show_time=s["show_time"],
            show_type=s["show_type"],
        )
        db.add(showing)

    db.commit()
    db.refresh(listing)
    return listing


def update_listing(db: Session, listing_id: int, data: dict) -> Listing:
    listing = get_listing(db, listing_id)
    for key, value in data.items():
        if value is not None:
            setattr(listing, key, value)
    db.commit()
    db.refresh(listing)
    return listing


def delete_listing(db: Session, listing_id: int) -> Listing:
    """Soft-delete a listing and its showings."""
    listing = get_listing(db, listing_id)
    listing.is_active = False
    for showing in listing.showings:
        showing.is_active = False
    db.commit()
    db.refresh(listing)
    return listing


# Efilm listing view (for GUI)
def get_film_listings_for_display(
    db: Session,
    cinema_id: int,
    target_date: date,
) -> list[dict]:
    """
    Build the data needed for the Film Listing GUI:
    Each film card with its showings and calculated prices.
    """
    listings = get_listings_for_cinema(db, cinema_id, target_date)
    result = []

    for listing in listings:
        screen = listing.screen
        cinema = screen.cinema
        city_id = cinema.city_id

        active_showings = [s for s in listing.showings if s.is_active]
        if not active_showings:
            continue

        showing_details = []
        for s in active_showings:
            # Look up base price for this city + show period
            bp = (
                db.query(BasePrice)
                .filter(BasePrice.city_id == city_id, BasePrice.show_period == s.show_type)
                .first()
            )
            if not bp:
                continue

            showing_details.append(
                {
                    "showing_id": s.showing_id,
                    "show_time": s.show_time,
                    "show_type": s.show_type,
                    "lower_hall_price": float(bp.lower_hall_price),
                    "upper_gallery_price": bp.upper_gallery_price,
                    "vip_price": bp.vip_price,
                }
            )

        film = listing.film
        result.append(
            {
                "film_id": film.film_id,
                "title": film.title,
                "description": film.description,
                "genre": film.genre,
                "age_rating": film.age_rating,
                "duration_mins": film.duration_mins,
                "duration_display": film.duration_display,
                "release_date": film.release_date,
                "imdb_rating": float(film.imdb_rating) if film.imdb_rating else None,
                "cast_list": film.cast_list,
                "director": film.director,
                "poster_url": film.poster_url,
                "listing_id": listing.listing_id,
                "screen_id": screen.screen_id,
                "screen_number": screen.screen_number,
                "start_date": listing.start_date,
                "end_date": listing.end_date,
                "showings": showing_details,
            }
        )

    return result
