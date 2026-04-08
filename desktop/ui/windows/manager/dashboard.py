"""
desktop/ui/windows/manager/dashboard.py
implements the Manager dashboard providing a cross-cinema overview of performance metrics.
displays real-time statistics for cinemas, staff, bookings, revenue, and cancellations.
"""

from datetime import date

from PyQt6.QtCore import Qt  # type: ignore
from PyQt6.QtGui import QShowEvent  # type: ignore
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
    HERO_BG,
    SPACING_LG,
    SPACING_MD,
    SPACING_SM,
    SUCCESS,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WHITE,
    body_font,
    heading_font,
)
from desktop.ui.widgets import (
    Card,
    error_dialog,
    heading_label,
    muted_label,
    secondary_button,
    separator,
)


class DashboardView(QWidget):
    """a comprehensive dashboard view for Managers to monitor system-wide activity and metrics."""

    def __init__(self):
        """initialises the dashboard and triggers the data loading process."""
        super().__init__()
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        """constructs the dashboard layout including the stats grid and cinema breakdown section."""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        # header row with title, subtitle, and refresh button
        header_content = QVBoxLayout()
        header_content.setSpacing(4)
        header_content.addWidget(heading_label("Manager Dashboard"))
        header_content.addWidget(
            muted_label(
                "Live overview of cinemas, staff, bookings and revenue across all locations"
            )
        )

        header = QHBoxLayout()
        header.addLayout(header_content)
        header.addStretch()

        self._refresh_btn = secondary_button("Refresh")
        self._refresh_btn.setStyleSheet(
            f"QPushButton {{ background-color: {HERO_BG}; color: {WHITE}; border: none; "
            f"min-height: 34px; max-height: 34px; min-width: 110px; font-weight: 700; "
            f"border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: #2E2C28; }}"
        )
        self._refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._refresh_btn.clicked.connect(self._load_data)
        header.addWidget(self._refresh_btn)

        layout.addLayout(header)
        layout.addWidget(separator())

        # grid layout for displaying key statistics
        self.grid = QGridLayout()
        self.grid.setSpacing(SPACING_MD)

        self.cinema_card = self._stat_card("0", "Total Cinemas", ACCENT)
        self.grid.addWidget(self.cinema_card, 0, 0)

        self.staff_card = self._stat_card("0", "Active Staff", SUCCESS)
        self.grid.addWidget(self.staff_card, 0, 1)

        self.bookings_card = self._stat_card("0", "Bookings This Month", GOLD)
        self.grid.addWidget(self.bookings_card, 0, 2)

        self.revenue_card = self._stat_card("£0", "Revenue This Month", SUCCESS)
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

        # detailed breakdown section for individual cinemas
        layout.addSpacing(SPACING_SM)

        breakdown_header = QHBoxLayout()
        breakdown_lbl = heading_label("Cinema Breakdown", size=14)
        breakdown_header.addWidget(breakdown_lbl)
        breakdown_header.addStretch()
        layout.addLayout(breakdown_header)
        layout.addWidget(separator())

        self.breakdown_layout = QVBoxLayout()
        self.breakdown_layout.setSpacing(SPACING_SM)
        layout.addLayout(self.breakdown_layout)

        layout.addStretch(1)

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _stat_card(self, value: str, label: str, color: str) -> Card:
        """helper to create a Card widget for displaying a single statistic."""
        card = Card()

        val_lbl = QLabel(value)
        val_lbl.setFont(heading_font(24))
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        val_lbl.setStyleSheet(f"color: {color}; background: transparent; font-weight: 700;")
        val_lbl.setObjectName("stat_value")
        card.add(val_lbl)

        title = QLabel(label)
        title.setFont(body_font(9))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent; letter-spacing: 0.3px;")
        card.add(title)
        return card

    def _update_stat(self, card: Card, value: str):
        """updates the text value of a specific stat card."""
        lbl = card.findChild(QLabel, "stat_value")
        if lbl:
            lbl.setText(value)

    def showEvent(self, event: QShowEvent):
        """refreshes dashboard data whenever the view is shown."""
        super().showEvent(event)
        self._load_data()

    def _load_data(self):
        """orchestrates API calls to fetch current month stats and cinema breakdown data."""
        today = date.today()
        y, m = today.year, today.month

        try:
            # fetch cinema and city totals
            cinemas = api.get_cinemas()
            self._update_stat(self.cinema_card, str(len(cinemas)))

            total_screens = sum(len(c.get("screens", [])) for c in cinemas)
            self._update_stat(self.screens_card, str(total_screens))

            # fetch total city count
            cities = api.get_cities()
            self._update_stat(self.cities_card, str(len(cities)))

            # fetch total active staff count
            users = api.get_users(active_only=True)
            self._update_stat(self.staff_card, str(len(users)))

            # fetch total active films count
            films = api.get_films(active_only=True)
            self._update_stat(self.films_card, str(len(films)))

            # calculate aggregated revenue and booking metrics
            rev_data = api.report_revenue(y, m)
            total_bookings = sum(d["total_bookings"] for d in rev_data)
            total_revenue = sum(d["total_revenue"] for d in rev_data)
            total_cancellations = sum(d["cancellations"] for d in rev_data)

            self._update_stat(self.bookings_card, str(total_bookings))
            self._update_stat(self.revenue_card, f"£{total_revenue:,.2f}")
            self._update_stat(self.cancellations_card, str(total_cancellations))

            # clear existing items from the cinema breakdown layout
            while self.breakdown_layout.count():
                item = self.breakdown_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            for rd in rev_data:
                row_card = Card()
                row_inner = QHBoxLayout()
                row_inner.setSpacing(SPACING_MD)

                # cinema name and associated city
                name_col = QVBoxLayout()
                name_col.setSpacing(2)
                name_lbl = QLabel(rd["cinema_name"])
                name_lbl.setFont(body_font(11, bold=True))
                name_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent;")
                city_lbl = QLabel(rd.get("city_name", ""))
                city_lbl.setFont(body_font(9))
                city_lbl.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
                name_col.addWidget(name_lbl)
                name_col.addWidget(city_lbl)
                row_inner.addLayout(name_col)
                row_inner.addStretch()

                # inline statistics for the cinema row
                for label_text, value_text, color in [
                    ("Bookings", str(rd["total_bookings"]), ACCENT),
                    ("Revenue", f"£{rd['total_revenue']:,.2f}", SUCCESS),
                    ("Cancellations", str(rd["cancellations"]), DANGER),
                ]:
                    col = QVBoxLayout()
                    col.setSpacing(2)
                    col.setContentsMargins(SPACING_MD, 0, SPACING_MD, 0)
                    v_lbl = QLabel(value_text)
                    v_lbl.setFont(body_font(12, bold=True))
                    v_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    v_lbl.setStyleSheet(f"color: {color}; background: transparent;")
                    k_lbl = QLabel(label_text)
                    k_lbl.setFont(body_font(9))
                    k_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    k_lbl.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
                    col.addWidget(v_lbl)
                    col.addWidget(k_lbl)
                    row_inner.addLayout(col)

                row_card.add_layout(row_inner)
                self.breakdown_layout.addWidget(row_card)

        except Exception as e:
            error_dialog(self, f"Dashboard error: {e}")
