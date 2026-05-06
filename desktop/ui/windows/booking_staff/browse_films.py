# ============================================
# Author: Garima Adhikari
# Student ID: 24000896
# Last Edited: 2026-04-25
# ============================================

"""
desktop/ui/windows/booking_staff/browse_films.py
implements the Browse All Films view for Booking Staff to explore the complete movie catalogue.
provides filtering capabilities by title, director, cast, genre, and age rating.
"""

from PyQt6.QtCore import Qt  # type: ignore
from PyQt6.QtGui import QColor  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from desktop.api_client import api
from desktop.ui.theme import (
    ACCENT,
    BORDER,
    DANGER,
    HERO_BG,
    RADIUS,
    SPACING_LG,
    SPACING_MD,
    SPACING_SM,
    SUCCESS,
    TEXT_SECONDARY,
    WHITE,
    body_font,
)
from desktop.ui.widgets import (
    error_dialog,
    heading_label,
    muted_label,
    secondary_button,
    separator,
)


class BrowseAllFilmsView(QWidget):
    """a view providing a searchable and filterable table of all films in the catalogue."""

    def __init__(self):
        """initialises the view and fetches the film dataset from the API."""
        super().__init__()
        self._all_films = []
        self._build_ui()
        self._load_films()

    def _build_ui(self):
        """constructs the primary layout including search filters and the film data table."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        # header section with view title and catalog description
        header_content = QVBoxLayout()
        header_content.setSpacing(4)
        header_content.addWidget(heading_label("Browse All Films"))
        desc = muted_label(
            "Complete movie catalog with ratings, genres, and detailed cinematic information"
        )
        header_content.addWidget(desc)

        header = QHBoxLayout()
        header.addLayout(header_content)
        header.addStretch()

        refresh_btn = secondary_button("Refresh")
        refresh_btn.setStyleSheet(
            f"QPushButton {{ background-color: {HERO_BG}; color: {WHITE}; border: none; "
            f"min-height: 34px; max-height: 34px; min-width: 140px; font-weight: 700; "
            f"border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: #2E2C28; }}"
        )
        refresh_btn.clicked.connect(self._load_films)
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        # filter row for searching and categorising films
        filter_row = QHBoxLayout()
        filter_row.setSpacing(SPACING_SM)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by title, director, cast...")
        self.search_input.setFixedWidth(300)
        self.search_input.textChanged.connect(self._apply_filters)
        filter_row.addWidget(self.search_input)

        lbl1 = QLabel("Genre:")
        lbl1.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent; font-weight: 600;")
        filter_row.addWidget(lbl1)
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

        lbl2 = QLabel("Rating:")
        lbl2.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent; font-weight: 600;")
        filter_row.addWidget(lbl2)
        self.rating_filter = QComboBox()
        self.rating_filter.addItems(["All Ratings", "U", "PG", "12A", "12", "15", "18"])
        self.rating_filter.setFixedWidth(120)
        self.rating_filter.currentIndexChanged.connect(self._apply_filters)
        filter_row.addWidget(self.rating_filter)

        filter_row.addStretch()
        layout.addLayout(filter_row)
        layout.addWidget(separator())

        # data table for displaying film details
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setGridStyle(Qt.PenStyle.NoPen)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["Title", "Genre", "Age Rating", "Duration", "Director", "IMDb", "Cast", "Status"]
        )

        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {WHITE};
                alternate-background-color: #F9F9F8;
                border: 1px solid {BORDER};
                border-radius: {RADIUS};
            }}
            QTableWidget::item {{
                border-left: 10px solid transparent;
            }}
        """)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        hh.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.table.setColumnWidth(0, 200)  # Title
        self.table.setColumnWidth(1, 120)  # Genre
        self.table.setColumnWidth(2, 100)  # Age Rating
        self.table.setColumnWidth(3, 100)  # Duration
        self.table.setColumnWidth(4, 180)  # Director
        self.table.setColumnWidth(5, 100)  # IMDb
        self.table.setColumnWidth(7, 100)  # Status

        hh.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)  # Cast

        layout.addWidget(self.table, 1)

        self.count_label = muted_label("")
        layout.addWidget(self.count_label)

    def _load_films(self):
        """fetches the active film list from the api and updates the view."""
        try:
            self._all_films = api.get_films(active_only=True)
            self._apply_filters()
        except Exception as e:
            error_dialog(self, f"Failed to load films: {e}")

    def _apply_filters(self):
        """applies current search terms and dropdown selections to the visible film list."""
        filtered = list(self._all_films)

        search = self.search_input.text().strip().lower()
        if search:
            filtered = [
                f
                for f in filtered
                if search in f.get("title", "").lower()
                or search in (f.get("director", "") or "").lower()
                or search in (f.get("cast_list", "") or "").lower()
            ]

        genre = self.genre_filter.currentText()
        if genre != "All Genres":
            filtered = [f for f in filtered if f.get("genre", "").lower() == genre.lower()]

        rating = self.rating_filter.currentText()
        if rating != "All Ratings":
            filtered = [f for f in filtered if f.get("age_rating", "").upper() == rating.upper()]

        self._fill_table(filtered)

    def _fill_table(self, films: list):
        """populates the QTableWidget with the provided list of films."""
        self.table.setRowCount(len(films))
        f_body = body_font(10)

        for row, f in enumerate(films):
            # title column
            it0 = QTableWidgetItem(f["title"])
            it0.setFont(f_body)
            self.table.setItem(row, 0, it0)

            # film genre
            it1 = QTableWidgetItem(f.get("genre", ""))
            it1.setFont(f_body)
            self.table.setItem(row, 1, it1)

            # age rating certification
            it2 = QTableWidgetItem(f.get("age_rating", ""))
            it2.setFont(f_body)
            self.table.setItem(row, 2, it2)

            # duration in minutes
            it3 = QTableWidgetItem(f"{f.get('duration_mins', '')} min")
            it3.setFont(f_body)
            self.table.setItem(row, 3, it3)

            # primary director
            it4 = QTableWidgetItem(f.get("director", "") or "\u2014")
            it4.setFont(f_body)
            self.table.setItem(row, 4, it4)

            # IMDb rating with visual star indicator
            imdb = f.get("imdb_rating")
            it5 = QTableWidgetItem(f"\u2605 {imdb}" if imdb else "\u2014")
            it5.setFont(body_font(10, bold=True))
            if imdb:
                it5.setForeground(QColor(ACCENT))
            self.table.setItem(row, 5, it5)

            # cast list snippet
            it6 = QTableWidgetItem(f.get("cast_list", "") or "\u2014")
            it6.setFont(f_body)
            self.table.setItem(row, 6, it6)

            # current catalogue status
            is_active = f.get("is_active")
            it7 = QTableWidgetItem("Active" if is_active else "Inactive")
            it7.setFont(body_font(10, bold=True))
            it7.setForeground(QColor(SUCCESS if is_active else DANGER))
            self.table.setItem(row, 7, it7)

        self.count_label.setText(f"Showing {len(films)} of {len(self._all_films)} films")
