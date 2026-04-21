"""
desktop/api_client.py
Synchronous HTTP client for the PyQt6 GUI to talk to the FastAPI backend.
Wraps httpx and handles JWT token management.
"""

from typing import Optional

import httpx

from config.settings import API_HOST, API_PORT


class ApiClient:
    """
    Thin wrapper around httpx that:
    - stores the JWT token after login
    - attaches Authorization header to every request
    - provides typed helper methods for common operations
    """

    def __init__(self):
        self.base_url = f"http://{API_HOST}:{API_PORT}/api/v1"
        self.token: Optional[str] = None
        self.user: Optional[dict] = None
        self._client = httpx.Client(timeout=15.0)

    # Auth
    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def login(self, username: str, password: str) -> dict:
        resp = self._client.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password},
        )
        resp.raise_for_status()
        data = resp.json()
        self.token = data["access_token"]
        self.user = data["user"]
        return data

    def logout(self):
        self.token = None
        self.user = None

    @property
    def is_authenticated(self) -> bool:
        return self.token is not None

    @property
    def user_id(self) -> int:
        return self.user.get("user_id", 0) if self.user else 0

    @property
    def username(self) -> str:
        return self.user.get("username", "") if self.user else ""

    @property
    def role(self) -> str:
        return self.user.get("role", "") if self.user else ""

    @property
    def cinema_id(self) -> int:
        return self.user.get("cinema_id", 0) if self.user else 0

    @property
    def display_name(self) -> str:
        return self.user.get("full_name", "") if self.user else ""

    @property
    def cinema_name(self) -> str:
        return self.user.get("cinema_name", "") if self.user else ""

    # Generic request helpers
    def get(self, path: str, params: dict = None) -> dict | list:
        resp = self._client.get(f"{self.base_url}{path}", headers=self._headers(), params=params)
        resp.raise_for_status()
        return resp.json()

    def post(self, path: str, json: dict = None) -> dict | list:
        resp = self._client.post(f"{self.base_url}{path}", headers=self._headers(), json=json)
        resp.raise_for_status()
        return resp.json()

    def patch(self, path: str, json: dict = None) -> dict | list:
        resp = self._client.patch(f"{self.base_url}{path}", headers=self._headers(), json=json)
        resp.raise_for_status()
        return resp.json()

    def delete(self, path: str) -> dict | list:
        resp = self._client.delete(f"{self.base_url}{path}", headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    # Typed convenience methods
    # Films
    def get_films(self, active_only: bool = True) -> list:
        return self.get("/films", {"active_only": active_only})

    def get_film_listings(self, cinema_id: int, target_date: str) -> list:
        return self.get(f"/films/display/cinema/{cinema_id}", {"target_date": target_date})

    def get_all_listings(self, target_date: str = None, city_id: int = None) -> list:
        params = {}
        if target_date:
            params["target_date"] = target_date
        if city_id:
            params["city_id"] = city_id
        return self.get("/films/listings/all", params)

    def create_film(self, data: dict) -> dict:
        return self.post("/films", data)

    def update_film(self, film_id: int, data: dict) -> dict:
        return self.patch(f"/films/{film_id}", data)

    def delete_film(self, film_id: int) -> dict:
        return self.delete(f"/films/{film_id}")

    # Listings
    def create_listing(self, data: dict) -> dict:
        return self.post("/films/listings", data)

    def update_listing(self, listing_id: int, data: dict) -> dict:
        return self.patch(f"/films/listings/{listing_id}", data)

    def delete_listing(self, listing_id: int) -> dict:
        return self.delete(f"/films/listings/{listing_id}")

    # Bookings
    def check_availability(self, data: dict) -> dict:
        return self.post("/bookings/check-availability", data)

    def create_booking(self, data: dict) -> dict:
        return self.post("/bookings", data)

    def cancel_booking(self, reference: str) -> dict:
        return self.post("/bookings/cancel", {"booking_reference": reference})

    def get_booking(self, reference: str) -> dict:
        return self.get(f"/bookings/reference/{reference}")

    def search_bookings(self, **params) -> list:
        return self.get("/bookings/search", {k: v for k, v in params.items() if v is not None})

    # Cinemas
    def get_cities(self) -> list:
        return self.get("/cinemas/cities")

    def get_cinemas(self, city_id: int = None) -> list:
        params = {"city_id": city_id} if city_id else {}
        return self.get("/cinemas", params)

    def get_cinema(self, cinema_id: int) -> dict:
        return self.get(f"/cinemas/{cinema_id}")

    def create_cinema(self, data: dict) -> dict:
        return self.post("/cinemas", data)

    def add_screen(self, cinema_id: int, data: dict) -> dict:
        return self.post(f"/cinemas/{cinema_id}/screens", data)

    def get_prices(self, city_id: int = None) -> list:
        params = {"city_id": city_id} if city_id else {}
        return self.get("/cinemas/prices", params)

    def set_price(self, data: dict) -> dict:
        return self.post("/cinemas/prices", data)

    # Reports
    def report_revenue(self, year: int, month: int, cinema_id: int = None) -> list:
        params = {"year": year, "month": month}
        if cinema_id:
            params["cinema_id"] = cinema_id
        return self.get("/reports/revenue", params)

    def report_bookings_per_listing(self, cinema_id: int = None) -> list:
        params = {"cinema_id": cinema_id} if cinema_id else {}
        return self.get("/reports/bookings-per-listing", params)

    def report_top_films(self, year: int, month: int, limit: int = 10) -> list:
        return self.get("/reports/top-films", {"year": year, "month": month, "limit": limit})

    def report_staff_bookings(self, year: int, month: int, cinema_id: int = None) -> list:
        params = {"year": year, "month": month}
        if cinema_id:
            params["cinema_id"] = cinema_id
        return self.get("/reports/staff-bookings", params)

    def report_occupancy(self, year: int, month: int, cinema_id: int = None) -> list:
        params = {"year": year, "month": month}
        if cinema_id:
            params["cinema_id"] = cinema_id
        return self.get("/reports/occupancy", params)

    def report_cancellation_rate(self, year: int, month: int, cinema_id: int = None) -> list:
        params = {"year": year, "month": month}
        if cinema_id:
            params["cinema_id"] = cinema_id
        return self.get("/reports/cancellation-rate", params)

    # Users (Admin)
    def get_users(self, cinema_id: int = None, role: str = None, active_only: bool = True) -> list:
        params = {"active_only": active_only}
        if cinema_id:
            params["cinema_id"] = cinema_id
        if role:
            params["role"] = role
        return self.get("/users", params)

    def reset_user_password(self, user_id: int) -> dict:
        return self.post(f"/users/{user_id}/reset-password")

    def toggle_user_active(self, user_id: int) -> dict:
        return self.post(f"/users/{user_id}/toggle-active")

    def get_user_activity(self, user_id: int, limit: int = 50) -> list:
        return self.get(f"/users/{user_id}/activity", {"limit": limit})

    def create_user(self, data: dict) -> dict:
        return self.post("/users", data)

    def change_password(self, current_password: str, new_password: str) -> dict:
        return self.post(
            "/users/me/change-password",
            {"current_password": current_password, "new_password": new_password},
        )

    # AI Analytics
    def post_ai_query(self, query: str, history: list = None, session_id: int = None) -> dict:
        payload = {"query": query}
        if history:
            payload["history"] = history
        if session_id:
            payload["session_id"] = session_id
        return self.post("/ai/query", payload)

    def get_ai_sessions(self) -> list:
        return self.get("/ai/sessions")

    def create_ai_session(self) -> dict:
        return self.post("/ai/sessions")

    def get_ai_session_messages(self, session_id: int) -> list:
        return self.get(f"/ai/sessions/{session_id}/messages")


# Singleton instance — shared across all windows
api = ApiClient()
