# ============================================
# Author: Himal Acharya
# Student ID: 22085619
# Last Edited: 2026-04-25
# ============================================

"""
backend/api/v1/endpoints/films.py
Film catalogue CRUD and enriched film listing view for the GUI.
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session  # type: ignore

from backend.api.deps import get_current_user, require_role
from backend.core.database import get_db
from backend.core.exceptions import HCBSException
from backend.schemas.film import (
    FilmCreate,
    FilmListingItem,
    FilmOut,
    FilmUpdate,
    ListingCreate,
    ListingOut,
    ListingUpdate,
)
from backend.services import film_service

router = APIRouter(prefix="/films", tags=["Films & Listings"])


# Film catalogue
@router.get("", response_model=list[FilmOut])
def list_films(
    active_only: bool = True,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Get all films in the catalogue."""
    return film_service.get_all_films(db, active_only)


@router.get("/{film_id}", response_model=FilmOut)
def get_film(
    film_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    try:
        return film_service.get_film(db, film_id)
    except HCBSException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("", response_model=FilmOut, status_code=201)
def create_film(
    body: FilmCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "manager")),
):
    """Add a new film to the shared catalogue. (Admin/Manager only)"""
    return film_service.create_film(db, body.model_dump())


@router.patch("/{film_id}", response_model=FilmOut)
def update_film(
    film_id: int,
    body: FilmUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "manager")),
):
    """Update film details. (Admin/Manager only)"""
    try:
        return film_service.update_film(db, film_id, body.model_dump(exclude_unset=True))
    except HCBSException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.delete("/{film_id}", response_model=FilmOut)
def delete_film(
    film_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "manager")),
):
    """Soft-delete a film. (Admin/Manager only)"""
    try:
        return film_service.delete_film(db, film_id)
    except HCBSException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# Listings
@router.get("/listings/all", response_model=list[ListingOut])
def list_all_listings(
    target_date: Optional[date] = Query(default=None),
    city_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "manager")),
):
    """
    All listings across all cinemas. (Admin/Manager only)
    Admins can browse listings from any HC cinema.
    """
    listings = film_service.get_all_listings(db, target_date, city_id)
    return _serialise_listings(listings)


@router.get("/listings/cinema/{cinema_id}", response_model=list[ListingOut])
def list_cinema_listings(
    cinema_id: int,
    target_date: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Listings for a specific cinema."""
    listings = film_service.get_listings_for_cinema(db, cinema_id, target_date)
    return _serialise_listings(listings)


@router.get("/listings/{listing_id}", response_model=ListingOut)
def get_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    try:
        listing = film_service.get_listing(db, listing_id)
        return _serialise_listing(listing)
    except HCBSException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/listings", response_model=ListingOut, status_code=201)
def create_listing(
    body: ListingCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "manager")),
):
    """Create a new listing with showings. (Admin/Manager only)"""
    try:
        showings_data = [s.model_dump() for s in body.showings]
        listing = film_service.create_listing(
            db,
            data={
                "film_id": body.film_id,
                "screen_id": body.screen_id,
                "start_date": body.start_date,
                "end_date": body.end_date,
            },
            showings_data=showings_data,
            created_by=int(user["sub"]),
        )
        return _serialise_listing(listing)
    except HCBSException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.patch("/listings/{listing_id}", response_model=ListingOut)
def update_listing(
    listing_id: int,
    body: ListingUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "manager")),
):
    try:
        listing = film_service.update_listing(db, listing_id, body.model_dump(exclude_unset=True))
        return _serialise_listing(listing)
    except HCBSException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.delete("/listings/{listing_id}", response_model=ListingOut)
def delete_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "manager")),
):
    """Soft-delete a listing and its showings. (Admin/Manager only)"""
    try:
        listing = film_service.delete_listing(db, listing_id)
        return _serialise_listing(listing)
    except HCBSException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# film listing view (for GUI)
@router.get("/display/cinema/{cinema_id}", response_model=list[FilmListingItem])
def film_listing_display(
    cinema_id: int,
    target_date: date = Query(default=None),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """
    Enriched film listing data for the Film Listing GUI window.
    Returns films with showings and calculated prices for a given cinema + date.
    """
    if target_date is None:
        target_date = date.today()
    return film_service.get_film_listings_for_display(db, cinema_id, target_date)


# Helpers
def _serialise_listing(listing) -> dict:
    """Convert a Listing ORM object to a dict matching ListingOut."""
    screen = listing.screen
    cinema = screen.cinema if screen else None
    city = cinema.city if cinema else None
    return {
        "listing_id": listing.listing_id,
        "film_id": listing.film_id,
        "film_title": listing.film.title if listing.film else "",
        "screen_id": listing.screen_id,
        "screen_number": screen.screen_number if screen else 0,
        "cinema_id": cinema.cinema_id if cinema else 0,
        "cinema_name": cinema.cinema_name if cinema else "",
        "city_name": city.city_name if city else "",
        "start_date": listing.start_date,
        "end_date": listing.end_date,
        "is_active": listing.is_active,
        "showings": [
            {
                "showing_id": s.showing_id,
                "listing_id": s.listing_id,
                "show_time": s.show_time,
                "show_type": s.show_type,
                "is_active": s.is_active,
            }
            for s in listing.showings
        ],
    }


def _serialise_listings(listings) -> list[dict]:
    return [_serialise_listing(listing) for listing in listings]
