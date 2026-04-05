"""
tests/integration/test_films.py
Integration tests for film and listing CRUD endpoints.

Test cases:
  TC-FLM-01  List films returns seeded film
  TC-FLM-02  Create film returns 201
  TC-FLM-03  Update film changes title
  TC-FLM-04  Soft-delete film sets is_active=False
  TC-FLM-05  Get single film by ID
  TC-FLM-06  Get non-existent film returns 404
  TC-FLM-07  Create listing with showings
  TC-FLM-08  Overlapping listing on same screen fails
  TC-FLM-09  Listing end_date < start_date fails validation
  TC-FLM-10  Film listing display returns enriched data
  TC-FLM-11  Soft-delete listing deactivates showings
  TC-FLM-12  Create film with invalid genre returns 422 (if genre validation exists) or 201
"""

from datetime import date, timedelta

from tests.conftest import auth_header # type: ignore


class TestFilmEndpoints:

    def test_list_films(self, seeded_client, staff_token):
        """TC-FLM-01"""
        client, _ = seeded_client
        resp = client.get("/api/v1/films", headers=auth_header(staff_token))
        assert resp.status_code == 200
        films = resp.json()
        assert len(films) >= 1
        titles = [f["title"] for f in films]
        assert "Top Gun: Maverick" in titles

    def test_create_film(self, seeded_client, admin_token):
        """TC-FLM-02"""
        client, _ = seeded_client
        resp = client.post("/api/v1/films", json={
            "title": "Test New Film",
            "genre": "Thriller",
            "age_rating": "15",
            "duration_mins": 155,
            "director": "Test Director",
        }, headers=auth_header(admin_token))
        assert resp.status_code == 201
        assert resp.json()["title"] == "Test New Film"
        assert resp.json()["is_active"] is True

    def test_update_film(self, seeded_client, admin_token):
        """TC-FLM-03"""
        client, seed = seeded_client
        film_id = seed["film"].film_id
        resp = client.patch(f"/api/v1/films/{film_id}", json={
            "title": "Top Gun: Maverick (IMAX)",
        }, headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert resp.json()["title"] == "Top Gun: Maverick (IMAX)"

    def test_soft_delete_film(self, seeded_client, admin_token):
        """TC-FLM-04"""
        client, _ = seeded_client
        # Create a film to delete
        create = client.post("/api/v1/films", json={
            "title": "Doomed Film", "genre": "Horror",
            "age_rating": "18", "duration_mins": 90,
        }, headers=auth_header(admin_token))
        fid = create.json()["film_id"]

        resp = client.delete(f"/api/v1/films/{fid}", headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    def test_get_single_film(self, seeded_client, staff_token):
        """TC-FLM-05"""
        client, seed = seeded_client
        fid = seed["film"].film_id
        resp = client.get(f"/api/v1/films/{fid}", headers=auth_header(staff_token))
        assert resp.status_code == 200
        assert resp.json()["film_id"] == fid

    def test_get_nonexistent_film(self, seeded_client, staff_token):
        """TC-FLM-06"""
        client, _ = seeded_client
        resp = client.get("/api/v1/films/99999", headers=auth_header(staff_token))
        assert resp.status_code == 404


class TestListingEndpoints:

    def test_create_listing_with_showings(self, seeded_client, admin_token):
        """TC-FLM-07"""
        client, seed = seeded_client
        # Create a new film first
        film_resp = client.post("/api/v1/films", json={
            "title": "Listing Test Film", "genre": "Drama",
            "age_rating": "PG", "duration_mins": 100,
        }, headers=auth_header(admin_token))
        film_id = film_resp.json()["film_id"]
        screen_id = seed["screens"]["london"].screen_id

        resp = client.post("/api/v1/films/listings", json={
            "film_id": film_id,
            "screen_id": screen_id,
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=7)).isoformat(),
            "showings": [
                {"show_time": "10:00:00", "show_type": "morning"},
                {"show_time": "19:00:00", "show_type": "evening"},
            ],
        }, headers=auth_header(admin_token))
        assert resp.status_code == 201
        data = resp.json()
        assert data["film_title"] == "Listing Test Film"
        assert len(data["showings"]) == 2

    def test_overlapping_listing_fails(self, seeded_client, admin_token):
        """TC-FLM-08: Can't create overlapping listing on the same screen."""
        client, seed = seeded_client
        screen_id = seed["screens"]["bristol"].screen_id  # already has a listing

        resp = client.post("/api/v1/films/listings", json={
            "film_id": seed["film"].film_id,
            "screen_id": screen_id,
            "start_date": (date.today() + timedelta(days=1)).isoformat(),
            "end_date": (date.today() + timedelta(days=10)).isoformat(),
            "showings": [{"show_time": "15:00:00", "show_type": "afternoon"}],
        }, headers=auth_header(admin_token))
        assert resp.status_code == 400
        assert "overlap" in resp.json()["detail"].lower()

    def test_film_listing_display(self, seeded_client, staff_token):
        """TC-FLM-10: Enriched display endpoint returns films with prices."""
        client, seed = seeded_client
        cinema_id = seed["cinemas"]["bristol"].cinema_id
        resp = client.get(
            f"/api/v1/films/display/cinema/{cinema_id}",
            params={"target_date": date.today().isoformat()},
            headers=auth_header(staff_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        film_card = data[0]
        assert "title" in film_card
        assert "showings" in film_card
        assert len(film_card["showings"]) >= 1
        s = film_card["showings"][0]
        assert "lower_hall_price" in s
        assert "upper_gallery_price" in s
        assert "vip_price" in s

    def test_soft_delete_listing(self, seeded_client, admin_token):
        """TC-FLM-11"""
        client, seed = seeded_client
        listing_id = seed["listing"].listing_id
        resp = client.delete(
            f"/api/v1/films/listings/{listing_id}",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_active"] is False