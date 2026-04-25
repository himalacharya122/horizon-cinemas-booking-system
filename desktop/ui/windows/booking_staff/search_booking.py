# ============================================
# Author: Ridesha khadka
# Student ID: 23002960
# Last Edited: 2026-04-25
# ============================================

"""
desktop/ui/windows/booking_staff/search_booking.py
implements the Search Bookings view for Booking Staff to look up active and historical reservations.
provides filtering by Reference, Customer Name, Email, and Status.
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
    ACCENT_HOVER,
    BG_DARK,
    BORDER,
    DANGER,
    HERO_BG,
    SPACING_LG,
    SPACING_MD,
    SUCCESS,
    TEXT_SECONDARY,
    WHITE,
)
from desktop.ui.widgets import (
    Card,
    error_dialog,
    heading_label,
    muted_label,
    primary_button,
    secondary_button,
    separator,
    subheading_label,
)


class SearchBookingView(QWidget):
    """a view that provides advanced searching capabilities for cinema bookings."""

    def __init__(self):
        """initialises the search view and builds the interface."""
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        """constructs the primary layout including search filters and the results table."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        # header section with view title and search service description
        header_content = QVBoxLayout()
        header_content.setSpacing(4)
        header_content.addWidget(heading_label("Search Bookings"))
        desc = muted_label(
            "Centralized search for all active and historical bookings across your cinema"
        )
        header_content.addWidget(desc)
        layout.addLayout(header_content)
        layout.addWidget(separator())

        # search form card containing various filter inputs
        search_card = Card()
        search_card.add(subheading_label("Search Filters"))

        row1 = QHBoxLayout()
        row1.setSpacing(SPACING_MD)

        def _style_input(w, ph="", w_px=180):
            """helper to apply placeholder text and a fixed width to input widgets."""
            w.setPlaceholderText(ph)
            w.setFixedWidth(w_px)

        def _make_label(text):
            """helper to create styled form labels for the search filters."""
            lbl = QLabel(text)
            lbl.setStyleSheet(
                f"color: {TEXT_SECONDARY}; background: transparent; "
                f"font-weight: 600; font-size: 10pt; border: none;"
            )
            return lbl

        v1 = QVBoxLayout()
        v1.setSpacing(4)
        v1.addWidget(_make_label("Reference:"))
        self.ref_input = QLineEdit()
        _style_input(self.ref_input, "HC-2025-00001", 180)
        v1.addWidget(self.ref_input)
        row1.addLayout(v1)

        v2 = QVBoxLayout()
        v2.setSpacing(4)
        v2.addWidget(_make_label("Customer Name:"))
        self.name_input = QLineEdit()
        _style_input(self.name_input, "e.g. John Doe", 200)
        v2.addWidget(self.name_input)
        row1.addLayout(v2)

        v3 = QVBoxLayout()
        v3.setSpacing(4)
        v3.addWidget(_make_label("Email Address:"))
        self.email_input = QLineEdit()
        _style_input(self.email_input, "customer@example.com", 220)
        v3.addWidget(self.email_input)
        row1.addLayout(v3)

        row1.addStretch()
        search_card.add_layout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(SPACING_MD)

        v4 = QVBoxLayout()
        v4.setSpacing(4)
        v4.addWidget(_make_label("Phone Number:"))
        self.phone_input = QLineEdit()
        _style_input(self.phone_input, "e.g. 077...", 180)
        v4.addWidget(self.phone_input)
        row2.addLayout(v4)

        v5 = QVBoxLayout()
        v5.setSpacing(4)
        v5.addWidget(_make_label("Booking Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["All", "confirmed", "cancelled"])
        self.status_combo.setFixedWidth(140)
        v5.addWidget(self.status_combo)
        row2.addLayout(v5)

        row2.addStretch()

        btns = QHBoxLayout()
        btns.setContentsMargins(0, 20, 0, 0)
        btns.setSpacing(10)

        search_btn = primary_button("Search Results")
        search_btn.setStyleSheet(
            f"QPushButton {{ background-color: {ACCENT}; color: {WHITE}; border: none; "
            f"min-height: 34px; max-height: 34px; min-width: 140px; font-weight: 700; "
            f"border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}"
        )
        search_btn.clicked.connect(self._do_search)
        btns.addWidget(search_btn)

        clear_btn = secondary_button("Clear Form")
        clear_btn.setStyleSheet(
            f"QPushButton {{ background-color: {HERO_BG}; color: {WHITE}; border: none; "
            f"min-height: 34px; max-height: 34px; min-width: 140px; font-weight: 700; "
            f"border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: #2E2C28; }}"
        )
        clear_btn.clicked.connect(self._clear_form)
        btns.addWidget(clear_btn)

        row2.addLayout(btns)
        search_card.add_layout(row2)
        layout.addWidget(search_card)

        # results table for displaying found booking records
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
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(
            ["Reference", "Film", "Date", "Time", "Customer", "Phone", "Tickets", "Total", "Status"]
        )

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(0, 170)  # Reference
        self.table.setColumnWidth(2, 140)  # Date
        self.table.setColumnWidth(3, 90)  # Time
        self.table.setColumnWidth(5, 140)  # Phone
        self.table.setColumnWidth(6, 90)  # Tickets
        self.table.setColumnWidth(7, 120)  # Total
        self.table.setColumnWidth(8, 150)  # Status

        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Film
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Customer

        layout.addWidget(self.table, 1)

        self.result_label = muted_label("")
        layout.addWidget(self.result_label)

        # detailed card for displaying expanded booking information
        self.detail_card = Card()
        self.detail_card.hide()
        layout.addWidget(self.detail_card)

        # enter key triggers search from any input field for efficiency
        for inp in (self.ref_input, self.name_input, self.email_input, self.phone_input):
            inp.returnPressed.connect(self._do_search)

    def _do_search(self):
        """orchestrates the search process by prioritizing direct lookup or applying filters."""
        # if a Booking Reference is provided, perform a direct lookup via the api
        ref = self.ref_input.text().strip()
        if ref:
            try:
                booking = api.get_booking(ref)
                self._fill_table([booking])
                self.result_label.setText("1 booking found")
                return
            except Exception as e:
                detail = str(e)
                if hasattr(e, "response"):
                    try:
                        detail = e.response.json().get("detail", detail)
                    except Exception:
                        pass
                error_dialog(self, detail)
                return

        # otherwise perform a broader search using the specified filters
        params = {}
        name = self.name_input.text().strip()
        if name:
            params["customer_name"] = name
        email = self.email_input.text().strip()
        if email:
            params["customer_email"] = email
        phone = self.phone_input.text().strip()
        if phone:
            params["customer_phone"] = phone
        status = self.status_combo.currentText()
        if status != "All":
            params["status"] = status

        # default search scope to the user's assigned cinema for Booking Staff
        if api.role == "booking_staff":
            params["cinema_id"] = api.cinema_id

        try:
            bookings = api.search_bookings(**params)
            self._fill_table(bookings)
            self.result_label.setText(f"{len(bookings)} booking(s) found")
        except Exception as e:
            error_dialog(self, f"Search failed: {e}")

    def _fill_table(self, bookings: list):
        """populates the results QTableWidget with the provided list of booking records."""
        self.table.setRowCount(len(bookings))
        for row, b in enumerate(bookings):
            self.table.setItem(row, 0, QTableWidgetItem(b["booking_reference"]))
            self.table.setItem(row, 1, QTableWidgetItem(b.get("film_title", "")))
            self.table.setItem(row, 2, QTableWidgetItem(str(b["show_date"])))
            self.table.setItem(row, 3, QTableWidgetItem(str(b.get("show_time", ""))[:5]))
            self.table.setItem(row, 4, QTableWidgetItem(b["customer_name"]))
            self.table.setItem(row, 5, QTableWidgetItem(b.get("customer_phone", "") or "\u2014"))
            self.table.setItem(row, 6, QTableWidgetItem(str(b["num_tickets"])))
            self.table.setItem(row, 7, QTableWidgetItem(f"\u00a3{b['total_cost']:.2f}"))

            # assign colored status indicators based on booking state
            status_str = b["booking_status"].lower()
            status_item = QTableWidgetItem(status_str.capitalize())
            if status_str == "confirmed":
                status_item.setForeground(QColor(SUCCESS))
            elif status_str == "cancelled":
                status_item.setForeground(QColor(DANGER))

            font = status_item.font()
            font.setBold(True)
            status_item.setFont(font)

            self.table.setItem(row, 8, status_item)

    def _clear_form(self):
        """resets all search inputs and clears the results table."""
        self.ref_input.clear()
        self.name_input.clear()
        self.email_input.clear()
        self.phone_input.clear()
        self.status_combo.setCurrentIndex(0)
        self.table.setRowCount(0)
        self.result_label.setText("")
        self.detail_card.hide()
