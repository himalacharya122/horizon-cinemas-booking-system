# ============================================
# Author: Himal Acharya
# Student ID: 22085619
# Last Edited: 2026-04-25
# ============================================

"""
backend/api/v1/endpoints/cinemas.py

Cinema, screen, city, and base price management.

IMPORTANT: Static path segments (/cities, /prices) are registered BEFORE
parameterised ones (/{cinema_id}) so FastAPI matches them correctly.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session  # type: ignore

from backend.api.deps import get_current_user, require_role
from backend.core.database import get_db
from backend.core.exceptions import HCBSException
from backend.schemas.cinema import (
    BasePriceCreate,
    BasePriceOut,
    CinemaCreate,
    CinemaOut,
    CinemaUpdate,
    CityCreate,
    CityOut,
    ScreenCreate,
    ScreenOut,
)
from backend.services import cinema_service

router = APIRouter(prefix="/cinemas", tags=["Cinemas"])


# Cities (static path — before /{cinema_id})


@router.get("/cities", response_model=list[CityOut])
def list_cities(
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    return cinema_service.get_all_cities(db)


@router.post("/cities", response_model=CityOut, status_code=201)
def create_city(
    body: CityCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("manager")),
):
    """Add a new city. (Manager only)"""
    try:
        return cinema_service.create_city(db, body.city_name)
    except HCBSException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# Base prices (static path — before /{cinema_id})


@router.get("/prices", response_model=list[BasePriceOut])
def list_prices(
    city_id: int | None = None,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    prices = cinema_service.get_base_prices(db, city_id)
    return [
        {
            "city_id": bp.city_id,
            "show_period": bp.show_period,
            "lower_hall_price": float(bp.lower_hall_price),
            "upper_gallery_price": bp.upper_gallery_price,
            "vip_price": bp.vip_price,
        }
        for bp in prices
    ]


@router.post("/prices", response_model=BasePriceOut, status_code=201)
def set_price(
    body: BasePriceCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "manager")),
):
    """Set or update a base price for a city + time period. (Admin/Manager)"""
    try:
        bp = cinema_service.set_base_price(
            db, body.city_id, body.show_period, body.lower_hall_price
        )
        return {
            "city_id": bp.city_id,
            "show_period": bp.show_period,
            "lower_hall_price": float(bp.lower_hall_price),
            "upper_gallery_price": bp.upper_gallery_price,
            "vip_price": bp.vip_price,
        }
    except HCBSException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# Cinemas (list + create — no path param)


@router.get("", response_model=list[CinemaOut])
def list_cinemas(
    city_id: int | None = None,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    cinemas = cinema_service.get_all_cinemas(db, city_id)
    return [_serialise_cinema(c) for c in cinemas]


@router.post("", response_model=CinemaOut, status_code=201)
def create_cinema(
    body: CinemaCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("manager")),
):
    """
    Add a new cinema with optional screens. (Manager only)
    Can create in an existing city (city_id) or a new city (new_city_name).
    """
    try:
        data = body.model_dump()
        data["screens"] = [s.model_dump() for s in body.screens]
        cinema = cinema_service.create_cinema(db, data)
        return _serialise_cinema(cinema)
    except HCBSException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# Single cinema by ID (parameterised — AFTER static routes)


@router.get("/{cinema_id}", response_model=CinemaOut)
def get_cinema(
    cinema_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    try:
        cinema = cinema_service.get_cinema(db, cinema_id)
        return _serialise_cinema(cinema)
    except HCBSException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.patch("/{cinema_id}", response_model=CinemaOut)
def update_cinema(
    cinema_id: int,
    body: CinemaUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "manager")),
):
    try:
        cinema = cinema_service.update_cinema(db, cinema_id, body.model_dump(exclude_unset=True))
        return _serialise_cinema(cinema)
    except HCBSException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# Screens


@router.post("/{cinema_id}/screens", response_model=ScreenOut, status_code=201)
def add_screen(
    cinema_id: int,
    body: ScreenCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("manager")),
):
    """Add a new screen to a cinema. (Manager only)"""
    try:
        return cinema_service.add_screen_to_cinema(db, cinema_id, body.model_dump())
    except HCBSException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# Helpers


def _serialise_cinema(cinema) -> dict:
    return {
        "cinema_id": cinema.cinema_id,
        "city_id": cinema.city_id,
        "city_name": cinema.city.city_name if cinema.city else "",
        "cinema_name": cinema.cinema_name,
        "address": cinema.address,
        "phone": cinema.phone,
        "total_screens": cinema.total_screens,
        "is_active": cinema.is_active,
        "screens": [
            {
                "screen_id": s.screen_id,
                "cinema_id": s.cinema_id,
                "screen_number": s.screen_number,
                "total_seats": s.total_seats,
                "lower_hall_seats": s.lower_hall_seats,
                "upper_gallery_seats": s.upper_gallery_seats,
                "vip_seats": s.vip_seats,
                "is_active": s.is_active,
            }
            for s in cinema.screens
        ],
    }
