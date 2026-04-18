"""
backend/models/__init__.py
Import all models here so that Base.metadata knows about every table.
"""

from backend.models.booking import BasePrice, BookedSeat, Booking  # noqa: F401
from backend.models.cinema import Cinema, City, Screen, Seat  # noqa: F401
from backend.models.film import Film, Listing, Showing  # noqa: F401
from backend.models.user import Role, User  # noqa: F401
