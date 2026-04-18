"""
tests/integration/test_bookings.py
Integration tests for the complete booking lifecycle.

Test cases:
  TC-BK-01   Check availability — seats exist and price is correct
  TC-BK-02   Create booking — returns confirmed status + seat numbers
  TC-BK-03   Booking reference format is HC-YYYY-#####
  TC-BK-04   Total cost = unit_price * num_tickets
  TC-BK-05   Look up booking by reference
  TC-BK-06   Cancel booking — 50% fee charged
  TC-BK-07   Cancel booking — refund = total - fee
  TC-BK-08   Cannot cancel already-cancelled booking
  TC-BK-09   Cannot book for past date
  TC-BK-10   Cannot book more than 7 days in advance
  TC-BK-11   Cannot book more seats than available
  TC-BK-12   No auth returns 403
  TC-BK-13   Booking with missing customer name returns 422
  TC-BK-14   VIP pricing is correct on booking
  TC-BK-15   Upper gallery pricing is correct on booking
  TC-BK-16   Availability decreases after booking
  TC-BK-17   Cancelled booking frees seats for re-booking
  TC-BK-18   Cannot cancel on the day of the show
  TC-BK-19   Invalid showing_id returns 404
  TC-BK-20   Date outside listing window returns 400
"""

import re
from datetime import date, timedelta

from tests.conftest import auth_header  # type: ignore


