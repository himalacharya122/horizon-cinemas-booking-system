"""
backend/schemas/film.py
Pydantic models for film, listing, and showing data.
"""

from datetime import date, time
from pydantic import BaseModel, Field
from typing import Optional


# Film
class FilmOut(BaseModel):
    film_id: int
    title: str
    description: Optional[str] = None
    genre: str
    age_rating: str
    duration_mins: int
    duration_display: str = ""
    release_date: Optional[date] = None
    imdb_rating: Optional[float] = None
    cast_list: Optional[str] = None
    director: Optional[str] = None
    poster_url: Optional[str] = None
    is_active: bool

    model_config = {"from_attributes": True}


class FilmCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    genre: str = Field(..., min_length=1)
    age_rating: str = Field(..., min_length=1, max_length=10)
    duration_mins: int = Field(..., gt=0)
    release_date: Optional[date] = None
    imdb_rating: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    cast_list: Optional[str] = None
    director: Optional[str] = None
    poster_url: Optional[str] = None


class FilmUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    genre: Optional[str] = None
    age_rating: Optional[str] = Field(default=None, max_length=10)
    duration_mins: Optional[int] = Field(default=None, gt=0)
    release_date: Optional[date] = None
    imdb_rating: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    cast_list: Optional[str] = None
    director: Optional[str] = None
    poster_url: Optional[str] = None
    is_active: Optional[bool] = None


# Showing
class ShowingOut(BaseModel):
    showing_id: int
    listing_id: int
    show_time: time
    show_type: str
    is_active: bool

    model_config = {"from_attributes": True}


class ShowingCreate(BaseModel):
    show_time: time
    show_type: str = Field(..., pattern="^(morning|afternoon|evening)$")


# Listing
class ListingOut(BaseModel):
    listing_id: int
    film_id: int
    film_title: str = ""
    screen_id: int
    screen_number: int = 0
    cinema_id: int = 0
    cinema_name: str = ""
    city_name: str = ""
    start_date: date
    end_date: date
    is_active: bool
    showings: list[ShowingOut] = []

    model_config = {"from_attributes": True}


class ListingCreate(BaseModel):
    film_id: int
    screen_id: int
    start_date: date
    end_date: date
    showings: list[ShowingCreate] = Field(default_factory=list, min_length=1, max_length=3)


class ListingUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None


# listing view for the film listing GUI
class ShowingDetail(BaseModel):
    showing_id: int
    show_time: time
    show_type: str
    lower_hall_price: float
    upper_gallery_price: float
    vip_price: float


class FilmListingItem(BaseModel):
    """One film card in the listings window — includes showings + prices."""
    film_id: int
    title: str
    description: Optional[str] = None
    genre: str
    age_rating: str
    duration_mins: int
    duration_display: str = ""
    release_date: Optional[date] = None
    imdb_rating: Optional[float] = None
    cast_list: Optional[str] = None
    director: Optional[str] = None
    poster_url: Optional[str] = None
    listing_id: int
    screen_id: int
    screen_number: int
    start_date: date
    end_date: date
    showings: list[ShowingDetail] = []