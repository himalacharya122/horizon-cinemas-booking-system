"""
backend/core/exceptions.py
Application-specific exceptions.
Raised by services, caught by API endpoints and translated to HTTP responses.
"""


class HCBSException(Exception):
    """Base exception for all HCBS business errors."""

    def __init__(self, message: str = "An error occurred", status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(HCBSException):
    """Invalid credentials or inactive account."""

    def __init__(self, message: str = "Invalid username or password"):
        super().__init__(message=message, status_code=401)


class AuthorisationError(HCBSException):
    """User lacks the required role for this action."""

    def __init__(self, message: str = "You do not have permission to perform this action"):
        super().__init__(message=message, status_code=403)


class NotFoundError(HCBSException):
    """Requested resource does not exist."""

    def __init__(self, resource: str = "Resource"):
        super().__init__(message=f"{resource} not found", status_code=404)


class BookingError(HCBSException):
    """Covers seat unavailability, advance-booking limits, cancellation rules, etc."""
    pass


class ValidationError(HCBSException):
    """Input data fails business validation."""
    pass