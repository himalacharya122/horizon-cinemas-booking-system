# ============================================
# Author: Smriti Ale
# Student ID: 24036547
# Last Edited: 2026-04-25
# ============================================

"""
backend/models/user.py
ORM models for: Role, User
"""

from sqlalchemy import (  # type: ignore
    TIMESTAMP,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    text,
)
from sqlalchemy.orm import relationship  # type: ignore

from backend.core.database import Base


class Role(Base):
    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String(20), nullable=False, unique=True)  # booking_staff, admin, manager

    users = relationship("User", back_populates="role", lazy="selectin")

    def __repr__(self):
        return f"<Role(role_id={self.role_id}, role_name='{self.role_name}')>"


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    cinema_id = Column(
        Integer, ForeignKey("cinemas.cinema_id", ondelete="RESTRICT"), nullable=False
    )
    role_id = Column(Integer, ForeignKey("roles.role_id", ondelete="RESTRICT"), nullable=False)
    username = Column(String(50), nullable=False, unique=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    )
    last_login = Column(DateTime, nullable=True)

    # Relationships
    cinema = relationship("Cinema", back_populates="users")
    role = relationship("Role", back_populates="users")
    bookings = relationship("Booking", back_populates="staff", lazy="selectin")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def role_name(self) -> str:
        return self.role.role_name if self.role else ""

    def __repr__(self):
        return f"<User(user_id={self.user_id}, username='{self.username}')>"
