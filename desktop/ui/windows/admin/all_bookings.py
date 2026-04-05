"""
desktop/ui/windows/admin/all_bookings.py
Admin view: view all bookings across all cinemas with cinema switcher.
"""

from datetime import date
from PyQt6.QtCore import Qt  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QLabel, QLineEdit, QDateEdit,
)
from PyQt6.QtCore import QDate  # type: ignore

from desktop.ui.theme import (
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    heading_font, body_font, SPACING_SM, SPACING_MD, SPACING_LG,
)
from desktop.ui.widgets import (
    heading_label, primary_button, secondary_button,
    separator, show_toast, error_dialog, muted_label,
)
from desktop.api_client import api


class AllBookingsView(QWidget):

    def __init__(self):
        super().__init__()
        self._build_ui()
        self._load_cinemas()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        header = QHBoxLayout()
        header.addWidget(heading_label("All Bookings"))
        header.addStretch()
        layout.addLayout(header)
        layout.addWidget(separator())

        # Filter row
        filter_row = QHBoxLayout()
        filter_row.setSpacing(SPACING_SM)

        lbl_cinema = QLabel("Cinema:")
        lbl_cinema.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        filter_row.addWidget(lbl_cinema)
        self.cinema_filter = QComboBox()
        self.cinema_filter.setFixedWidth(240)
        filter_row.addWidget(self.cinema_filter)

        lbl_status = QLabel("Status:")
        lbl_status.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        filter_row.addWidget(lbl_status)
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "confirmed", "cancelled"])
        self.status_filter.setFixedWidth(120)
        filter_row.addWidget(self.status_filter)

        lbl_name = QLabel("Customer:")
        lbl_name.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        filter_row.addWidget(lbl_name)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Name search...")
        self.name_input.setFixedWidth(180)
        filter_row.addWidget(self.name_input)

        search_btn = primary_button("Search")
        search_btn.clicked.connect(self._load_bookings)
        filter_row.addWidget(search_btn)

        filter_row.addStretch()
        layout.addLayout(filter_row)

        # Table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "Reference", "Film", "Cinema", "Date", "Time",
            "Customer", "Phone", "Tickets", "Total", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)

        self.count_label = muted_label("")
        layout.addWidget(self.count_label)

        self.name_input.returnPressed.connect(self._load_bookings)

    def _load_cinemas(self):
        try:
            cinemas = api.get_cinemas()
            self.cinema_filter.clear()
            self.cinema_filter.addItem("All Cinemas", None)
            for c in cinemas:
                self.cinema_filter.addItem(
                    f"{c['cinema_name']} ({c.get('city_name', '')})",
                    c["cinema_id"],
                )
            self._load_bookings()
        except Exception as e:
            error_dialog(self, str(e))

    def _load_bookings(self):
        params = {}
        cinema_id = self.cinema_filter.currentData()
        if cinema_id:
            params["cinema_id"] = cinema_id

        status = self.status_filter.currentText()
        if status != "All":
            params["status"] = status

        name = self.name_input.text().strip()
        if name:
            params["customer_name"] = name

        try:
            bookings = api.search_bookings(**params)
            self._fill_table(bookings)
            self.count_label.setText(f"{len(bookings)} booking(s) found")
        except Exception as e:
            error_dialog(self, f"Failed to load bookings: {e}")

    def _fill_table(self, bookings: list):
        self.table.setRowCount(len(bookings))
        for row, b in enumerate(bookings):
            self.table.setItem(row, 0, QTableWidgetItem(b["booking_reference"]))
            self.table.setItem(row, 1, QTableWidgetItem(b.get("film_title", "")))
            self.table.setItem(row, 2, QTableWidgetItem(b.get("cinema_name", "")))
            self.table.setItem(row, 3, QTableWidgetItem(str(b["show_date"])))
            self.table.setItem(row, 4, QTableWidgetItem(str(b.get("show_time", ""))[:5]))
            self.table.setItem(row, 5, QTableWidgetItem(b["customer_name"]))
            self.table.setItem(row, 6, QTableWidgetItem(b.get("customer_phone", "") or "\u2014"))
            self.table.setItem(row, 7, QTableWidgetItem(str(b["num_tickets"])))
            self.table.setItem(row, 8, QTableWidgetItem(f"\u00a3{b['total_cost']:.2f}"))
            self.table.setItem(row, 9, QTableWidgetItem(b["booking_status"].capitalize()))