class TestCheckAvailability:
    def test_availability_returns_correct_data(self, seeded_client, staff_token):
        """TC-BK-01: Availability check returns seats + correct evening lower hall price."""
        client, seed = seeded_client
        showing = seed["showings"]["evening"]
        resp = client.post(
            "/api/v1/bookings/check-availability",
            json={
                "showing_id": showing.showing_id,
                "show_date": (date.today() + timedelta(days=1)).isoformat(),
                "seat_type": "lower_hall",
                "num_tickets": 2,
            },
            headers=auth_header(staff_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["available"] is True
        assert data["seats_total"] == 24  # Bristol screen lower hall
        assert data["unit_price"] == 8.00  # Bristol evening lower
        assert data["total_price"] == 16.00

    def test_availability_nonexistent_showing(self, seeded_client, staff_token):
        """TC-BK-19"""
        client, _ = seeded_client
        resp = client.post(
            "/api/v1/bookings/check-availability",
            json={
                "showing_id": 99999,
                "show_date": date.today().isoformat(),
                "seat_type": "lower_hall",
                "num_tickets": 1,
            },
            headers=auth_header(staff_token),
        )
        assert resp.status_code == 404

    def test_availability_outside_listing_window(self, seeded_client, staff_token):
        """TC-BK-20"""
        client, seed = seeded_client
        showing = seed["showings"]["morning"]
        far_future = (date.today() + timedelta(days=30)).isoformat()
        resp = client.post(
            "/api/v1/bookings/check-availability",
            json={
                "showing_id": showing.showing_id,
                "show_date": far_future,
                "seat_type": "lower_hall",
                "num_tickets": 1,
            },
            headers=auth_header(staff_token),
        )
        # Could be 400 (booking error) or 400 (advance limit) depending on which fires first
        assert resp.status_code == 400


class TestCreateBooking:
    def _book(self, client, token, seed, seat_type="lower_hall", num=2, days_ahead=1):
        showing = seed["showings"]["evening"]
        return client.post(
            "/api/v1/bookings",
            json={
                "showing_id": showing.showing_id,
                "show_date": (date.today() + timedelta(days=days_ahead)).isoformat(),
                "customer_name": "Alice Test",
                "customer_phone": "07700900000",
                "customer_email": "alice@test.com",
                "seat_type": seat_type,
                "num_tickets": num,
                "payment_simulated": True,
            },
            headers=auth_header(token),
        )

    def test_create_booking_confirmed(self, seeded_client, staff_token):
        """TC-BK-02: Booking is created with confirmed status."""
        client, seed = seeded_client
        resp = self._book(client, staff_token, seed)
        assert resp.status_code == 201
        data = resp.json()
        assert data["booking_status"] == "confirmed"
        assert data["num_tickets"] == 2
        assert len(data["booked_seats"]) == 2
        assert data["customer_name"] == "Alice Test"

    def test_booking_reference_format(self, seeded_client, staff_token):
        """TC-BK-03: Reference matches HC-YYYY-##### pattern."""
        client, seed = seeded_client
        resp = self._book(client, staff_token, seed)
        ref = resp.json()["booking_reference"]
        year = date.today().year
        assert re.match(rf"^HC-{year}-\d{{5}}$", ref)

    def test_total_cost_calculation(self, seeded_client, staff_token):
        """TC-BK-04: total_cost = unit_price × num_tickets."""
        client, seed = seeded_client
        resp = self._book(client, staff_token, seed, num=3)
        data = resp.json()
        # Bristol evening lower = £8 × 3 = £24
        assert data["total_cost"] == 24.00

    def test_vip_pricing_on_booking(self, seeded_client, staff_token):
        """TC-BK-14: VIP booking uses correct price (lower × 1.44)."""
        client, seed = seeded_client
        resp = self._book(client, staff_token, seed, seat_type="vip", num=1)
        assert resp.status_code == 201
        data = resp.json()
        # Bristol evening VIP = 8 * 1.44 = 11.52
        assert data["total_cost"] == 11.52
        assert data["booked_seats"][0]["unit_price"] == 11.52

    def test_upper_gallery_pricing(self, seeded_client, staff_token):
        """TC-BK-15: Upper gallery = lower × 1.20."""
        client, seed = seeded_client
        resp = self._book(client, staff_token, seed, seat_type="upper_gallery", num=2)
        assert resp.status_code == 201
        data = resp.json()
        # Bristol evening upper = 8 * 1.20 = 9.60 × 2 = 19.20
        assert data["total_cost"] == 19.20

    def test_cannot_book_past_date(self, seeded_client, staff_token):
        """TC-BK-09"""
        client, seed = seeded_client
        showing = seed["showings"]["evening"]
        resp = client.post(
            "/api/v1/bookings",
            json={
                "showing_id": showing.showing_id,
                "show_date": (date.today() - timedelta(days=1)).isoformat(),
                "customer_name": "X",
                "seat_type": "lower_hall",
                "num_tickets": 1,
            },
            headers=auth_header(staff_token),
        )
        assert resp.status_code == 400
        assert "past" in resp.json()["detail"].lower()

    def test_cannot_book_beyond_7_days(self, seeded_client, staff_token):
        """TC-BK-10"""
        client, seed = seeded_client
        resp = self._book(client, staff_token, seed, days_ahead=8)
        assert resp.status_code == 400
        assert "7 days" in resp.json()["detail"]

    def test_cannot_overbook_seats(self, seeded_client, staff_token):
        """TC-BK-11: Requesting more seats than available fails."""
        client, seed = seeded_client
        # Bristol screen has 5 VIP seats — try to book 6
        resp = self._book(client, staff_token, seed, seat_type="vip", num=6)
        assert resp.status_code == 400
        assert "available" in resp.json()["detail"].lower()

    def test_no_auth_returns_403(self, seeded_client):
        """TC-BK-12: Requests without a token get 403."""
        client, seed = seeded_client
        showing = seed["showings"]["evening"]
        resp = client.post(
            "/api/v1/bookings",
            json={
                "showing_id": showing.showing_id,
                "show_date": date.today().isoformat(),
                "customer_name": "X",
                "seat_type": "lower_hall",
                "num_tickets": 1,
            },
        )
        assert resp.status_code == 403

    def test_missing_customer_name(self, seeded_client, staff_token):
        """TC-BK-13"""
        client, seed = seeded_client
        showing = seed["showings"]["evening"]
        resp = client.post(
            "/api/v1/bookings",
            json={
                "showing_id": showing.showing_id,
                "show_date": (date.today() + timedelta(days=1)).isoformat(),
                "seat_type": "lower_hall",
                "num_tickets": 1,
                # customer_name is missing
            },
            headers=auth_header(staff_token),
        )
        assert resp.status_code == 422

    def test_availability_decreases_after_booking(self, seeded_client, staff_token):
        """TC-BK-16: Booking 3 lower hall seats reduces availability by 3."""
        client, seed = seeded_client
        showing = seed["showings"]["evening"]
        show_date = (date.today() + timedelta(days=1)).isoformat()

        # Check before
        r1 = client.post(
            "/api/v1/bookings/check-availability",
            json={
                "showing_id": showing.showing_id,
                "show_date": show_date,
                "seat_type": "lower_hall",
                "num_tickets": 1,
            },
            headers=auth_header(staff_token),
        )
        before = r1.json()["seats_available"]

        # Book 3
        self._book(client, staff_token, seed, num=3)

        # Check after
        r2 = client.post(
            "/api/v1/bookings/check-availability",
            json={
                "showing_id": showing.showing_id,
                "show_date": show_date,
                "seat_type": "lower_hall",
                "num_tickets": 1,
            },
            headers=auth_header(staff_token),
        )
        after = r2.json()["seats_available"]

        assert after == before - 3


class TestLookupBooking:
    def test_lookup_by_reference(self, seeded_client, staff_token):
        """TC-BK-05"""
        client, seed = seeded_client
        showing = seed["showings"]["morning"]
        create_resp = client.post(
            "/api/v1/bookings",
            json={
                "showing_id": showing.showing_id,
                "show_date": (date.today() + timedelta(days=1)).isoformat(),
                "customer_name": "Bob Lookup",
                "seat_type": "lower_hall",
                "num_tickets": 1,
            },
            headers=auth_header(staff_token),
        )
        ref = create_resp.json()["booking_reference"]

        lookup = client.get(
            f"/api/v1/bookings/reference/{ref}",
            headers=auth_header(staff_token),
        )
        assert lookup.status_code == 200
        assert lookup.json()["booking_reference"] == ref
        assert lookup.json()["customer_name"] == "Bob Lookup"

    def test_lookup_nonexistent_reference(self, seeded_client, staff_token):
        """Non-existent reference returns 404."""
        client, _ = seeded_client
        resp = client.get(
            "/api/v1/bookings/reference/HC-0000-99999",
            headers=auth_header(staff_token),
        )
        assert resp.status_code == 404


class TestCancelBooking:
    def _make_booking(self, client, token, seed, days_ahead=2):
        showing = seed["showings"]["afternoon"]
        resp = client.post(
            "/api/v1/bookings",
            json={
                "showing_id": showing.showing_id,
                "show_date": (date.today() + timedelta(days=days_ahead)).isoformat(),
                "customer_name": "Cancel Test",
                "seat_type": "lower_hall",
                "num_tickets": 2,
            },
            headers=auth_header(token),
        )
        return resp.json()

    def test_cancel_50_percent_fee(self, seeded_client, staff_token):
        """TC-BK-06: Cancellation fee = 50% of total."""
        client, seed = seeded_client
        booking = self._make_booking(client, staff_token, seed)
        total = booking["total_cost"]

        resp = client.post(
            "/api/v1/bookings/cancel",
            json={
                "booking_reference": booking["booking_reference"],
            },
            headers=auth_header(staff_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["cancellation_fee"] == round(total * 0.50, 2)

    def test_cancel_refund_amount(self, seeded_client, staff_token):
        """TC-BK-07: Refund = total - fee."""
        client, seed = seeded_client
        booking = self._make_booking(client, staff_token, seed)
        total = booking["total_cost"]

        resp = client.post(
            "/api/v1/bookings/cancel",
            json={
                "booking_reference": booking["booking_reference"],
            },
            headers=auth_header(staff_token),
        )
        data = resp.json()
        expected_refund = round(total - total * 0.50, 2)
        assert data["refund_amount"] == expected_refund

    def test_cannot_cancel_twice(self, seeded_client, staff_token):
        """TC-BK-08"""
        client, seed = seeded_client
        booking = self._make_booking(client, staff_token, seed)
        ref = booking["booking_reference"]

        # First cancel — OK
        client.post(
            "/api/v1/bookings/cancel",
            json={
                "booking_reference": ref,
            },
            headers=auth_header(staff_token),
        )

        # Second cancel — should fail
        resp = client.post(
            "/api/v1/bookings/cancel",
            json={
                "booking_reference": ref,
            },
            headers=auth_header(staff_token),
        )
        assert resp.status_code == 400
        assert "already" in resp.json()["detail"].lower()

    def test_cancelled_booking_frees_seats(self, seeded_client, staff_token):
        """TC-BK-17: After cancellation, seats become available again."""
        client, seed = seeded_client
        showing = seed["showings"]["afternoon"]
        show_date = (date.today() + timedelta(days=2)).isoformat()

        # Check initial
        r1 = client.post(
            "/api/v1/bookings/check-availability",
            json={
                "showing_id": showing.showing_id,
                "show_date": show_date,
                "seat_type": "lower_hall",
                "num_tickets": 1,
            },
            headers=auth_header(staff_token),
        )
        before = r1.json()["seats_available"]

        # Book 2
        booking = self._make_booking(client, staff_token, seed)

        # Cancel
        client.post(
            "/api/v1/bookings/cancel",
            json={
                "booking_reference": booking["booking_reference"],
            },
            headers=auth_header(staff_token),
        )

        # Check again — should be back to original
        r2 = client.post(
            "/api/v1/bookings/check-availability",
            json={
                "showing_id": showing.showing_id,
                "show_date": show_date,
                "seat_type": "lower_hall",
                "num_tickets": 1,
            },
            headers=auth_header(staff_token),
        )
        after = r2.json()["seats_available"]

        assert after == before
