"""
backend/models/booking.py
ORM models for: BasePrice, Booking, BookedSeat
"""

from sqlalchemy import ( # type: ignore
    Column, Integer, String, Boolean, Date, Numeric, ForeignKey,
    CheckConstraint, UniqueConstraint, TIMESTAMP, text
)
from sqlalchemy.orm import relationship # type: ignore
from backend.core.database import Base


class BasePrice(Base):
    __tablename__ = "base_prices"
    __table_args__ = (
        UniqueConstraint("city_id", "show_period", name="uq_city_period"),
    )

    price_id         = Column(Integer, primary_key=True, autoincrement=True)
    city_id          = Column(Integer, ForeignKey("cities.city_id", ondelete="RESTRICT"), nullable=False)
    show_period      = Column(String(10), nullable=False)   # 'morning', 'afternoon', 'evening'
    lower_hall_price = Column(Numeric(6, 2), nullable=False)

    # Relationships
    city = relationship("City", back_populates="base_prices")

    @property
    def upper_gallery_price(self) -> float:
        """Lower hall * 1.20"""
        return round(float(self.lower_hall_price) * 1.20, 2)

    @property
    def vip_price(self) -> float:
        """Lower hall * 1.20 * 1.20"""
        return round(float(self.lower_hall_price) * 1.20 * 1.20, 2)

    def price_for_seat_type(self, seat_type: str) -> float:
        """Return the correct price for a given seat type."""
        if seat_type == "lower_hall":
            return float(self.lower_hall_price)
        elif seat_type == "upper_gallery":
            return self.upper_gallery_price
        elif seat_type == "vip":
            return self.vip_price
        raise ValueError(f"Unknown seat type: {seat_type}")

    def __repr__(self):
        return f"<BasePrice(city={self.city_id}, period='{self.show_period}', lower=£{self.lower_hall_price})>"


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("show_date <= DATE(booking_date) + INTERVAL 7 DAY", name="chk_advance_booking"),
        CheckConstraint("show_date >= DATE(booking_date)", name="chk_show_date_valid"),
    )

    booking_id        = Column(Integer, primary_key=True, autoincrement=True)
    booking_reference = Column(String(20), nullable=False, unique=True, index=True)
    showing_id        = Column(Integer, ForeignKey("showings.showing_id", ondelete="RESTRICT"), nullable=False, index=True)
    show_date         = Column(Date, nullable=False, index=True)
    booked_by         = Column(Integer, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    customer_name     = Column(String(255), nullable=False)
    customer_phone    = Column(String(20))
    customer_email    = Column(String(255))
    num_tickets       = Column(Integer, nullable=False)
    total_cost        = Column(Numeric(8, 2), nullable=False)
    booking_status    = Column(String(10), nullable=False, default="confirmed", index=True)  # confirmed / cancelled
    payment_simulated = Column(Boolean, nullable=False, default=False)
    booking_date      = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), index=True)
    cancelled_at      = Column(TIMESTAMP, nullable=True)
    cancellation_fee  = Column(Numeric(8, 2), default=0.00)
    refund_amount     = Column(Numeric(8, 2), default=0.00)

    # Relationships
    showing      = relationship("Showing", back_populates="bookings")
    staff        = relationship("User", back_populates="bookings")
    booked_seats = relationship("BookedSeat", back_populates="booking", lazy="selectin", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Booking(booking_id={self.booking_id}, ref='{self.booking_reference}', status='{self.booking_status}')>"


class BookedSeat(Base):
    __tablename__ = "booked_seats"
    __table_args__ = (
        UniqueConstraint("booking_id", "seat_id", name="uq_booking_seat"),
    )

    booked_seat_id = Column(Integer, primary_key=True, autoincrement=True)
    booking_id     = Column(Integer, ForeignKey("bookings.booking_id", ondelete="CASCADE"), nullable=False, index=True)
    seat_id        = Column(Integer, ForeignKey("seats.seat_id", ondelete="RESTRICT"), nullable=False, index=True)
    unit_price     = Column(Numeric(6, 2), nullable=False)

    # Relationships
    booking = relationship("Booking", back_populates="booked_seats")
    seat    = relationship("Seat", back_populates="booked_seats")

    def __repr__(self):
        return f"<BookedSeat(booking={self.booking_id}, seat={self.seat_id}, price=£{self.unit_price})>"