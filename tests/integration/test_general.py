# ============================================
# Author: Himal Acharya
# Student ID: 22085619
# Last Edited: 2026-04-25
# ============================================

"""
tests/integration/test_general.py
General integration tests: health check, edge cases, bad input.

Test cases:
  TC-GEN-01  Health check returns 200
  TC-GEN-02  Non-existent route returns 404
  TC-GEN-03  Invalid JSON body returns 422
  TC-GEN-04  Expired token returns 401
  TC-GEN-05  Booking search with filters
"""

from datetime import date, timedelta

from backend.core.security import create_access_token
from tests.conftest import auth_header  # type: ignore


class TestHealthCheck:
    def test_health(self, seeded_client):
        """TC-GEN-01"""
        client, _ = seeded_client
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestEdgeCases:
    def test_nonexistent_route(self, seeded_client):
        """TC-GEN-02"""
        client, _ = seeded_client
        resp = client.get("/api/v1/nonexistent")
        assert resp.status_code in (404, 405)

    def test_invalid_json_body(self, seeded_client, staff_token):
        """TC-GEN-03"""
        client, _ = seeded_client
        resp = client.post(
            "/api/v1/bookings",
            content="not json",
            headers={**auth_header(staff_token), "Content-Type": "application/json"},
        )
        assert resp.status_code == 422

    def test_expired_token_returns_401(self, seeded_client):
        """TC-GEN-04"""
        client, seed = seeded_client
        expired = create_access_token(
            1,
            "x",
            "booking_staff",
            1,
            expires_delta=timedelta(seconds=-10),
        )
        resp = client.get("/api/v1/films", headers=auth_header(expired))
        assert resp.status_code == 401

    def test_booking_search_with_filters(self, seeded_client, staff_token):
        """TC-GEN-05: Search endpoint works with various filter combos."""
        client, seed = seeded_client
        # First create a booking
        showing = seed["showings"]["morning"]
        client.post(
            "/api/v1/bookings",
            json={
                "showing_id": showing.showing_id,
                "show_date": (date.today() + timedelta(days=1)).isoformat(),
                "customer_name": "Search Test User",
                "customer_email": "search@test.com",
                "seat_type": "lower_hall",
                "num_tickets": 1,
            },
            headers=auth_header(staff_token),
        )

        # Search by name
        resp = client.get(
            "/api/v1/bookings/search",
            params={"customer_name": "Search Test"},
            headers=auth_header(staff_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 1
        assert resp.json()[0]["customer_name"] == "Search Test User"

        # Search by status
        resp = client.get(
            "/api/v1/bookings/search",
            params={"status": "confirmed"},
            headers=auth_header(staff_token),
        )
        assert resp.status_code == 200
        for b in resp.json():
            assert b["booking_status"] == "confirmed"
