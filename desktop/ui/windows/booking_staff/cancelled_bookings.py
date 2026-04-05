"""
desktop/ui/windows/booking_staff/cancelled_bookings.py
View all cancelled bookings for the staff member's cinema.
"""

from PyQt6.QtCore import Qt  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
)

from desktop.ui.theme import (
    DANGER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    heading_font, body_font, SPACING_MD, SPACING_LG,
)
from desktop.ui.widgets import (
    heading_label, muted_label, secondary_button,
    separator, error_dialog,
)
from desktop.api_client import api


class CancelledBookingsView(QWidget):

    def __init__(self):
        super().__init__()
        self._build_ui()
        self._load_cancelled()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        header = QHBoxLayout()
        header.addWidget(heading_label("Cancelled Bookings"))
        header.addStretch()

        refresh_btn = secondary_button("Refresh")
        refresh_btn.clicked.connect(self._load_cancelled)
        header.addWidget(refresh_btn)

        layout.addLayout(header)
        layout.addWidget(separator())

        # Table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Reference", "Film", "Show Date", "Customer",
            "Tickets", "Original Cost", "Cancel Fee", "Refund", "Cancelled At"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)

        self.count_label = muted_label("")
        layout.addWidget(self.count_label)

    def _load_cancelled(self):
        try:
            params = {"status": "cancelled"}
            if api.role == "booking_staff":
                params["cinema_id"] = api.cinema_id

            bookings = api.search_bookings(**params)
            self._fill_table(bookings)
            self.count_label.setText(f"{len(bookings)} cancelled booking(s)")

        except Exception as e:
            error_dialog(self, f"Failed to load cancelled bookings: {e}")

    def _fill_table(self, bookings: list):
        self.table.setRowCount(len(bookings))
        for row, b in enumerate(bookings):
            self.table.setItem(row, 0, QTableWidgetItem(b["booking_reference"]))
            self.table.setItem(row, 1, QTableWidgetItem(b.get("film_title", "")))
            self.table.setItem(row, 2, QTableWidgetItem(str(b["show_date"])))
            self.table.setItem(row, 3, QTableWidgetItem(b["customer_name"]))
            self.table.setItem(row, 4, QTableWidgetItem(str(b["num_tickets"])))
            self.table.setItem(row, 5, QTableWidgetItem(f"\u00a3{b['total_cost']:.2f}"))
            self.table.setItem(row, 6, QTableWidgetItem(f"\u00a3{b.get('cancellation_fee', 0):.2f}"))
            self.table.setItem(row, 7, QTableWidgetItem(f"\u00a3{b.get('refund_amount', 0):.2f}"))
            cancelled = b.get("cancelled_at", "")
            self.table.setItem(row, 8, QTableWidgetItem(str(cancelled)[:19] if cancelled else "\u2014"))
