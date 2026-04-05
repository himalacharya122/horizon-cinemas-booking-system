"""
tests/unit/test_security.py
Unit tests for password hashing and JWT token handling.

Test cases:
  TC-SEC-01  Password hash produces a valid bcrypt string
  TC-SEC-02  Correct password verifies successfully
  TC-SEC-03  Wrong password fails verification
  TC-SEC-04  JWT token contains expected claims
  TC-SEC-05  Valid JWT decodes correctly
  TC-SEC-06  Expired JWT returns None
  TC-SEC-07  Tampered JWT returns None
  TC-SEC-08  Empty / garbage token returns None
"""

from datetime import timedelta

from backend.core.security import (
    hash_password, verify_password,
    create_access_token, decode_access_token,
)


class TestPasswordHashing:

    def test_hash_produces_bcrypt_string(self):
        """TC-SEC-01: hash output starts with $2b$ (bcrypt prefix)."""
        hashed = hash_password("MySecret123")
        assert hashed.startswith("$2b$")
        assert len(hashed) > 50

    def test_correct_password_verifies(self):
        """TC-SEC-02: verify returns True for the original password."""
        hashed = hash_password("Password123!")
        assert verify_password("Password123!", hashed) is True

    def test_wrong_password_fails(self):
        """TC-SEC-03: verify returns False for a different password."""
        hashed = hash_password("Password123!")
        assert verify_password("WrongPassword", hashed) is False

    def test_different_hashes_for_same_password(self):
        """Each call to hash_password should produce a unique salt."""
        h1 = hash_password("Same")
        h2 = hash_password("Same")
        assert h1 != h2  # different salts
        assert verify_password("Same", h1) is True
        assert verify_password("Same", h2) is True


class TestJWT:

    def test_token_contains_expected_claims(self):
        """TC-SEC-04: JWT payload includes sub, username, role, cinema_id, exp."""
        token = create_access_token(
            user_id=42, username="testuser", role_name="admin", cinema_id=1
        )
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "42"
        assert payload["username"] == "testuser"
        assert payload["role"] == "admin"
        assert payload["cinema_id"] == 1
        assert "exp" in payload

    def test_valid_token_decodes(self):
        """TC-SEC-05: A freshly created token decodes without error."""
        token = create_access_token(1, "u", "booking_staff", 1)
        result = decode_access_token(token)
        assert result is not None
        assert result["sub"] == "1"

    def test_expired_token_returns_none(self):
        """TC-SEC-06: An already-expired token returns None."""
        token = create_access_token(
            1, "u", "booking_staff", 1,
            expires_delta=timedelta(seconds=-10),
        )
        assert decode_access_token(token) is None

    def test_tampered_token_returns_none(self):
        """TC-SEC-07: Modifying the token string makes it invalid."""
        token = create_access_token(1, "u", "booking_staff", 1)
        tampered = token[:-4] + "XXXX"
        assert decode_access_token(tampered) is None

    def test_garbage_token_returns_none(self):
        """TC-SEC-08: Completely invalid strings return None."""
        assert decode_access_token("") is None
        assert decode_access_token("not.a.jwt") is None
        assert decode_access_token("abc123") is None