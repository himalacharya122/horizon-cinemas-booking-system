"""
desktop/ui/windows/booking_staff/new_booking.py
Booking form with receipt display and print capability.
"""

from PyQt6.QtCore import QDate, Qt  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QApplication,
    QButtonGroup,
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from desktop.api_client import api
from desktop.ui.theme import (
    ACCENT,
    BG_HOVER,
    BORDER,
    SPACING_LG,
    SPACING_MD,
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
    form_row,
    heading_label,
    labelled_value,
    muted_label,
    primary_button,
    secondary_button,
    separator,
    show_toast,
    status_badge,
    subheading_label,
)


class NewBookingView(QWidget):
    def __init__(self):
        super().__init__()
        self._showings_data = []
        self._availability = None
        self._last_booking = None
        self._build_ui()
        self._load_cinemas()

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        self.main_layout = QVBoxLayout(content)
        self.main_layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        self.main_layout.setSpacing(SPACING_MD)

        self.main_layout.addWidget(heading_label("New Booking"))
        # self.main_layout.addWidget(separator())

        columns = QHBoxLayout()
        columns.setSpacing(SPACING_LG)

        # Left column — booking form
        left = QVBoxLayout()
        left.setSpacing(SPACING_MD)

        # Cinema & Film selection
        select_card = Card()

        self.cinema_combo = QComboBox()
        self.cinema_combo.currentIndexChanged.connect(self._on_cinema_changed)
        select_card.add_layout(form_row("Cinema", self.cinema_combo))

        self.film_combo = QComboBox()
        self.film_combo.currentIndexChanged.connect(self._on_film_changed)
        select_card.add_layout(form_row("Film", self.film_combo))

        self.showing_combo = QComboBox()
        select_card.add_layout(form_row("Showing", self.showing_combo))

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setMinimumDate(QDate.currentDate())
        self.date_edit.setMaximumDate(QDate.currentDate().addDays(7))
        select_card.add_layout(form_row("Date", self.date_edit))

        left.addWidget(select_card)

        # Ticket type
        ticket_card = Card()
        type_group_layout = QHBoxLayout()
        self.seat_type_group = QButtonGroup(self)

        self.rb_lower = QRadioButton("Lower Hall")
        self.rb_upper = QRadioButton("Upper Gallery")
        self.rb_vip = QRadioButton("VIP")
        self.rb_lower.setChecked(True)

        self.seat_type_group.addButton(self.rb_lower, 0)
        self.seat_type_group.addButton(self.rb_upper, 1)
        self.seat_type_group.addButton(self.rb_vip, 2)

        st_lbl = QLabel("Seat Type:")
        st_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        type_group_layout.addWidget(st_lbl)
        type_group_layout.addWidget(self.rb_lower)
        type_group_layout.addWidget(self.rb_upper)
        type_group_layout.addWidget(self.rb_vip)
        type_group_layout.addStretch()
        ticket_card.add_layout(type_group_layout)

        self.num_tickets = QSpinBox()
        self.num_tickets.setMinimum(1)
        self.num_tickets.setMaximum(20)
        self.num_tickets.setValue(1)
        ticket_card.add_layout(form_row("Tickets", self.num_tickets))

        self.check_btn = primary_button("Check Availability & Price")
        self.check_btn.clicked.connect(self._check_availability)
        ticket_card.add(self.check_btn)

        self.avail_label = QLabel("")
        self.avail_label.setFont(body_font(11))
        self.avail_label.setWordWrap(True)
        self.avail_label.hide()
        ticket_card.add(self.avail_label)

        left.addWidget(ticket_card)

        # Customer info
        customer_card = Card()
        cust_title = subheading_label("Customer Details", 12)
        customer_card.add(cust_title)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Full name")
        customer_card.add_layout(form_row("Name *", self.name_input))

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone number")
        customer_card.add_layout(form_row("Phone", self.phone_input))

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email address")
        customer_card.add_layout(form_row("Email", self.email_input))

        customer_card.add(separator())

        pay_lbl = QLabel("Simulate payment (card details not stored)")
        pay_lbl.setFont(body_font(9))
        pay_lbl.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        customer_card.add(pay_lbl)

        btn_row = QHBoxLayout()
        self.book_btn = primary_button("Confirm Booking")
        self.book_btn.setEnabled(False)
        self.book_btn.clicked.connect(self._create_booking)
        btn_row.addWidget(self.book_btn)

        self.reset_btn = secondary_button("Reset")
        self.reset_btn.clicked.connect(self._reset_form)
        btn_row.addWidget(self.reset_btn)
        btn_row.addStretch()

        customer_card.add_layout(btn_row)
        left.addWidget(customer_card)
        left.addStretch()

        # Right column — receipt
        right = QVBoxLayout()
        right.setSpacing(SPACING_MD)

        receipt_title = subheading_label("Booking Receipt", 13)
        right.addWidget(receipt_title)

        self.receipt_card = Card()
        self.receipt_placeholder = muted_label("Receipt will appear here after booking.")
        self.receipt_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.receipt_placeholder.setMinimumHeight(200)
        self.receipt_card.add(self.receipt_placeholder)
        right.addWidget(self.receipt_card)

        # Print / Copy button
        self.print_btn = QPushButton("Copy Receipt to Clipboard")
        self.print_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.print_btn.setStyleSheet(
            f"QPushButton {{ background-color: {BG_HOVER}; color: {TEXT_PRIMARY}; "
            f"border: 1px solid {BORDER}; border-radius: 6px; padding: 10px; "
            f"font-weight: 600; }}"
            f"QPushButton:hover {{ background-color: {BORDER}; }}"
        )
        self.print_btn.clicked.connect(self._copy_receipt)
        self.print_btn.hide()
        right.addWidget(self.print_btn)

        right.addStretch()

        columns.addLayout(left, 3)
        columns.addLayout(right, 2)

        self.main_layout.addLayout(columns)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(content)
        outer.addWidget(scroll)

    # Data loading

    def _load_cinemas(self):
        try:
            cinemas = api.get_cinemas()
            self.cinema_combo.blockSignals(True)
            self.cinema_combo.clear()

            if api.role == "booking_staff":
                cinemas = [c for c in cinemas if c["cinema_id"] == api.cinema_id]

            for c in cinemas:
                label = f"{c['cinema_name']}"
                if c.get("city_name"):
                    label += f"  \u2014  {c['city_name']}"
                self.cinema_combo.addItem(label, c["cinema_id"])

            self.cinema_combo.blockSignals(False)
            self._on_cinema_changed()
        except Exception as e:
            error_dialog(self, f"Failed to load cinemas: {e}")

    def _on_cinema_changed(self):
        cinema_id = self.cinema_combo.currentData()
        if not cinema_id:
            return
        target = self.date_edit.date().toPyDate().isoformat()
        try:
            listings = api.get_film_listings(cinema_id, target)
            self.film_combo.blockSignals(True)
            self.film_combo.clear()
            self._showings_data = []

            for item in listings:
                self.film_combo.addItem(
                    f"{item['title']}  (Screen {item['screen_number']})",
                    item,
                )

            self.film_combo.blockSignals(False)
            self._on_film_changed()
        except Exception as e:
            error_dialog(self, f"Failed to load films: {e}")

    def _on_film_changed(self):
        self.showing_combo.clear()
        idx = self.film_combo.currentIndex()
        if idx < 0:
            return

        film_data = self.film_combo.itemData(idx)
        if not film_data:
            return

        self._showings_data = film_data.get("showings", [])
        for s in self._showings_data:
            t = s["show_time"]
            if isinstance(t, str) and len(t) > 5:
                t = t[:5]
            label = (
                f"{t}  ({s['show_type'].capitalize()})  \u2014  "
                f"from \u00a3{s['lower_hall_price']:.2f}"
            )
            self.showing_combo.addItem(label, s)

        self._availability = None
        self.book_btn.setEnabled(False)
        self.avail_label.hide()

    # Availability

    def _get_seat_type(self) -> str:
        btn_id = self.seat_type_group.checkedId()
        return ["lower_hall", "upper_gallery", "vip"][btn_id]

    def _check_availability(self):
        showing_idx = self.showing_combo.currentIndex()
        if showing_idx < 0 or not self._showings_data:
            error_dialog(self, "Please select a film and showing first.")
            return

        showing = self.showing_combo.itemData(showing_idx)
        if not showing:
            return

        data = {
            "showing_id": showing["showing_id"],
            "show_date": self.date_edit.date().toPyDate().isoformat(),
            "seat_type": self._get_seat_type(),
            "num_tickets": self.num_tickets.value(),
        }

        try:
            result = api.check_availability(data)
            self._availability = result
            available = result["available"]
            seats = result["seats_available"]
            total_seats = result["seats_total"]
            unit = result["unit_price"]
            total = result["total_price"]
            seat_type = result["seat_type"].replace("_", " ").title()

            if available:
                self.avail_label.setText(
                    f"\u2713  {seats}/{total_seats} {seat_type} seats available\n"
                    f"Unit price: \u00a3{unit:.2f}  \u00d7  {self.num_tickets.value()} tickets  =  "
                    f"<b>\u00a3{total:.2f}</b>"
                )
                self.avail_label.setStyleSheet(
                    f"color: {SUCCESS}; background: transparent; padding: 8px;"
                )
                self.book_btn.setEnabled(True)
            else:
                self.avail_label.setText(
                    f"\u2717  Only {seats} {seat_type} seat(s) available "
                    f"(requested {self.num_tickets.value()})"
                )
                self.avail_label.setStyleSheet(
                    f"color: {ACCENT}; background: transparent; padding: 8px;"
                )
                self.book_btn.setEnabled(False)

            self.avail_label.show()
        except Exception as e:
            detail = str(e)
            if hasattr(e, "response"):
                try:
                    detail = e.response.json().get("detail", detail)
                except Exception:
                    pass
            error_dialog(self, detail)

    # Create booking

    def _create_booking(self):
        name = self.name_input.text().strip()
        if not name:
            error_dialog(self, "Customer name is required.")
            return

        showing_idx = self.showing_combo.currentIndex()
        showing = self.showing_combo.itemData(showing_idx)
        if not showing:
            return

        data = {
            "showing_id": showing["showing_id"],
            "show_date": self.date_edit.date().toPyDate().isoformat(),
            "customer_name": name,
            "customer_phone": self.phone_input.text().strip() or None,
            "customer_email": self.email_input.text().strip() or None,
            "seat_type": self._get_seat_type(),
            "num_tickets": self.num_tickets.value(),
            "payment_simulated": True,
        }

        self.book_btn.setEnabled(False)
        self.book_btn.setText("Processing\u2026")

        try:
            booking = api.create_booking(data)
            self._last_booking = booking
            self._show_receipt(booking)
            show_toast(self, f"Booking {booking['booking_reference']} confirmed!", success=True)
        except Exception as e:
            detail = str(e)
            if hasattr(e, "response"):
                try:
                    detail = e.response.json().get("detail", detail)
                except Exception:
                    pass
            error_dialog(self, detail)
        finally:
            self.book_btn.setEnabled(True)
            self.book_btn.setText("Confirm Booking")

    # Receipt

    def _show_receipt(self, booking: dict):
        while self.receipt_card._layout.count():
            item = self.receipt_card._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.receipt_card.add(subheading_label("Booking Confirmed", 13))
        self.receipt_card.add(status_badge(booking["booking_status"]))
        self.receipt_card.add(separator())

        fields = [
            ("Reference", booking["booking_reference"]),
            ("Film", booking.get("film_title", "")),
            ("Date", str(booking["show_date"])),
            ("Time", str(booking.get("show_time", ""))[:5]),
            ("Screen", str(booking.get("screen_number", ""))),
            ("Cinema", booking.get("cinema_name", "")),
            ("Customer", booking["customer_name"]),
            ("Tickets", str(booking["num_tickets"])),
        ]

        for label, value in fields:
            self.receipt_card.add_layout(labelled_value(label, value))

        seats = booking.get("booked_seats", [])
        if seats:
            seat_nums = ", ".join(s["seat_number"] for s in seats)
            seat_type = seats[0]["seat_type"].replace("_", " ").title()
            self.receipt_card.add_layout(labelled_value("Seats", seat_nums))
            self.receipt_card.add_layout(labelled_value("Seat Type", seat_type))

        self.receipt_card.add(separator())

        total_lbl = QLabel(f"Total: \u00a3{booking['total_cost']:.2f}")
        total_lbl.setFont(heading_font(16))
        total_lbl.setStyleSheet(f"color: {ACCENT}; background: transparent;")
        self.receipt_card.add(total_lbl)

        booking_date = booking.get("booking_date", "")
        if booking_date:
            bd_str = str(booking_date)[:19]
            self.receipt_card.add(muted_label(f"Booked: {bd_str}"))

        self.print_btn.show()

    def _copy_receipt(self):
        """Copy a formatted text receipt to the clipboard."""
        b = self._last_booking
        if not b:
            return

        seats = b.get("booked_seats", [])
        seat_str = ", ".join(s["seat_number"] for s in seats) if seats else "N/A"
        seat_type = seats[0]["seat_type"].replace("_", " ").title() if seats else "N/A"

        text = (
            "═══════════════════════════════════════\n"
            "        HORIZON CINEMAS — RECEIPT      \n"
            "═══════════════════════════════════════\n"
            f"  Reference:  {b['booking_reference']}\n"
            f"  Status:     {b['booking_status'].capitalize()}\n"
            f"  Film:       {b.get('film_title', '')}\n"
            f"  Date:       {b['show_date']}\n"
            f"  Time:       {str(b.get('show_time', ''))[:5]}\n"
            f"  Screen:     {b.get('screen_number', '')}\n"
            f"  Cinema:     {b.get('cinema_name', '')}\n"
            f"  Customer:   {b['customer_name']}\n"
            f"  Tickets:    {b['num_tickets']}\n"
            f"  Seats:      {seat_str}\n"
            f"  Seat Type:  {seat_type}\n"
            "───────────────────────────────────────\n"
            f"  TOTAL:      \u00a3{b['total_cost']:.2f}\n"
            "═══════════════════════════════════════\n"
        )

        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        show_toast(self, "Receipt copied to clipboard!", success=True)

    # Reset

    def _reset_form(self):
        self.name_input.clear()
        self.phone_input.clear()
        self.email_input.clear()
        self.num_tickets.setValue(1)
        self.rb_lower.setChecked(True)
        self.avail_label.hide()
        self.book_btn.setEnabled(False)
        self._availability = None
        self._last_booking = None
        self.print_btn.hide()

        while self.receipt_card._layout.count():
            item = self.receipt_card._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.receipt_placeholder = muted_label("Receipt will appear here after booking.")
        self.receipt_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.receipt_placeholder.setMinimumHeight(200)
        self.receipt_card.add(self.receipt_placeholder)
