# ============================================
# Author: Garima Adhikari
# Student ID: 24000896
# Last Edited: 2026-04-25
# ============================================

"""
desktop/ui/windows/booking_staff/film_listings.py
implements the Film Listings view for Booking Staff to browse scheduled films at a specific cinema.
includes filtering options for Date, Genre, Rating, and Showtime period.
"""

from PyQt6.QtCore import QDate, Qt  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QComboBox,
    QDateEdit,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from desktop.api_client import api
from desktop.ui.theme import (
    ACCENT,
    BORDER,
    GOLD,
    HERO_BG,
    SPACING_LG,
    SPACING_MD,
    SPACING_SM,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WHITE,
    body_font,
    heading_font,
)
from desktop.ui.widgets import (
    Card,
    badge_label,
    heading_label,
    muted_label,
    secondary_button,
    separator,
    show_toast,
    subheading_label,
)


class FilmListingsView(QWidget):
    """a view that enables staff to explore upcoming showtimes and screen availability for films."""

    def __init__(self):
        """initialises the view and fetches the available cinema locations."""
        super().__init__()
        self._all_listings = []
        self._build_ui()
        self._load_cinemas()

    def _build_ui(self):
        """constructs the primary layout including the header, filter controls, and the scrollable cards area."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        # header row with view title and schedule description
        header_content = QVBoxLayout()
        header_content.setSpacing(4)
        header_content.addWidget(heading_label("Film Listings"))
        desc = muted_label(
            "Explore upcoming showtimes, screen availability, and current film schedules"
        )
        header_content.addWidget(desc)

        header = QHBoxLayout()
        header.addLayout(header_content)
        header.addStretch()

        # cinema selection dropdown for choosing which location's schedule to view
        lbl1 = QLabel("Cinema:")
        lbl1.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent; font-weight: 600;")
        header.addWidget(lbl1)
        self.cinema_combo = QComboBox()
        self.cinema_combo.setFixedWidth(260)
        self.cinema_combo.currentIndexChanged.connect(self._on_filters_changed)
        header.addWidget(self.cinema_combo)
        layout.addLayout(header)

        # filter container grouping search and categorisation controls
        filters_container = QVBoxLayout()
        filters_container.setSpacing(SPACING_SM)

        # row 1: Date | Genre | Rating filters
        row1 = QHBoxLayout()
        row1.setSpacing(SPACING_SM)

        lbl2 = QLabel("Date:")
        lbl2.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent; font-weight: 600;")
        row1.addWidget(lbl2)
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setMinimumDate(QDate.currentDate())
        self.date_edit.setMaximumDate(QDate.currentDate().addDays(7))
        self.date_edit.setFixedWidth(130)
        self.date_edit.dateChanged.connect(self._on_filters_changed)
        row1.addWidget(self.date_edit)

        lbl3 = QLabel("Genre:")
        lbl3.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent; font-weight: 600;")
        row1.addWidget(lbl3)
        self.genre_filter = QComboBox()
        self.genre_filter.addItem("All Genres")
        self.genre_filter.addItems(
            [
                "Action",
                "Comedy",
                "Drama",
                "Horror",
                "Sci-Fi",
                "Romance",
                "Thriller",
                "Animation",
                "Documentary",
            ]
        )
        self.genre_filter.setFixedWidth(140)
        self.genre_filter.currentIndexChanged.connect(self._apply_filters)
        row1.addWidget(self.genre_filter)

        lbl4 = QLabel("Rating:")
        lbl4.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent; font-weight: 600;")
        row1.addWidget(lbl4)
        self.rating_filter = QComboBox()
        self.rating_filter.addItems(["All Ratings", "U", "PG", "12A", "12", "15", "18"])
        self.rating_filter.setFixedWidth(110)
        self.rating_filter.currentIndexChanged.connect(self._apply_filters)
        row1.addWidget(self.rating_filter)
        row1.addStretch()
        filters_container.addLayout(row1)

        # row 2: Showtime | Search Title | navigation buttons
        row2 = QHBoxLayout()
        row2.setSpacing(SPACING_SM)

        lbl5 = QLabel("Show:")
        lbl5.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent; font-weight: 600;")
        row2.addWidget(lbl5)
        self.showtime_filter = QComboBox()
        self.showtime_filter.addItems(["All Times", "Morning", "Afternoon", "Evening"])
        self.showtime_filter.setFixedWidth(130)
        self.showtime_filter.currentIndexChanged.connect(self._apply_filters)
        row2.addWidget(self.showtime_filter)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search film title...")
        self.search_input.setFixedWidth(240)
        self.search_input.textChanged.connect(self._apply_filters)
        row2.addWidget(self.search_input)

        row2.addStretch()

        # navigation buttons for quickly changing the selected date
        def _style_nav_btn(btn):
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {HERO_BG};
                    color: {WHITE};
                    border: none;
                    min-height: 34px;
                    max-height: 34px;
                    min-width: 90px;
                    font-weight: 700;
                    border-radius: 6px;
                }}
                QPushButton:hover {{ background-color: #2E2C28; }}
            """)

        prev_btn = secondary_button("\u25c0  Prev")
        _style_nav_btn(prev_btn)
        prev_btn.clicked.connect(self._prev_day)

        next_btn = secondary_button("Next  \u25b6")
        _style_nav_btn(next_btn)
        next_btn.clicked.connect(self._next_day)

        row2.addWidget(prev_btn)
        row2.addWidget(next_btn)
        filters_container.addLayout(row2)

        layout.addLayout(filters_container)
        layout.addWidget(separator())

        # scrollable area for displaying individual film cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(SPACING_MD)
        self.cards_layout.addStretch()

        scroll.setWidget(self.cards_container)
        layout.addWidget(scroll, 1)

    def _load_cinemas(self):
        """fetches the available cinemas from the api and populates the selector."""
        try:
            cinemas = api.get_cinemas()
            self.cinema_combo.blockSignals(True)
            self.cinema_combo.clear()
            for c in cinemas:
                label = (
                    f"{c['cinema_name']} ({c['city_name']})"
                    if c.get("city_name")
                    else c["cinema_name"]
                )
                self.cinema_combo.addItem(label, c["cinema_id"])

            for i in range(self.cinema_combo.count()):
                if self.cinema_combo.itemData(i) == api.cinema_id:
                    self.cinema_combo.setCurrentIndex(i)
                    break

            self.cinema_combo.blockSignals(False)
            self._load_listings()
        except Exception as e:
            show_toast(self, f"Failed to load cinemas: {e}", success=False)

    def _on_filters_changed(self):
        """triggers a fresh listings reload when primary filters like Cinema or Date change."""
        self._load_listings()

    def _prev_day(self):
        current = self.date_edit.date()
        new_date = current.addDays(-1)
        if new_date >= QDate.currentDate():
            self.date_edit.setDate(new_date)

    def _next_day(self):
        """advances the selected date by one day within the allowed 7-day range."""
        current = self.date_edit.date()
        new_date = current.addDays(1)
        if new_date <= QDate.currentDate().addDays(7):
            self.date_edit.setDate(new_date)

    def _load_listings(self):
        """fetches scheduled film listings from the api based on current location and date."""
        cinema_id = self.cinema_combo.currentData()
        if not cinema_id:
            return

        target_date = self.date_edit.date().toPyDate().isoformat()

        try:
            self._all_listings = api.get_film_listings(cinema_id, target_date)
        except Exception as e:
            show_toast(self, f"Failed to load listings: {e}", success=False)
            self._all_listings = []

        self._apply_filters()

    def _apply_filters(self):
        """filters the loaded listings by Genre, Rating, Showtime period, and search text."""
        filtered = list(self._all_listings)

        genre = self.genre_filter.currentText()
        if genre != "All Genres":
            filtered = [f for f in filtered if f.get("genre", "").lower() == genre.lower()]

        rating = self.rating_filter.currentText()
        if rating != "All Ratings":
            filtered = [f for f in filtered if f.get("age_rating", "").upper() == rating.upper()]

        showtime = self.showtime_filter.currentText()
        if showtime != "All Times":
            st = showtime.lower()
            filtered = [
                f
                for f in filtered
                if any(s.get("show_type", "") == st for s in f.get("showings", []))
            ]

        search = self.search_input.text().strip().lower()
        if search:
            filtered = [f for f in filtered if search in f.get("title", "").lower()]

        self._render_cards(filtered)

    def _render_cards(self, listings: list):
        """clears existing cards and renders the new filtered list of film listings."""
        # clear existing cards from the layout
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not listings:
            empty = QLabel("No films match the current filters.")
            empty.setFont(body_font(12))
            empty.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent; padding: 40px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cards_layout.insertWidget(0, empty)
            return

        for film_data in listings:
            card = self._build_film_card(film_data)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

    def _build_film_card(self, data: dict) -> Card:
        """constructs a detailed Card widget for a single film listing."""
        card = Card()

        # title row containing film name and various badges
        title_row = QHBoxLayout()
        title_lbl = subheading_label(data["title"], 14)
        title_row.addWidget(title_lbl)
        title_row.addStretch()

        if data.get("imdb_rating"):
            rating = badge_label(f"\u2605 {data['imdb_rating']}", GOLD)
            title_row.addWidget(rating)

        genre_badge = badge_label(data["genre"], ACCENT)
        title_row.addWidget(genre_badge)

        age_badge = badge_label(data["age_rating"], HERO_BG)
        title_row.addWidget(age_badge)

        card.add_layout(title_row)

        # meta information line containing duration, director, and screen number
        meta_parts = []
        if data.get("duration_display"):
            meta_parts.append(data["duration_display"])
        if data.get("director"):
            meta_parts.append(f"Dir: {data['director']}")
        meta_parts.append(f"Screen {data['screen_number']}")

        meta = muted_label(" \u00b7 ".join(meta_parts))
        card.add(meta)

        # detailed film description
        if data.get("description"):
            desc = QLabel(data["description"])
            desc.setFont(body_font(10))
            desc.setStyleSheet(
                f"color: {TEXT_SECONDARY}; background: transparent; margin-top: 4px;"
            )
            desc.setWordWrap(True)
            card.add(desc)

        # cast members list
        if data.get("cast_list"):
            cast = muted_label(f"Cast: {data['cast_list']}")
            cast.setWordWrap(True)
            card.add(cast)

        card.add(separator())

        # showings section displaying available times and starting prices
        showings_container = QVBoxLayout()
        showings_container.setSpacing(SPACING_SM)

        show_label = QLabel("Available Showings")
        show_label.setFont(body_font(10, bold=True))
        show_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; background: transparent; margin-bottom: 4px;"
        )
        showings_container.addWidget(show_label)

        showings_row = QHBoxLayout()
        showings_row.setSpacing(SPACING_SM)

        for s in data.get("showings", []):
            show_time = s["show_time"]
            if isinstance(show_time, str) and len(show_time) > 5:
                show_time = show_time[:5]

            show_widget = QFrame()
            show_widget.setStyleSheet(
                f"background: #F9F9F8; border: 1px solid {BORDER}; "
                f"border-radius: 6px; padding: 4px;"
            )
            sw_layout = QVBoxLayout(show_widget)
            sw_layout.setContentsMargins(12, 8, 12, 8)
            sw_layout.setSpacing(2)

            time_lbl = QLabel(str(show_time))
            time_lbl.setFont(heading_font(12, bold=True))
            time_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            time_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent; border: none;")
            sw_layout.addWidget(time_lbl)

            type_lbl = QLabel(s["show_type"].capitalize())
            type_lbl.setFont(body_font(8, bold=True))
            type_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            type_lbl.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent; border: none;")
            sw_layout.addWidget(type_lbl)

            price_lbl = QLabel(f"from \u00a3{s['lower_hall_price']:.2f}")
            price_lbl.setFont(body_font(9, bold=True))
            price_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            price_lbl.setStyleSheet(f"color: {ACCENT}; background: transparent; border: none;")
            sw_layout.addWidget(price_lbl)

            showings_row.addWidget(show_widget)

        showings_row.addStretch()
        showings_container.addLayout(showings_row)
        card.add_layout(showings_container)

        return card
