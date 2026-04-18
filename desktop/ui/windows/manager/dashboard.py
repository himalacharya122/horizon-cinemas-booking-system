"""
desktop/ui/windows/manager/dashboard.py
Manager dashboard: cross-cinema overview with key stats.
"""

from datetime import date

from PyQt6.QtCore import Qt  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from desktop.api_client import api
from desktop.ui.theme import (
    ACCENT,
    DANGER,
    GOLD,
    SPACING_LG,
    SPACING_MD,
    SPACING_SM,
    SUCCESS,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    body_font,
    heading_font,
)
from desktop.ui.widgets import (
    Card,
    error_dialog,
    heading_label,
    primary_button,
    separator,
)


class DashboardView(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        header = QHBoxLayout()
        header.addWidget(heading_label("Manager Dashboard"))
        header.addStretch()

        refresh_btn = primary_button("Refresh")
        refresh_btn.clicked.connect(self._load_data)
        header.addWidget(refresh_btn)

        layout.addLayout(header)
        layout.addWidget(separator())

        # Stats grid
        self.grid = QGridLayout()
        self.grid.setSpacing(SPACING_MD)

        self.cinema_card = self._stat_card("0", "Total Cinemas", ACCENT)
        self.grid.addWidget(self.cinema_card, 0, 0)

        self.staff_card = self._stat_card("0", "Active Staff", SUCCESS)
        self.grid.addWidget(self.staff_card, 0, 1)

        self.bookings_card = self._stat_card("0", "Bookings This Month", GOLD)
        self.grid.addWidget(self.bookings_card, 0, 2)

        self.revenue_card = self._stat_card("\u00a30", "Revenue This Month", SUCCESS)
        self.grid.addWidget(self.revenue_card, 0, 3)

        self.cancellations_card = self._stat_card("0", "Cancellations", DANGER)
        self.grid.addWidget(self.cancellations_card, 1, 0)

        self.films_card = self._stat_card("0", "Active Films", ACCENT)
        self.grid.addWidget(self.films_card, 1, 1)

        self.screens_card = self._stat_card("0", "Total Screens", TEXT_SECONDARY)
        self.grid.addWidget(self.screens_card, 1, 2)

        self.cities_card = self._stat_card("0", "Cities", TEXT_SECONDARY)
        self.grid.addWidget(self.cities_card, 1, 3)

        layout.addLayout(self.grid)

        # Cinema breakdown
        layout.addSpacing(SPACING_MD)
        layout.addWidget(heading_label("Cinema Breakdown", size=14))

        self.breakdown_layout = QVBoxLayout()
        self.breakdown_layout.setSpacing(SPACING_SM)
        layout.addLayout(self.breakdown_layout)

        layout.addStretch(1)

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _stat_card(self, value: str, label: str, color: str) -> Card:
        card = Card()
        val_lbl = QLabel(value)
        val_lbl.setFont(heading_font(22))
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        val_lbl.setStyleSheet(f"color: {color}; background: transparent; font-weight: 700;")
        val_lbl.setObjectName("stat_value")
        card.add(val_lbl)

        title = QLabel(label)
        title.setFont(body_font(9))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        card.add(title)
        return card

    def _update_stat(self, card: Card, value: str):
        lbl = card.findChild(QLabel, "stat_value")
        if lbl:
            lbl.setText(value)

    def _load_data(self):
        today = date.today()
        y, m = today.year, today.month

        try:
            # Cinemas
            cinemas = api.get_cinemas()
            self._update_stat(self.cinema_card, str(len(cinemas)))

            total_screens = sum(len(c.get("screens", [])) for c in cinemas)
            self._update_stat(self.screens_card, str(total_screens))

            # Cities
            cities = api.get_cities()
            self._update_stat(self.cities_card, str(len(cities)))

            # Staff
            users = api.get_users(active_only=True)
            self._update_stat(self.staff_card, str(len(users)))

            # Films
            films = api.get_films(active_only=True)
            self._update_stat(self.films_card, str(len(films)))

            # Revenue
            rev_data = api.report_revenue(y, m)
            total_bookings = sum(d["total_bookings"] for d in rev_data)
            total_revenue = sum(d["total_revenue"] for d in rev_data)
            total_cancellations = sum(d["cancellations"] for d in rev_data)

            self._update_stat(self.bookings_card, str(total_bookings))
            self._update_stat(self.revenue_card, f"\u00a3{total_revenue:,.2f}")
            self._update_stat(self.cancellations_card, str(total_cancellations))

            # Cinema breakdown
            # Clear old
            while self.breakdown_layout.count():
                item = self.breakdown_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            for rd in rev_data:
                row_card = Card()
                row_lbl = QLabel(
                    f"{rd['cinema_name']}  ({rd['city_name']})   \u2014   "
                    f"Bookings: {rd['total_bookings']}   |   "
                    f"Revenue: \u00a3{rd['total_revenue']:,.2f}   |   "
                    f"Cancellations: {rd['cancellations']}"
                )
                row_lbl.setFont(body_font(10))
                row_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent;")
                row_lbl.setWordWrap(True)
                row_card.add(row_lbl)
                self.breakdown_layout.addWidget(row_card)

        except Exception as e:
            error_dialog(self, f"Dashboard error: {e}")
