"""
desktop/ui/windows/booking_staff/browse_films.py
Browse All Films — view the full film catalogue regardless of listings.
"""

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
    SPACING_LG,
    SPACING_MD,
    SPACING_SM,
    TEXT_SECONDARY,
)
from desktop.ui.widgets import (
    error_dialog,
    heading_label,
    muted_label,
    secondary_button,
    separator,
)


class BrowseAllFilmsView(QWidget):
    def __init__(self):
        super().__init__()
        self._all_films = []
        self._build_ui()
        self._load_films()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        header = QHBoxLayout()
        header.addWidget(heading_label("Browse All Films"))
        header.addStretch()

        refresh_btn = secondary_button("Refresh")
        refresh_btn.clicked.connect(self._load_films)
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        # Filters
        filter_row = QHBoxLayout()
        filter_row.setSpacing(SPACING_SM)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by title, director, cast...")
        self.search_input.setFixedWidth(300)
        self.search_input.textChanged.connect(self._apply_filters)
        filter_row.addWidget(self.search_input)

        lbl1 = QLabel("Genre:")
        lbl1.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
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
        lbl2.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        filter_row.addWidget(lbl2)
        self.rating_filter = QComboBox()
        self.rating_filter.addItems(["All Ratings", "U", "PG", "12A", "12", "15", "18"])
        self.rating_filter.setFixedWidth(120)
        self.rating_filter.currentIndexChanged.connect(self._apply_filters)
        filter_row.addWidget(self.rating_filter)

        filter_row.addStretch()
        layout.addLayout(filter_row)
        layout.addWidget(separator())

        # Table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["Title", "Genre", "Age Rating", "Duration", "Director", "IMDb", "Cast", "Status"]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)

        self.count_label = muted_label("")
        layout.addWidget(self.count_label)

    def _load_films(self):
        try:
            self._all_films = api.get_films(active_only=True)
            self._apply_filters()
        except Exception as e:
            error_dialog(self, f"Failed to load films: {e}")

    def _apply_filters(self):
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
        self.table.setRowCount(len(films))
        for row, f in enumerate(films):
            self.table.setItem(row, 0, QTableWidgetItem(f["title"]))
            self.table.setItem(row, 1, QTableWidgetItem(f.get("genre", "")))
            self.table.setItem(row, 2, QTableWidgetItem(f.get("age_rating", "")))
            self.table.setItem(row, 3, QTableWidgetItem(f"{f.get('duration_mins', '')} min"))
            self.table.setItem(row, 4, QTableWidgetItem(f.get("director", "") or "\u2014"))
            imdb = f.get("imdb_rating")
            self.table.setItem(row, 5, QTableWidgetItem(f"\u2605 {imdb}" if imdb else "\u2014"))
            self.table.setItem(row, 6, QTableWidgetItem(f.get("cast_list", "") or "\u2014"))
            self.table.setItem(
                row, 7, QTableWidgetItem("Active" if f.get("is_active") else "Inactive")
            )

        self.count_label.setText(f"Showing {len(films)} of {len(self._all_films)} films")
