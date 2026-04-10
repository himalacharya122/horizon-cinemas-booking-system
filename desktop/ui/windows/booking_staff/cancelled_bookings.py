"""
desktop/ui/windows/booking_staff/cancelled_bookings.py
implements the Cancelled Bookings view for Booking Staff.
provides a searchable audit trail of all voided reservations and refund transactions.
"""

from PyQt6.QtCore import Qt  # type: ignore
from PyQt6.QtGui import QShowEvent  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from desktop.api_client import api
from desktop.ui.theme import (
    BG_DARK,
    BORDER,
    HERO_BG,
    SPACING_LG,
    SPACING_MD,
    TEXT_SECONDARY,
    WHITE,
)
from desktop.ui.widgets import (
    error_dialog,
    heading_label,
    muted_label,
    secondary_button,
    separator,
)


class CancelledBookingsView(QWidget):
    """a view that displays a table of cancelled bookings with filtering by customer name or reference."""

    def __init__(self):
        """initialises the view and fetches the initial set of cancelled bookings."""
        super().__init__()
        self._build_ui()
        self._load_cancelled()

    def _build_ui(self):
        """constructs the primary layout including the filter bar and the cancelled bookings table."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        # header section with view title and audit description
        header_content = QVBoxLayout()
        header_content.setSpacing(4)
        header_content.addWidget(heading_label("Cancelled Bookings"))
        desc = muted_label(
            "Audit all inactive reservations and refund transactions for your cinema"
        )
        header_content.addWidget(desc)

        header = QHBoxLayout()
        header.addLayout(header_content)
        header.addStretch()

        # refresh action to reload the cancelled bookings dataset
        self.refresh_btn = secondary_button("Refresh List")
        self.refresh_btn.setStyleSheet(
            f"QPushButton {{ background-color: {HERO_BG}; color: {WHITE}; border: none; "
            f"min-height: 34px; max-height: 34px; min-width: 120px; font-weight: 700; "
            f"border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: #2E2C28; }}"
        )
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.clicked.connect(self._load_cancelled)
        header.addWidget(self.refresh_btn)

        layout.addLayout(header)
        layout.addWidget(separator())

        # filter bar for searching by Customer Name or Booking Reference
        filter_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search customer name or reference...")
        self.search_input.setFixedWidth(350)
        self.search_input.setStyleSheet(
            f"border: 1px solid {BORDER}; border-radius: 6px; height: 34px; "
            f"padding: 0 12px; background: {WHITE};"
        )
        self.search_input.textChanged.connect(self._load_cancelled)
        filter_row.addWidget(self.search_input)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        # data table for displaying cancelled booking details
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(44)

        self.table.setStyleSheet(
            f"QTableWidget {{ border: 1.5px solid {BORDER}; border-radius: 8px; background: {WHITE}; }}"
            f"QHeaderView::section {{ background-color: {BG_DARK}; color: {TEXT_SECONDARY}; "
            f"font-weight: 600; padding: 8px 5px; border: none; border-bottom: 2.5px solid {BORDER}; "
            f"border-right: 1px solid {BORDER}; border-left: 10px solid transparent; }}"
            f"QTableWidget::item {{ border-left: 10px solid transparent; padding-right: 10px; }}"
            "QTableWidget::item:selected { background-color: #FEF2F2; color: #0A0908; }"
        )
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(
            [
                "Reference",
                "Film",
                "Show Date",
                "Customer",
                "Tickets",
                "Original Cost",
                "Cancel Fee",
                "Refund",
                "Cancelled At",
            ]
        )

        # Balance column widths nicely
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        # Set specific widths for fixed data
        self.table.setColumnWidth(0, 170)  # Reference
        self.table.setColumnWidth(2, 120)  # Show Date
        self.table.setColumnWidth(4, 80)  # Tickets
        self.table.setColumnWidth(5, 110)  # Cost
        self.table.setColumnWidth(6, 110)  # Fee
        self.table.setColumnWidth(7, 110)  # Refund
        self.table.setColumnWidth(8, 210)  # Cancelled At

        # Stretch the variable text columns
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Film
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Customer

        layout.addWidget(self.table, 1)

        self.count_label = muted_label("")
        layout.addWidget(self.count_label)

    def showEvent(self, event: QShowEvent):
        """refreshes the cancelled bookings list whenever the view is shown."""
        super().showEvent(event)
        self._load_cancelled()

    def _load_cancelled(self):
        """fetches cancelled bookings from the api based on current filter criteria."""
        try:
            query = self.search_input.text().strip()
            params = {"status": "cancelled"}

            if query:
                if "HC-" in query.upper():
                    params["reference"] = query
                else:
                    params["customer_name"] = query

            if api.role == "booking_staff" and api.cinema_id > 0:
                params["cinema_id"] = api.cinema_id

            bookings = api.search_bookings(**params)
            self._fill_table(bookings)
            self.count_label.setText(f"{len(bookings)} cancelled booking(s)")

        except Exception as e:
            error_dialog(self, f"Failed to load cancelled bookings: {e}")

    def _fill_table(self, bookings: list):
        """populates the QTableWidget with the provided list of cancelled bookings."""
        self.table.setRowCount(len(bookings))
        for row, b in enumerate(bookings):
            self.table.setItem(row, 0, QTableWidgetItem(b["booking_reference"]))
            self.table.setItem(row, 1, QTableWidgetItem(b.get("film_title", "")))
            self.table.setItem(row, 2, QTableWidgetItem(str(b["show_date"])))
            self.table.setItem(row, 3, QTableWidgetItem(b["customer_name"]))
            self.table.setItem(row, 4, QTableWidgetItem(str(b["num_tickets"])))
            self.table.setItem(row, 5, QTableWidgetItem(f"\u00a3{b['total_cost']:.2f}"))
            self.table.setItem(
                row, 6, QTableWidgetItem(f"\u00a3{b.get('cancellation_fee', 0):.2f}")
            )
            self.table.setItem(row, 7, QTableWidgetItem(f"\u00a3{b.get('refund_amount', 0):.2f}"))
            cancelled = b.get("cancelled_at", "")
            self.table.setItem(
                row, 8, QTableWidgetItem(str(cancelled)[:19] if cancelled else "\u2014")
            )
