"""
tests/integration/test_roles.py
Integration tests for role-based access control.

Test cases:
  TC-ROLE-01  Booking staff can list films
  TC-ROLE-02  Booking staff CANNOT create films (admin-only)
  TC-ROLE-03  Booking staff CANNOT create cinemas (manager-only)
  TC-ROLE-04  Admin CAN create films
  TC-ROLE-05  Admin CANNOT create cinemas (manager-only)
  TC-ROLE-06  Manager CAN create cinemas
  TC-ROLE-07  Manager CAN create films (inherits admin)
  TC-ROLE-08  Admin CAN access reports
  TC-ROLE-09  Booking staff CANNOT access reports
  TC-ROLE-10  No token returns 403 on protected endpoints
"""

from tests.conftest import auth_header  # type: ignore


class TestRoleAccess:
    def test_staff_can_list_films(self, seeded_client, staff_token):
        """TC-ROLE-01"""
        client, _ = seeded_client
        resp = client.get("/api/v1/films", headers=auth_header(staff_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_staff_cannot_create_film(self, seeded_client, staff_token):
        """TC-ROLE-02"""
        client, _ = seeded_client
        resp = client.post(
            "/api/v1/films",
            json={
                "title": "Blocked Film",
                "genre": "Action",
                "age_rating": "PG",
                "duration_mins": 90,
            },
            headers=auth_header(staff_token),
        )
        assert resp.status_code == 403

    def test_staff_cannot_create_cinema(self, seeded_client, staff_token):
        """TC-ROLE-03"""
        client, _ = seeded_client
        resp = client.post(
            "/api/v1/cinemas",
            json={
                "city_id": 1,
                "cinema_name": "X",
                "address": "X",
            },
            headers=auth_header(staff_token),
        )
        assert resp.status_code == 403

    def test_admin_can_create_film(self, seeded_client, admin_token):
        """TC-ROLE-04"""
        client, _ = seeded_client
        resp = client.post(
            "/api/v1/films",
            json={
                "title": "Admin Film",
                "genre": "Drama",
                "age_rating": "15",
                "duration_mins": 120,
            },
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 201
        assert resp.json()["title"] == "Admin Film"

    def test_admin_cannot_create_cinema(self, seeded_client, admin_token):
        """TC-ROLE-05"""
        client, _ = seeded_client
        resp = client.post(
            "/api/v1/cinemas",
            json={
                "city_id": 1,
                "cinema_name": "X",
                "address": "X",
            },
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 403

    def test_manager_can_create_cinema(self, seeded_client, manager_token):
        """TC-ROLE-06"""
        client, seed = seeded_client
        city_id = seed["cities"]["london"].city_id
        resp = client.post(
            "/api/v1/cinemas",
            json={
                "city_id": city_id,
                "cinema_name": "Horizon London Stratford",
                "address": "Westfield Stratford",
            },
            headers=auth_header(manager_token),
        )
        assert resp.status_code == 201
        assert "Stratford" in resp.json()["cinema_name"]

    def test_manager_can_create_film(self, seeded_client, manager_token):
        """TC-ROLE-07"""
        client, _ = seeded_client
        resp = client.post(
            "/api/v1/films",
            json={
                "title": "Manager Film",
                "genre": "Comedy",
                "age_rating": "PG-13",
                "duration_mins": 95,
            },
            headers=auth_header(manager_token),
        )
        assert resp.status_code == 201

    def test_admin_can_access_reports(self, seeded_client, admin_token):
        """TC-ROLE-08"""
        client, _ = seeded_client
        resp = client.get(
            "/api/v1/reports/revenue",
            params={"year": 2025, "month": 1},
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200

    def test_staff_cannot_access_reports(self, seeded_client, staff_token):
        """TC-ROLE-09"""
        client, _ = seeded_client
        resp = client.get(
            "/api/v1/reports/revenue",
            params={"year": 2025, "month": 1},
            headers=auth_header(staff_token),
        )
        assert resp.status_code == 403

    def test_no_token_returns_403(self, seeded_client):
        """TC-ROLE-10"""
        client, _ = seeded_client
        resp = client.get("/api/v1/films")
        assert resp.status_code == 403
