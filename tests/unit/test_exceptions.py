# ============================================
# Author: Himal Acharya
# Student ID: 22085619
# Last Edited: 2026-04-25
# ============================================

"""
tests/unit/test_exceptions.py
Unit tests for custom exception classes.

Test cases:
  TC-EXC-01  HCBSException has message and status_code
  TC-EXC-02  AuthenticationError defaults to 401
  TC-EXC-03  AuthorisationError defaults to 403
  TC-EXC-04  NotFoundError defaults to 404
  TC-EXC-05  BookingError defaults to 400
  TC-EXC-06  ValidationError defaults to 400
  TC-EXC-07  NotFoundError includes resource name
"""

from backend.core.exceptions import (
    AuthenticationError,
    AuthorisationError,
    BookingError,
    HCBSException,
    NotFoundError,
    ValidationError,
)


class TestExceptions:
    def test_base_exception(self):
        """TC-EXC-01"""
        exc = HCBSException("Something broke", 500)
        assert exc.message == "Something broke"
        assert exc.status_code == 500
        assert str(exc) == "Something broke"

    def test_authentication_error_401(self):
        """TC-EXC-02"""
        exc = AuthenticationError()
        assert exc.status_code == 401
        assert "Invalid" in exc.message

    def test_authorisation_error_403(self):
        """TC-EXC-03"""
        exc = AuthorisationError()
        assert exc.status_code == 403

    def test_not_found_error_404(self):
        """TC-EXC-04"""
        exc = NotFoundError()
        assert exc.status_code == 404

    def test_booking_error_400(self):
        """TC-EXC-05"""
        exc = BookingError("Seats unavailable")
        assert exc.status_code == 400
        assert exc.message == "Seats unavailable"

    def test_validation_error_400(self):
        """TC-EXC-06"""
        exc = ValidationError("Bad input")
        assert exc.status_code == 400

    def test_not_found_includes_resource_name(self):
        """TC-EXC-07"""
        exc = NotFoundError("Film")
        assert "Film" in exc.message
        assert exc.message == "Film not found"
