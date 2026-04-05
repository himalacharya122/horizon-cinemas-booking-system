"""
backend/models/__init__.py
Import all models here so that Base.metadata knows about every table.
"""

from backend.models.cinema import City, Cinema, Screen, Seat        # noqa: F401
from backend.models.user import Role, User                          # noqa: F401
from backend.models.film import Film, Listing, Showing              # noqa: F401
from backend.models.booking import BasePrice, Booking, BookedSeat   # noqa: F401