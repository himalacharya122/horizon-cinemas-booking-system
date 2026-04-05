"""
desktop/ui/windows/booking_staff/search_booking.py
Search bookings by reference, customer name, email, or phone.
"""

from PyQt6.QtCore import Qt  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
)

from desktop.ui.theme import (
    ACCENT, SUCCESS, DANGER, WHITE,
    BG_CARD, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    heading_font, body_font, SPACING_SM, SPACING_MD, SPACING_LG,
)
from desktop.ui.widgets import (
    heading_label, subheading_label, muted_label, primary_button,
    secondary_button, Card, separator, labelled_value, status_badge,
    show_toast, error_dialog,
)
from desktop.api_client import api


class SearchBookingView(QWidget):

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        layout.addWidget(heading_label("Search Bookings"))
        layout.addWidget(separator())

        # Search form
        search_card = Card()

        row1 = QHBoxLayout()
        row1.setSpacing(SPACING_SM)

        lbl_ref = QLabel("Reference:")
        lbl_ref.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        row1.addWidget(lbl_ref)
        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("HC-2025-00001")
        self.ref_input.setFixedWidth(200)
        row1.addWidget(self.ref_input)

        lbl_name = QLabel("Name:")
        lbl_name.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        row1.addWidget(lbl_name)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Customer name")
        self.name_input.setFixedWidth(200)
        row1.addWidget(self.name_input)

        lbl_email = QLabel("Email:")
        lbl_email.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        row1.addWidget(lbl_email)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email address")
        self.email_input.setFixedWidth(200)
        row1.addWidget(self.email_input)

        row1.addStretch()
        search_card.add_layout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(SPACING_SM)

        lbl_phone = QLabel("Phone:")
        lbl_phone.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        row2.addWidget(lbl_phone)
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone number")
        self.phone_input.setFixedWidth(200)
        row2.addWidget(self.phone_input)

        lbl_status = QLabel("Status:")
        lbl_status.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        row2.addWidget(lbl_status)
        self.status_combo = QComboBox()
        self.status_combo.addItems(["All", "confirmed", "cancelled"])
        self.status_combo.setFixedWidth(140)
        row2.addWidget(self.status_combo)

        row2.addStretch()

        search_btn = primary_button("Search")
        search_btn.clicked.connect(self._do_search)
        row2.addWidget(search_btn)

        clear_btn = secondary_button("Clear")
        clear_btn.clicked.connect(self._clear_form)
        row2.addWidget(clear_btn)

        search_card.add_layout(row2)
        layout.addWidget(search_card)

        # Results table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Reference", "Film", "Date", "Time", "Customer",
            "Phone", "Tickets", "Total", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)

        self.result_label = muted_label("")
        layout.addWidget(self.result_label)

        # Detail card
        self.detail_card = Card()
        self.detail_card.hide()
        layout.addWidget(self.detail_card)

        # Enter key triggers search from any input
        for inp in (self.ref_input, self.name_input, self.email_input, self.phone_input):
            inp.returnPressed.connect(self._do_search)

    def _do_search(self):
        # If reference is provided, do a direct lookup
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

        # Otherwise search with filters
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

        # Default to user's cinema for booking staff
        if api.role == "booking_staff":
            params["cinema_id"] = api.cinema_id

        try:
            bookings = api.search_bookings(**params)
            self._fill_table(bookings)
            self.result_label.setText(f"{len(bookings)} booking(s) found")
        except Exception as e:
            error_dialog(self, f"Search failed: {e}")

    def _fill_table(self, bookings: list):
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
            self.table.setItem(row, 8, QTableWidgetItem(b["booking_status"].capitalize()))

    def _clear_form(self):
        self.ref_input.clear()
        self.name_input.clear()
        self.email_input.clear()
        self.phone_input.clear()
        self.status_combo.setCurrentIndex(0)
        self.table.setRowCount(0)
        self.result_label.setText("")
        self.detail_card.hide()
