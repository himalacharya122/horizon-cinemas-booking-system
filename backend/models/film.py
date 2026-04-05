"""
backend/models/film.py
ORM models for: Film, Listing, Showing
"""

from sqlalchemy import ( # type: ignore
    Column, Integer, String, Boolean, Text, Date, Time, Numeric,
    ForeignKey, CheckConstraint, TIMESTAMP, text
)
from sqlalchemy.orm import relationship # type: ignore
from backend.core.database import Base


class Film(Base):
    __tablename__ = "films"

    film_id       = Column(Integer, primary_key=True, autoincrement=True)
    title         = Column(String(255), nullable=False)
    description   = Column(Text)
    genre         = Column(String(20), nullable=False)   # ENUM in MySQL
    age_rating    = Column(String(10), nullable=False)
    duration_mins = Column(Integer, nullable=False)
    release_date  = Column(Date)
    imdb_rating   = Column(Numeric(3, 1))
    cast_list     = Column(Text)
    director      = Column(String(255))
    poster_url    = Column(String(500))
    is_active     = Column(Boolean, nullable=False, default=True, index=True)
    created_at    = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    # Relationships
    listings = relationship("Listing", back_populates="film", lazy="selectin")

    @property
    def duration_display(self) -> str:
        """Return human-readable duration e.g. '2h 10m'."""
        hours, mins = divmod(self.duration_mins, 60)
        return f"{hours}h {mins}m" if hours else f"{mins}m"

    def __repr__(self):
        return f"<Film(film_id={self.film_id}, title='{self.title}')>"


class Listing(Base):
    __tablename__ = "listings"
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="chk_listing_dates"),
    )

    listing_id = Column(Integer, primary_key=True, autoincrement=True)
    film_id    = Column(Integer, ForeignKey("films.film_id", ondelete="CASCADE"), nullable=False, index=True)
    screen_id  = Column(Integer, ForeignKey("screens.screen_id", ondelete="CASCADE"), nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date   = Column(Date, nullable=False)
    is_active  = Column(Boolean, nullable=False, default=True)
    created_by = Column(Integer, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    # Relationships
    film     = relationship("Film", back_populates="listings")
    screen   = relationship("Screen", back_populates="listings")
    creator  = relationship("User", foreign_keys=[created_by])
    showings = relationship("Showing", back_populates="listing", lazy="selectin", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Listing(listing_id={self.listing_id}, film={self.film_id}, screen={self.screen_id})>"


class Showing(Base):
    __tablename__ = "showings"

    showing_id = Column(Integer, primary_key=True, autoincrement=True)
    listing_id = Column(Integer, ForeignKey("listings.listing_id", ondelete="CASCADE"), nullable=False, index=True)
    show_time  = Column(Time, nullable=False)
    show_type  = Column(String(10), nullable=False)   # 'morning', 'afternoon', 'evening'
    is_active  = Column(Boolean, nullable=False, default=True)

    # Relationships
    listing  = relationship("Listing", back_populates="showings")
    bookings = relationship("Booking", back_populates="showing", lazy="selectin")

    def __repr__(self):
        return f"<Showing(showing_id={self.showing_id}, time={self.show_time}, type='{self.show_type}')>"