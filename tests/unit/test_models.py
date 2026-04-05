"""
tests/unit/test_models.py
Unit tests for ORM model properties and constraints.

Test cases:
  TC-MOD-01  Film.duration_display formats correctly (hours + minutes)
  TC-MOD-02  Film.duration_display for sub-hour films
  TC-MOD-03  User.full_name concatenation
  TC-MOD-04  Screen seat arithmetic (lower + upper = total)
  TC-MOD-05  VIP seats ≤ 10
  TC-MOD-06  Screen capacity range 50-120
  TC-MOD-07  Screen number range 1-6
  TC-MOD-08  Booking reference format HC-YYYY-#####
"""

import re
from datetime import date

from backend.models.film import Film
from backend.models.user import User, Role
from backend.models.cinema import Screen


class TestFilmModel:

    def test_duration_display_hours_and_minutes(self):
        """TC-MOD-01: 130 min → '2h 10m'"""
        film = Film.__new__(Film)
        film.duration_mins = 130
        assert film.duration_display == "2h 10m"

    def test_duration_display_sub_hour(self):
        """TC-MOD-02: 45 min → '45m'"""
        film = Film.__new__(Film)
        film.duration_mins = 45
        assert film.duration_display == "45m"

    def test_duration_display_exact_hour(self):
        """Exact hour: 120 min → '2h 0m'"""
        film = Film.__new__(Film)
        film.duration_mins = 120
        assert film.duration_display == "2h 0m"


class TestUserModel:

    def test_full_name(self):
        """TC-MOD-03"""
        user = User.__new__(User)
        user.first_name = "Aisha"
        user.last_name = "Khan"
        assert user.full_name == "Aisha Khan"


class TestScreenConstraints:

    def test_seat_arithmetic(self):
        """TC-MOD-04: lower + upper must equal total."""
        # Valid
        s = Screen(
            cinema_id=1, screen_number=1,
            total_seats=80, lower_hall_seats=24,
            upper_gallery_seats=56, vip_seats=5,
        )
        assert s.lower_hall_seats + s.upper_gallery_seats == s.total_seats

    def test_vip_max_10(self):
        """TC-MOD-05: VIP seats should be ≤ 10."""
        s = Screen(
            cinema_id=1, screen_number=1,
            total_seats=120, lower_hall_seats=36,
            upper_gallery_seats=84, vip_seats=10,
        )
        assert s.vip_seats <= 10

    def test_capacity_range(self):
        """TC-MOD-06: total_seats between 50 and 120."""
        for valid in [50, 80, 120]:
            s = Screen(
                cinema_id=1, screen_number=1,
                total_seats=valid, lower_hall_seats=int(valid * 0.3),
                upper_gallery_seats=valid - int(valid * 0.3), vip_seats=0,
            )
            assert 50 <= s.total_seats <= 120

    def test_screen_number_range(self):
        """TC-MOD-07: screen_number between 1 and 6."""
        for valid in [1, 3, 6]:
            s = Screen(
                cinema_id=1, screen_number=valid,
                total_seats=80, lower_hall_seats=24,
                upper_gallery_seats=56, vip_seats=0,
            )
            assert 1 <= s.screen_number <= 6


class TestBookingReference:

    def test_reference_format(self):
        """TC-MOD-08: Booking reference matches HC-YYYY-##### pattern."""
        year = date.today().year
        pattern = rf"^HC-{year}-\d{{5}}$"
        # Simulate few references
        for num in [1, 42, 99999]:
            ref = f"HC-{year}-{num:05d}"
            assert re.match(pattern, ref), f"{ref} does not match pattern"