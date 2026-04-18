"""
desktop/ui/windows/booking_staff/film_listings.py
Film Listings — browse films at a cinema for a chosen date.
Includes genre, rating, and showtime filters.
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
    BG_DARK,
    BG_HOVER,
    BORDER,
    GOLD,
    SPACING_LG,
    SPACING_MD,
    SPACING_SM,
    TEXT_MUTED,
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
    def __init__(self):
        super().__init__()
        self._all_listings = []
        self._build_ui()
        self._load_cinemas()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        # Header row
        header = QHBoxLayout()
        header.addWidget(heading_label("Film Listings"))
        header.addStretch()

        # Cinema selector
        self.cinema_combo = QComboBox()
        self.cinema_combo.setFixedWidth(260)
        self.cinema_combo.currentIndexChanged.connect(self._on_filters_changed)
        lbl1 = QLabel("Cinema:")
        lbl1.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        header.addWidget(lbl1)
        header.addWidget(self.cinema_combo)

        # Date selector
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setMinimumDate(QDate.currentDate())
        self.date_edit.setMaximumDate(QDate.currentDate().addDays(7))
        self.date_edit.setFixedWidth(140)
        self.date_edit.dateChanged.connect(self._on_filters_changed)
        lbl2 = QLabel("Date:")
        lbl2.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        header.addWidget(lbl2)
        header.addWidget(self.date_edit)

        layout.addLayout(header)

        # Filter row
        filter_row = QHBoxLayout()
        filter_row.setSpacing(SPACING_SM)

        # Genre filter
        lbl3 = QLabel("Genre:")
        lbl3.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        filter_row.addWidget(lbl3)
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
        self.genre_filter.setFixedWidth(150)
        self.genre_filter.currentIndexChanged.connect(self._apply_filters)
        filter_row.addWidget(self.genre_filter)

        # Rating filter
        lbl4 = QLabel("Rating:")
        lbl4.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        filter_row.addWidget(lbl4)
        self.rating_filter = QComboBox()
        self.rating_filter.addItems(["All Ratings", "U", "PG", "12A", "12", "15", "18"])
        self.rating_filter.setFixedWidth(120)
        self.rating_filter.currentIndexChanged.connect(self._apply_filters)
        filter_row.addWidget(self.rating_filter)

        # Showtime filter
        lbl5 = QLabel("Show:")
        lbl5.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        filter_row.addWidget(lbl5)
        self.showtime_filter = QComboBox()
        self.showtime_filter.addItems(["All Times", "Morning", "Afternoon", "Evening"])
        self.showtime_filter.setFixedWidth(130)
        self.showtime_filter.currentIndexChanged.connect(self._apply_filters)
        filter_row.addWidget(self.showtime_filter)

        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search film title...")
        self.search_input.setFixedWidth(200)
        self.search_input.textChanged.connect(self._apply_filters)
        filter_row.addWidget(self.search_input)

        filter_row.addStretch()

        # Day nav buttons
        prev_btn = secondary_button("\u25c0  Prev")
        prev_btn.setFixedWidth(90)
        prev_btn.clicked.connect(self._prev_day)
        next_btn = secondary_button("Next  \u25b6")
        next_btn.setFixedWidth(90)
        next_btn.clicked.connect(self._next_day)
        filter_row.addWidget(prev_btn)
        filter_row.addWidget(next_btn)

        layout.addLayout(filter_row)
        layout.addWidget(separator())

        # Scrollable film cards
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
        self._load_listings()

    def _prev_day(self):
        current = self.date_edit.date()
        new_date = current.addDays(-1)
        if new_date >= QDate.currentDate():
            self.date_edit.setDate(new_date)

    def _next_day(self):
        current = self.date_edit.date()
        new_date = current.addDays(1)
        if new_date <= QDate.currentDate().addDays(7):
            self.date_edit.setDate(new_date)

    def _load_listings(self):
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
        """Filter the loaded listings by genre, rating, showtime, search text."""
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
        # Clear existing cards
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
        card = Card()

        # Title row
        title_row = QHBoxLayout()
        title_lbl = subheading_label(data["title"], 14)
        title_row.addWidget(title_lbl)
        title_row.addStretch()

        if data.get("imdb_rating"):
            rating = badge_label(f"\u2605 {data['imdb_rating']}", GOLD)
            title_row.addWidget(rating)

        genre_badge = badge_label(data["genre"], ACCENT)
        title_row.addWidget(genre_badge)

        age_badge = badge_label(data["age_rating"], BG_HOVER)
        title_row.addWidget(age_badge)

        card.add_layout(title_row)

        # Meta line
        meta_parts = []
        if data.get("duration_display"):
            meta_parts.append(data["duration_display"])
        if data.get("director"):
            meta_parts.append(f"Dir: {data['director']}")
        meta_parts.append(f"Screen {data['screen_number']}")

        meta = muted_label(" \u00b7 ".join(meta_parts))
        card.add(meta)

        # Description
        if data.get("description"):
            desc = QLabel(data["description"])
            desc.setFont(body_font(10))
            desc.setStyleSheet(
                f"color: {TEXT_SECONDARY}; background: transparent; margin-top: 4px;"
            )
            desc.setWordWrap(True)
            card.add(desc)

        # Cast
        if data.get("cast_list"):
            cast = muted_label(f"Cast: {data['cast_list']}")
            cast.setWordWrap(True)
            card.add(cast)

        card.add(separator())

        # Showings row
        showings_row = QHBoxLayout()
        showings_row.setSpacing(SPACING_SM)

        show_label = QLabel("Showings:")
        show_label.setFont(body_font(10))
        show_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; background: transparent; font-weight: 600;"
        )
        showings_row.addWidget(show_label)

        for s in data.get("showings", []):
            show_time = s["show_time"]
            if isinstance(show_time, str) and len(show_time) > 5:
                show_time = show_time[:5]

            show_widget = QFrame()
            show_widget.setStyleSheet(
                f"background: {BG_DARK}; border: 1px solid {BORDER}; "
                f"border-radius: 4px; padding: 4px;"
            )
            sw_layout = QVBoxLayout(show_widget)
            sw_layout.setContentsMargins(12, 6, 12, 6)
            sw_layout.setSpacing(2)

            time_lbl = QLabel(str(show_time))
            time_lbl.setFont(heading_font(12, bold=True))
            time_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            time_lbl.setStyleSheet(f"color: {WHITE}; background: transparent; border: none;")
            sw_layout.addWidget(time_lbl)

            type_lbl = QLabel(s["show_type"].capitalize())
            type_lbl.setFont(body_font(8))
            type_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            type_lbl.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent; border: none;")
            sw_layout.addWidget(type_lbl)

            price_lbl = QLabel(f"from \u00a3{s['lower_hall_price']:.2f}")
            price_lbl.setFont(body_font(9))
            price_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            price_lbl.setStyleSheet(
                f"color: {ACCENT}; background: transparent; font-weight: 600; border: none;"
            )
            sw_layout.addWidget(price_lbl)

            showings_row.addWidget(show_widget)

        showings_row.addStretch()
        card.add_layout(showings_row)

        return card
