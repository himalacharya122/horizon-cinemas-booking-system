"""
desktop/ui/windows/booking_staff/my_bookings_today.py
View bookings made by the current staff member today.
"""

from datetime import date
from PyQt6.QtCore import Qt  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
)

from desktop.ui.theme import (
    ACCENT, SUCCESS, WHITE,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    heading_font, body_font, SPACING_MD, SPACING_LG,
)
from desktop.ui.widgets import (
    heading_label, muted_label, primary_button, secondary_button,
    separator, show_toast, error_dialog, Card, badge_label,
)
from desktop.api_client import api


class MyBookingsTodayView(QWidget):

    def __init__(self):
        super().__init__()
        self._build_ui()
        self._load_bookings()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        header = QHBoxLayout()
        header.addWidget(heading_label("My Bookings Today"))
        header.addStretch()

        self.date_label = QLabel(f"Date: {date.today().strftime('%A, %d %B %Y')}")
        self.date_label.setFont(body_font(11))
        self.date_label.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        header.addWidget(self.date_label)

        refresh_btn = secondary_button("Refresh")
        refresh_btn.clicked.connect(self._load_bookings)
        header.addWidget(refresh_btn)

        layout.addLayout(header)
        layout.addWidget(separator())

        # Summary cards
        summary_row = QHBoxLayout()
        summary_row.setSpacing(SPACING_MD)

        self.total_card = self._make_stat_card("Total Bookings", "0")
        self.tickets_card = self._make_stat_card("Tickets Sold", "0")
        self.revenue_card = self._make_stat_card("Revenue", "\u00a30.00")
        summary_row.addWidget(self.total_card)
        summary_row.addWidget(self.tickets_card)
        summary_row.addWidget(self.revenue_card)
        summary_row.addStretch()

        layout.addLayout(summary_row)

        # Table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Reference", "Film", "Show Date", "Time",
            "Customer", "Tickets", "Total", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)

        self.count_label = muted_label("")
        layout.addWidget(self.count_label)

    def _make_stat_card(self, title: str, value: str) -> Card:
        card = Card()
        card.setFixedWidth(180)
        card.setFixedHeight(80)

        t = QLabel(title)
        t.setFont(body_font(9))
        t.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        card.add(t)

        self._stat_labels = getattr(self, '_stat_labels', {})
        v = QLabel(value)
        v.setFont(heading_font(18))
        v.setStyleSheet(f"color: {WHITE}; background: transparent;")
        self._stat_labels[title] = v
        card.add(v)

        return card

    def _load_bookings(self):
        today = date.today().isoformat()
        try:
            bookings = api.search_bookings(
                booked_by=api.user_id,
                booking_date=today,
            )

            self._fill_table(bookings)

            # Update stats
            confirmed = [b for b in bookings if b["booking_status"] == "confirmed"]
            total_tickets = sum(b["num_tickets"] for b in confirmed)
            total_revenue = sum(b["total_cost"] for b in confirmed)

            self._stat_labels["Total Bookings"].setText(str(len(bookings)))
            self._stat_labels["Tickets Sold"].setText(str(total_tickets))
            self._stat_labels["Revenue"].setText(f"\u00a3{total_revenue:.2f}")

            self.count_label.setText(f"{len(bookings)} booking(s) made today")

        except Exception as e:
            error_dialog(self, f"Failed to load bookings: {e}")

    def _fill_table(self, bookings: list):
        self.table.setRowCount(len(bookings))
        for row, b in enumerate(bookings):
            self.table.setItem(row, 0, QTableWidgetItem(b["booking_reference"]))
            self.table.setItem(row, 1, QTableWidgetItem(b.get("film_title", "")))
            self.table.setItem(row, 2, QTableWidgetItem(str(b["show_date"])))
            self.table.setItem(row, 3, QTableWidgetItem(str(b.get("show_time", ""))[:5]))
            self.table.setItem(row, 4, QTableWidgetItem(b["customer_name"]))
            self.table.setItem(row, 5, QTableWidgetItem(str(b["num_tickets"])))
            self.table.setItem(row, 6, QTableWidgetItem(f"\u00a3{b['total_cost']:.2f}"))
            self.table.setItem(row, 7, QTableWidgetItem(b["booking_status"].capitalize()))
