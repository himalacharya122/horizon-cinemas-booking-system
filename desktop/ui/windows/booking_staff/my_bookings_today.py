"""
desktop/ui/windows/booking_staff/my_bookings_today.py
implements the My Bookings Today view for Booking Staff.
provides a performance snapshot and a detailed table of reservations processed by the current user on the current date.
"""

from datetime import date

from PyQt6.QtCore import Qt  # type: ignore
from PyQt6.QtGui import QColor  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from desktop.api_client import api
from desktop.ui.theme import (
    BG_DARK,
    BORDER,
    DANGER,
    HERO_BG,
    SPACING_LG,
    SPACING_MD,
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


class MyBookingsTodayView(QWidget):
    """a view providing a summary of the staff member's daily booking activity and revenue."""

    def __init__(self):
        """initialises the view and loads today's booking data from the API."""
        super().__init__()
        self._build_ui()
        self._load_bookings()

    def _build_ui(self):
        """constructs the primary layout including stat cards, the date indicator, and the bookings table."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        # header section with view title and performance description
        header_content = QVBoxLayout()
        header_content.setSpacing(4)
        header_content.addWidget(heading_label("My Bookings Today"))
        desc = muted_label("Instant snapshot of your processed reservations for today's sessions")
        header_content.addWidget(desc)

        header = QHBoxLayout()
        header.addLayout(header_content)
        header.addStretch()

        # current date display indicator
        self.date_label = QLabel(f"Date: {date.today().strftime('%A, %d %B %Y')}")
        self.date_label.setFont(body_font(11))
        self.date_label.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        header.addWidget(self.date_label)

        # refresh button to fetch the latest booking data
        refresh_btn = secondary_button("Refresh")
        refresh_btn.setStyleSheet(
            f"QPushButton {{ background-color: {HERO_BG}; color: {WHITE}; border: none; "
            f"min-height: 34px; max-height: 34px; min-width: 120px; font-weight: 700; "
            f"border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: #2E2C28; }}"
        )
        refresh_btn.clicked.connect(self._load_bookings)
        header.addWidget(refresh_btn)

        layout.addLayout(header)
        layout.addWidget(separator())

        # summary cards for high-level daily statistics
        summary_row = QHBoxLayout()
        summary_row.setSpacing(SPACING_MD)

        self.total_card = self._make_stat_card("Total Bookings", "0")
        self.tickets_card = self._make_stat_card("Tickets Sold", "0")
        self.revenue_card = self._make_stat_card("Revenue Today", "\u00a30.00")
        summary_row.addWidget(self.total_card)
        summary_row.addWidget(self.tickets_card)
        summary_row.addWidget(self.revenue_card)
        summary_row.addStretch()

        layout.addLayout(summary_row)

        # detailed table displaying individual booking transactions
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(38)

        self.table.setStyleSheet(
            f"QTableWidget {{ border: 1px solid {BORDER}; border-radius: 8px; background: {WHITE}; }}"
            f"QHeaderView::section {{ background-color: {BG_DARK}; color: {TEXT_SECONDARY}; "
            f"font-weight: 600; padding: 8px 5px; border: none; border-bottom: 1px solid {BORDER}; "
            f"border-right: 1px solid {BORDER}; border-left: 10px solid transparent; }}"
            f"QTableWidget::item {{ border-left: 10px solid transparent; padding-right: 10px; }}"
        )
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["Reference", "Film", "Show Date", "Time", "Customer", "Tickets", "Total", "Status"]
        )

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(0, 170)  # Reference
        self.table.setColumnWidth(2, 120)  # Show Date
        self.table.setColumnWidth(3, 80)  # Time
        self.table.setColumnWidth(5, 80)  # Tickets
        self.table.setColumnWidth(6, 110)  # Total
        self.table.setColumnWidth(7, 150)  # Status

        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Film
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Customer

        layout.addWidget(self.table, 1)

        self.count_label = muted_label("")
        layout.addWidget(self.count_label)

    def _make_stat_card(self, title: str, value: str) -> Card:
        """helper function to create a styled statistic card with a title and value."""
        card = Card()
        card.setFixedWidth(200)
        card.setFixedHeight(90)

        t = QLabel(title)
        t.setFont(body_font(9, bold=True))
        t.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        card.add(t)

        self._stat_labels = getattr(self, "_stat_labels", {})
        v = QLabel(value)
        v.setFont(heading_font(20))
        v.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent;")
        self._stat_labels[title] = v
        card.add(v)

        return card

    def _load_bookings(self):
        """fetches bookings made by the current user today from the api and updates stats."""
        today = date.today().isoformat()
        try:
            bookings = api.search_bookings(
                booked_by=api.user_id,
                booking_date=today,
            )

            self._fill_table(bookings)

            # update daily statistics labels
            confirmed = [b for b in bookings if b["booking_status"] == "confirmed"]
            total_tickets = sum(b["num_tickets"] for b in confirmed)
            total_revenue = sum(b["total_cost"] for b in confirmed)

            self._stat_labels["Total Bookings"].setText(str(len(bookings)))
            self._stat_labels["Tickets Sold"].setText(str(total_tickets))
            self._stat_labels["Revenue Today"].setText(f"\u00a3{total_revenue:.2f}")

            self.count_label.setText(f"{len(bookings)} booking(s) made today")

        except Exception as e:
            error_dialog(self, f"Failed to load bookings: {e}")

    def _fill_table(self, bookings: list):
        """populates the QTableWidget with individual booking records."""
        self.table.setRowCount(len(bookings))
        for row, b in enumerate(bookings):
            self.table.setItem(row, 0, QTableWidgetItem(b["booking_reference"]))
            self.table.setItem(row, 1, QTableWidgetItem(b.get("film_title", "")))
            self.table.setItem(row, 2, QTableWidgetItem(str(b["show_date"])))
            self.table.setItem(row, 3, QTableWidgetItem(str(b.get("show_time", ""))[:5]))
            self.table.setItem(row, 4, QTableWidgetItem(b["customer_name"]))
            self.table.setItem(row, 5, QTableWidgetItem(str(b["num_tickets"])))
            self.table.setItem(row, 6, QTableWidgetItem(f"\u00a3{b['total_cost']:.2f}"))

            # assign colored status indicators based on booking state
            status_str = b["booking_status"].lower()
            status_item = QTableWidgetItem(status_str.capitalize())
            if status_str == "confirmed":
                status_item.setForeground(QColor(SUCCESS))
            elif status_str == "cancelled":
                status_item.setForeground(QColor(DANGER))

            # make the status text bold for improved visibility
            font = status_item.font()
            font.setBold(True)
            status_item.setFont(font)

            self.table.setItem(row, 7, status_item)
