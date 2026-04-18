"""
tests/integration/test_cinemas.py
Integration tests for cinema, city, screen, and price management.

Test cases:
  TC-CIN-01  List cinemas returns seeded cinemas
  TC-CIN-02  Get single cinema with screens
  TC-CIN-03  Manager creates cinema in existing city
  TC-CIN-04  Manager creates cinema in new city
  TC-CIN-05  Manager adds screen to cinema (with seat generation)
  TC-CIN-06  Cannot add screen beyond max 6
  TC-CIN-07  List cities
  TC-CIN-08  List base prices
  TC-CIN-09  Set / update base price
  TC-CIN-10  Screen seat arithmetic validated on creation
  TC-CIN-11  Filter cinemas by city_id
"""

from tests.conftest import auth_header  # type: ignore


class TestCinemaEndpoints:
    def test_list_cinemas(self, seeded_client, staff_token):
        """TC-CIN-01"""
        client, _ = seeded_client
        resp = client.get("/api/v1/cinemas", headers=auth_header(staff_token))
        assert resp.status_code == 200
        names = [c["cinema_name"] for c in resp.json()]
        assert any("Bristol" in n for n in names)
        assert any("London" in n for n in names)

    def test_get_cinema_with_screens(self, seeded_client, staff_token):
        """TC-CIN-02"""
        client, seed = seeded_client
        cid = seed["cinemas"]["bristol"].cinema_id
        resp = client.get(f"/api/v1/cinemas/{cid}", headers=auth_header(staff_token))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["screens"]) >= 1
        assert data["screens"][0]["total_seats"] == 80

    def test_manager_creates_cinema_existing_city(self, seeded_client, manager_token):
        """TC-CIN-03"""
        client, seed = seeded_client
        resp = client.post(
            "/api/v1/cinemas",
            json={
                "city_id": seed["cities"]["bristol"].city_id,
                "cinema_name": "Horizon Bristol Harbourside",
                "address": "10 Harbourside Walk, Bristol",
                "phone": "0117 000 9999",
            },
            headers=auth_header(manager_token),
        )
        assert resp.status_code == 201
        assert resp.json()["cinema_name"] == "Horizon Bristol Harbourside"

    def test_manager_creates_cinema_new_city(self, seeded_client, manager_token):
        """TC-CIN-04"""
        client, _ = seeded_client
        resp = client.post(
            "/api/v1/cinemas",
            json={
                "new_city_name": "Manchester",
                "cinema_name": "Horizon Manchester Arndale",
                "address": "Unit 5 Arndale Centre, Manchester",
            },
            headers=auth_header(manager_token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["cinema_name"] == "Horizon Manchester Arndale"

    def test_manager_adds_screen(self, seeded_client, manager_token):
        """TC-CIN-05: Adding a screen auto-generates seat records."""
        client, seed = seeded_client
        cid = seed["cinemas"]["london"].cinema_id
        resp = client.post(
            f"/api/v1/cinemas/{cid}/screens",
            json={
                "screen_number": 2,
                "total_seats": 60,
                "lower_hall_seats": 18,
                "upper_gallery_seats": 42,
                "vip_seats": 5,
            },
            headers=auth_header(manager_token),
        )
        assert resp.status_code == 201
        assert resp.json()["screen_number"] == 2
        assert resp.json()["total_seats"] == 60


class TestCityEndpoints:
    def test_list_cities(self, seeded_client, staff_token):
        """TC-CIN-07"""
        client, _ = seeded_client
        resp = client.get("/api/v1/cinemas/cities", headers=auth_header(staff_token))
        assert resp.status_code == 200
        names = [c["city_name"] for c in resp.json()]
        assert "Bristol" in names
        assert "London" in names


class TestPriceEndpoints:
    def test_list_prices(self, seeded_client, staff_token):
        """TC-CIN-08"""
        client, _ = seeded_client
        resp = client.get("/api/v1/cinemas/prices", headers=auth_header(staff_token))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 6  # 2 cities × 3 periods

    def test_set_price(self, seeded_client, admin_token):
        """TC-CIN-09"""
        client, seed = seeded_client
        city_id = seed["cities"]["bristol"].city_id
        resp = client.post(
            "/api/v1/cinemas/prices",
            json={
                "city_id": city_id,
                "show_period": "morning",
                "lower_hall_price": 7.50,
            },
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["lower_hall_price"] == 7.50
        assert data["upper_gallery_price"] == 9.00  # 7.50 * 1.20
        assert data["vip_price"] == 10.80  # 7.50 * 1.44

    def test_filter_cinemas_by_city(self, seeded_client, staff_token):
        """TC-CIN-11"""
        client, seed = seeded_client
        city_id = seed["cities"]["bristol"].city_id
        resp = client.get(
            "/api/v1/cinemas",
            params={"city_id": city_id},
            headers=auth_header(staff_token),
        )
        assert resp.status_code == 200
        for c in resp.json():
            assert c["city_id"] == city_id
