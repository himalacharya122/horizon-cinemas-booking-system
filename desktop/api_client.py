# ============================================
# Author: Himal Acharya
# Student ID: 22085619
# Last Edited: 2026-04-25
# ============================================

"""
desktop/api_client.py
synchronous HTTP client for the PyQt6 GUI to communicate with the FastAPI backend.
wraps httpx and handles JWT token management and user session state.
"""

from typing import Optional

import httpx

from config.settings import API_HOST, API_PORT


class ApiClient:
    """
    thin wrapper around httpx that manages authentication and provides typed helper methods.
    it stores the JWT token after login and attaches it to the Authorization header of every request.
    """

    def __init__(self):
        """initialises the base_url from config and prepares the internal httpx client."""
        self.base_url = f"http://{API_HOST}:{API_PORT}/api/v1"
        self.token: Optional[str] = None
        self.user: Optional[dict] = None
        self._client = httpx.Client(timeout=15.0)

    # auth management
    def _headers(self) -> dict:
        """returns the standard headers, including the Authorization token if present."""
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def login(self, username: str, password: str) -> dict:
        """authenticates with the backend and stores the returned JWT token and user data."""
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
        """clears the stored authentication token and user profile."""
        self.token = None
        self.user = None

    @property
    def is_authenticated(self) -> bool:
        """checks if a valid token is currently stored."""
        return self.token is not None

    @property
    def user_id(self) -> int:
        """returns the unique ID of the logged-in user."""
        return self.user.get("user_id", 0) if self.user else 0

    @property
    def username(self) -> str:
        """returns the username of the current session."""
        return self.user.get("username", "") if self.user else ""

    @property
    def role(self) -> str:
        """returns the access role (e.g., admin, staff) of the user."""
        return self.user.get("role", "") if self.user else ""

    @property
    def cinema_id(self) -> int:
        """returns the ID of the cinema the user is assigned to."""
        return self.user.get("cinema_id", 0) if self.user else 0

    @property
    def display_name(self) -> str:
        """returns the full name of the user for UI display."""
        return self.user.get("full_name", "") if self.user else ""

    @property
    def cinema_name(self) -> str:
        """returns the name of the assigned cinema."""
        return self.user.get("cinema_name", "") if self.user else ""

    # generic request helpers
    def get(self, path: str, params: dict = None) -> dict | list:
        """performs a GET request and handles the response."""
        resp = self._client.get(f"{self.base_url}{path}", headers=self._headers(), params=params)
        return self._handle_response(resp)

    def post(self, path: str, json: dict = None) -> dict | list:
        """performs a POST request and handles the response."""
        resp = self._client.post(f"{self.base_url}{path}", headers=self._headers(), json=json)
        return self._handle_response(resp)

    def patch(self, path: str, json: dict = None) -> dict | list:
        """performs a PATCH request and handles the response."""
        resp = self._client.patch(f"{self.base_url}{path}", headers=self._headers(), json=json)
        return self._handle_response(resp)

    def delete(self, path: str) -> dict | list:
        """performs a DELETE request and handles the response."""
        resp = self._client.delete(f"{self.base_url}{path}", headers=self._headers())
        return self._handle_response(resp)

    def _handle_response(self, resp) -> dict | list:
        """verifies the response status and parses JSON, returning an empty dict for No Content."""
        resp.raise_for_status()

        if resp.status_code == 204 or not resp.content:
            return {}

        try:
            return resp.json()
        except Exception:
            return {}

    # typed convenience methods for specific API domains

    # films
    def get_films(self, active_only: bool = True) -> list:
        """retrieves a list of all films, optionally filtered by activity status."""
        return self.get("/films", {"active_only": active_only})

    def get_film_listings(self, cinema_id: int, target_date: str) -> list:
        """fetches showtimes for a specific cinema and date."""
        return self.get(f"/films/display/cinema/{cinema_id}", {"target_date": target_date})

    def get_all_listings(self, target_date: str = None, city_id: int = None) -> list:
        """fetches all showtimes across the network with optional date and city filters."""
        params = {}
        if target_date:
            params["target_date"] = target_date
        if city_id:
            params["city_id"] = city_id
        return self.get("/films/listings/all", params)

    def create_film(self, data: dict) -> dict:
        """adds a new film record to the database."""
        return self.post("/films", data)

    def update_film(self, film_id: int, data: dict) -> dict:
        """updates details for an existing film."""
        return self.patch(f"/films/{film_id}", data)

    def delete_film(self, film_id: int) -> dict:
        """removes a film record."""
        return self.delete(f"/films/{film_id}")

    # listings
    def create_listing(self, data: dict) -> dict:
        """schedules a new showing or listing."""
        return self.post("/films/listings", data)

    def update_listing(self, listing_id: int, data: dict) -> dict:
        """modifies an existing listing's details."""
        return self.patch(f"/films/listings/{listing_id}", data)

    def delete_listing(self, listing_id: int) -> dict:
        """removes a scheduled listing."""
        return self.delete(f"/films/listings/{listing_id}")

    # bookings
    def get_seat_map(self, showing_id: int, show_date: str, seat_type: str) -> dict:
        """retrieves the current seat availability and layout for a specific showing."""
        return self.get(
            "/bookings/seat-map",
            {
                "showing_id": showing_id,
                "show_date": show_date,
                "seat_type": seat_type,
            },
        )

    def check_availability(self, data: dict) -> dict:
        """verifies if requested seats are still available before finalising a booking."""
        return self.post("/bookings/check-availability", data)

    def create_booking(self, data: dict) -> dict:
        """submits a new ticket booking."""
        return self.post("/bookings", data)

    def cancel_booking(self, reference: str) -> dict:
        """cancels a booking using its unique reference code."""
        return self.post("/bookings/cancel", {"booking_reference": reference})

    def get_booking(self, reference: str) -> dict:
        """retrieves full details for a booking reference."""
        return self.get(f"/bookings/reference/{reference}")

    def search_bookings(self, **params) -> list:
        """searches for bookings based on various criteria like user_id or date."""
        return self.get("/bookings/search", {k: v for k, v in params.items() if v is not None})

    # cinemas
    def get_cities(self) -> list:
        """retrieves the list of cities where cinemas are located."""
        return self.get("/cinemas/cities")

    def get_cinemas(self, city_id: int = None) -> list:
        """lists all cinemas, optionally filtered by city."""
        params = {"city_id": city_id} if city_id else {}
        return self.get("/cinemas", params)

    def get_cinema(self, cinema_id: int) -> dict:
        """retrieves information for a single cinema."""
        return self.get(f"/cinemas/{cinema_id}")

    def create_cinema(self, data: dict) -> dict:
        """adds a new cinema location."""
        return self.post("/cinemas", data)

    def add_screen(self, cinema_id: int, data: dict) -> dict:
        """registers a new screen (auditorium) for a cinema."""
        return self.post(f"/cinemas/{cinema_id}/screens", data)

    def get_prices(self, city_id: int = None) -> list:
        """fetches current ticket pricing, optionally filtered by city."""
        params = {"city_id": city_id} if city_id else {}
        return self.get("/cinemas/prices", params)

    def set_price(self, data: dict) -> dict:
        """updates or sets ticket prices."""
        return self.post("/cinemas/prices", data)

    # reports
    def report_revenue(self, year: int, month: int, cinema_id: int = None) -> list:
        """generates a revenue report for a given month and year."""
        params = {"year": year, "month": month}
        if cinema_id:
            params["cinema_id"] = cinema_id
        return self.get("/reports/revenue", params)

    def report_bookings_per_listing(self, cinema_id: int = None) -> list:
        """shows booking counts aggregated by listing."""
        params = {"cinema_id": cinema_id} if cinema_id else {}
        return self.get("/reports/bookings-per-listing", params)

    def report_top_films(self, year: int, month: int, limit: int = 10) -> list:
        """identifies the best-performing films based on ticket sales."""
        return self.get("/reports/top-films", {"year": year, "month": month, "limit": limit})

    def report_staff_bookings(self, year: int, month: int, cinema_id: int = None) -> list:
        """tracks booking activity performed by individual staff members."""
        params = {"year": year, "month": month}
        if cinema_id:
            params["cinema_id"] = cinema_id
        return self.get("/reports/staff-bookings", params)

    def report_occupancy(self, year: int, month: int, cinema_id: int = None) -> list:
        """calculates seat occupancy percentages for showings."""
        params = {"year": year, "month": month}
        if cinema_id:
            params["cinema_id"] = cinema_id
        return self.get("/reports/occupancy", params)

    def report_cancellation_rate(self, year: int, month: int, cinema_id: int = None) -> list:
        """reports the ratio of cancelled to total bookings."""
        params = {"year": year, "month": month}
        if cinema_id:
            params["cinema_id"] = cinema_id
        return self.get("/reports/cancellation-rate", params)

    # users (Admin)
    def get_users(self, cinema_id: int = None, role: str = None, active_only: bool = True) -> list:
        """lists system users with optional filters for cinema, role, and activity."""
        params = {"active_only": active_only}
        if cinema_id:
            params["cinema_id"] = cinema_id
        if role:
            params["role"] = role
        return self.get("/users", params)

    def reset_user_password(self, user_id: int) -> dict:
        """forces a password reset for a specific user."""
        return self.post(f"/users/{user_id}/reset-password")

    def toggle_user_active(self, user_id: int) -> dict:
        """enables or disables a user account."""
        return self.post(f"/users/{user_id}/toggle-active")

    def get_user_activity(self, user_id: int, limit: int = 50) -> list:
        """retrieves recent logs for a specific user's actions."""
        return self.get(f"/users/{user_id}/activity", {"limit": limit})

    def create_user(self, data: dict) -> dict:
        """registers a new user account."""
        return self.post("/users", data)

    def change_password(self, current_password: str, new_password: str) -> dict:
        """allows the current user to update their own password."""
        return self.post(
            "/users/me/change-password",
            {"current_password": current_password, "new_password": new_password},
        )

    # AI analytics
    def post_ai_query(self, query: str, history: list = None, session_id: int = None) -> dict:
        """sends a natural language query to the Groq AI service for analysis."""
        payload = {"query": query}
        if history:
            payload["history"] = history
        if session_id:
            payload["session_id"] = session_id
        return self.post("/ai/query", payload)

    def get_ai_sessions(self) -> list:
        """retrieves all previous AI chat sessions for the user."""
        return self.get("/ai/sessions")

    def create_ai_session(self) -> dict:
        """starts a new AI analytical chat session."""
        return self.post("/ai/sessions")

    def get_ai_session_messages(self, session_id: int) -> list:
        """fetches the message history for a specific AI session."""
        return self.get(f"/ai/sessions/{session_id}/messages")

    def delete_ai_session(self, session_id: int):
        """permanently removes an AI session and its history."""
        return self.delete(f"/ai/sessions/{session_id}")

    def rename_ai_session(self, session_id: int, title: str) -> dict:
        """updates the display title of an AI session."""
        return self.patch(f"/ai/sessions/{session_id}", json={"title": title})

    def get_ai_suggestions(self, session_id: Optional[int] = None) -> list[str]:
        """gets context-aware query suggestions from the AI."""
        params = {"session_id": session_id} if session_id else {}
        return self.get("/ai/suggestions", params=params)


# singleton instance — shared across all windows of the application
api = ApiClient()
