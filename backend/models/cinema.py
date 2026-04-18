"""
backend/models/cinema.py
ORM models for: City, Cinema, Screen, Seat
"""

from sqlalchemy import (  # type: ignore
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import relationship  # type: ignore

from backend.core.database import Base


class City(Base):
    __tablename__ = "cities"

    city_id = Column(Integer, primary_key=True, autoincrement=True)
    city_name = Column(String(50), nullable=False, unique=True)

    # Relationships
    cinemas = relationship("Cinema", back_populates="city", lazy="selectin")
    base_prices = relationship("BasePrice", back_populates="city", lazy="selectin")

    def __repr__(self):
        return f"<City(city_id={self.city_id}, city_name='{self.city_name}')>"


class Cinema(Base):
    __tablename__ = "cinemas"

    cinema_id = Column(Integer, primary_key=True, autoincrement=True)
    city_id = Column(
        Integer, ForeignKey("cities.city_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    cinema_name = Column(String(150), nullable=False)
    address = Column(String(255), nullable=False)
    phone = Column(String(20))
    total_screens = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    # Relationships
    city = relationship("City", back_populates="cinemas")
    screens = relationship(
        "Screen", back_populates="cinema", lazy="selectin", cascade="all, delete-orphan"
    )
    users = relationship("User", back_populates="cinema", lazy="selectin")

    def __repr__(self):
        return f"<Cinema(cinema_id={self.cinema_id}, cinema_name='{self.cinema_name}')>"


class Screen(Base):
    __tablename__ = "screens"
    __table_args__ = (
        UniqueConstraint("cinema_id", "screen_number", name="uq_screen"),
        CheckConstraint("screen_number BETWEEN 1 AND 6", name="chk_screen_number"),
        CheckConstraint("total_seats BETWEEN 50 AND 120", name="chk_total_seats"),
        CheckConstraint("vip_seats <= 10", name="chk_vip_seats"),
    )

    screen_id = Column(Integer, primary_key=True, autoincrement=True)
    cinema_id = Column(
        Integer, ForeignKey("cinemas.cinema_id", ondelete="CASCADE"), nullable=False, index=True
    )
    screen_number = Column(Integer, nullable=False)
    total_seats = Column(Integer, nullable=False)
    lower_hall_seats = Column(Integer, nullable=False)
    upper_gallery_seats = Column(Integer, nullable=False)
    vip_seats = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    cinema = relationship("Cinema", back_populates="screens")
    seats = relationship(
        "Seat", back_populates="screen", lazy="selectin", cascade="all, delete-orphan"
    )
    listings = relationship("Listing", back_populates="screen", lazy="selectin")

    def __repr__(self):
        return (
            f"<Screen(screen_id={self.screen_id}, cinema={self.cinema_id}, "
            f"number={self.screen_number})>"
        )


class Seat(Base):
    __tablename__ = "seats"
    __table_args__ = (UniqueConstraint("screen_id", "seat_number", name="uq_seat"),)

    seat_id = Column(Integer, primary_key=True, autoincrement=True)
    screen_id = Column(Integer, ForeignKey("screens.screen_id", ondelete="CASCADE"), nullable=False)
    seat_number = Column(String(10), nullable=False)
    seat_type = Column(String(15), nullable=False)  # 'lower_hall', 'upper_gallery', 'vip'
    row_label = Column(String(5), nullable=False)

    # Relationships
    screen = relationship("Screen", back_populates="seats")
    booked_seats = relationship("BookedSeat", back_populates="seat", lazy="selectin")

    def __repr__(self):
        return (
            f"<Seat(seat_id={self.seat_id}, number='{self.seat_number}', type='{self.seat_type}')>"
        )
