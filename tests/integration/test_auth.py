# ============================================
# Author: Smriti Ale
# Student ID: 24036547
# Last Edited: 2026-04-25
# ============================================

"""
tests/integration/test_auth.py
Integration tests for POST /api/v1/auth/login.

Test cases:
  TC-AUTH-01  Valid credentials return token + user info
  TC-AUTH-02  Wrong password returns 401
  TC-AUTH-03  Non-existent username returns 401
  TC-AUTH-04  Empty username returns 422 (validation)
  TC-AUTH-05  Empty password returns 422 (validation)
  TC-AUTH-06  Response token is a valid JWT with correct claims
"""

from backend.core.security import decode_access_token


class TestAuthEndpoint:
    def test_valid_login(self, seeded_client):
        """TC-AUTH-01: Correct credentials return 200 + token + user info."""
        client, seed = seeded_client
        resp = client.post(
            "/api/v1/auth/login", json={"username": "teststaff", "password": "Password123!"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "teststaff"
        assert data["user"]["role"] == "booking_staff"
        assert data["user"]["full_name"] == "Test Staff"

    def test_wrong_password(self, seeded_client):
        """TC-AUTH-02"""
        client, _ = seeded_client
        resp = client.post(
            "/api/v1/auth/login", json={"username": "teststaff", "password": "WrongPassword"}
        )
        assert resp.status_code == 401
        assert "Invalid" in resp.json()["detail"]

    def test_nonexistent_user(self, seeded_client):
        """TC-AUTH-03"""
        client, _ = seeded_client
        resp = client.post(
            "/api/v1/auth/login", json={"username": "nobody", "password": "Password123!"}
        )
        assert resp.status_code == 401

    def test_empty_username(self, seeded_client):
        """TC-AUTH-04"""
        client, _ = seeded_client
        resp = client.post("/api/v1/auth/login", json={"username": "", "password": "Password123!"})
        assert resp.status_code == 422

    def test_empty_password(self, seeded_client):
        """TC-AUTH-05"""
        client, _ = seeded_client
        resp = client.post("/api/v1/auth/login", json={"username": "teststaff", "password": ""})
        assert resp.status_code == 422

    def test_token_contains_correct_claims(self, seeded_client):
        """TC-AUTH-06: The returned JWT has the right payload."""
        client, seed = seeded_client
        resp = client.post(
            "/api/v1/auth/login", json={"username": "testadmin", "password": "Password123!"}
        )
        token = resp.json()["access_token"]
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["role"] == "admin"
        assert payload["username"] == "testadmin"
