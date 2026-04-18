"""
backend/schemas/cinema.py
Pydantic models for cinema, city, screen, and seat data.
"""

from typing import Optional

from pydantic import BaseModel, Field


# City
class CityOut(BaseModel):
    city_id: int
    city_name: str

    model_config = {"from_attributes": True}


class CityCreate(BaseModel):
    city_name: str = Field(..., min_length=1, max_length=50)


# Screen
class ScreenOut(BaseModel):
    screen_id: int
    cinema_id: int
    screen_number: int
    total_seats: int
    lower_hall_seats: int
    upper_gallery_seats: int
    vip_seats: int
    is_active: bool

    model_config = {"from_attributes": True}


class ScreenCreate(BaseModel):
    screen_number: int = Field(..., ge=1, le=6)
    total_seats: int = Field(..., ge=50, le=120)
    lower_hall_seats: int = Field(..., ge=1)
    upper_gallery_seats: int = Field(..., ge=1)
    vip_seats: int = Field(default=0, ge=0, le=10)


# Cinema
class CinemaOut(BaseModel):
    cinema_id: int
    city_id: int
    city_name: str = ""
    cinema_name: str
    address: str
    phone: Optional[str] = None
    total_screens: int
    is_active: bool
    screens: list[ScreenOut] = []

    model_config = {"from_attributes": True}


class CinemaCreate(BaseModel):
    city_id: Optional[int] = None  # use existing city
    new_city_name: Optional[str] = None  # or create a new city
    cinema_name: str = Field(..., min_length=1, max_length=150)
    address: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)
    screens: list[ScreenCreate] = Field(default_factory=list)


class CinemaUpdate(BaseModel):
    cinema_name: Optional[str] = Field(default=None, max_length=150)
    address: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)
    is_active: Optional[bool] = None


# Seat availability summary
class SeatAvailability(BaseModel):
    seat_type: str
    total: int
    booked: int
    available: int


# Base Price
class BasePriceOut(BaseModel):
    city_id: int
    show_period: str
    lower_hall_price: float
    upper_gallery_price: float
    vip_price: float

    model_config = {"from_attributes": True}


class BasePriceCreate(BaseModel):
    city_id: int
    show_period: str = Field(..., pattern="^(morning|afternoon|evening)$")
    lower_hall_price: float = Field(..., gt=0)
