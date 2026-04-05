"""
desktop/ui/windows/booking_staff/cancellation.py
Cancel a booking by reference. Shows booking details before confirming.
"""

from PyQt6.QtCore import Qt  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QScrollArea,
)

from desktop.ui.theme import (
    ACCENT, DANGER, SUCCESS, WHITE,
    BG_CARD, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    heading_font, body_font, SPACING_MD, SPACING_LG,
)
from desktop.ui.widgets import (
    heading_label, subheading_label, muted_label, primary_button,
    danger_button, secondary_button, Card, separator,
    labelled_value, status_badge, show_toast, confirm_dialog,
    error_dialog,
)
from desktop.api_client import api


class CancellationView(QWidget):

    def __init__(self):
        super().__init__()
        self._booking = None
        self._build_ui()

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

        layout.addWidget(heading_label("Booking Cancellation"))
        layout.addWidget(separator())

        # Search bar
        search_card = Card()
        search_row = QHBoxLayout()

        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("Enter booking reference (e.g. HC-2025-00001)")
        self.ref_input.setFixedWidth(360)
        ref_lbl = QLabel("Reference:")
        ref_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        search_row.addWidget(ref_lbl)
        search_row.addWidget(self.ref_input)

        self.search_btn = primary_button("Look Up")
        self.search_btn.clicked.connect(self._lookup_booking)
        search_row.addWidget(self.search_btn)
        search_row.addStretch()

        search_card.add_layout(search_row)
        layout.addWidget(search_card)

        # Booking details
        self.details_card = Card()
        self.details_card.hide()
        layout.addWidget(self.details_card)

        # Cancel result
        self.result_card = Card()
        self.result_card.hide()
        layout.addWidget(self.result_card)

        layout.addStretch()

        self.ref_input.returnPressed.connect(self._lookup_booking)

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _lookup_booking(self):
        ref = self.ref_input.text().strip()
        if not ref:
            error_dialog(self, "Please enter a booking reference.")
            return

        self.details_card.hide()
        self.result_card.hide()

        try:
            booking = api.get_booking(ref)
            self._booking = booking
            self._show_details(booking)
        except Exception as e:
            detail = str(e)
            if hasattr(e, "response"):
                try:
                    detail = e.response.json().get("detail", detail)
                except Exception:
                    pass
            error_dialog(self, detail)

    def _show_details(self, b: dict):
        while self.details_card._layout.count():
            item = self.details_card._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        title_row = QHBoxLayout()
        title_row.addWidget(subheading_label("Booking Details", 13))
        title_row.addStretch()
        title_row.addWidget(status_badge(b["booking_status"]))
        self.details_card.add_layout(title_row)

        self.details_card.add(separator())

        fields = [
            ("Reference", b["booking_reference"]),
            ("Film", b.get("film_title", "")),
            ("Date", str(b["show_date"])),
            ("Time", str(b.get("show_time", ""))[:5]),
            ("Screen", str(b.get("screen_number", ""))),
            ("Cinema", b.get("cinema_name", "")),
            ("Customer", b["customer_name"]),
            ("Phone", b.get("customer_phone", "") or "\u2014"),
            ("Email", b.get("customer_email", "") or "\u2014"),
            ("Tickets", str(b["num_tickets"])),
            ("Total Cost", f"\u00a3{b['total_cost']:.2f}"),
        ]

        for label, value in fields:
            self.details_card.add_layout(labelled_value(label, value))

        seats = b.get("booked_seats", [])
        if seats:
            seat_str = ", ".join(s["seat_number"] for s in seats)
            self.details_card.add_layout(labelled_value("Seats", seat_str))

        if b["booking_status"] == "cancelled":
            self.details_card.add(separator())
            self.details_card.add_layout(
                labelled_value("Cancellation Fee", f"\u00a3{b.get('cancellation_fee', 0):.2f}")
            )
            self.details_card.add_layout(
                labelled_value("Refund Amount", f"\u00a3{b.get('refund_amount', 0):.2f}")
            )
        else:
            self.details_card.add(separator())

            fee = round(b["total_cost"] * 0.50, 2)
            refund = round(b["total_cost"] - fee, 2)

            warn = QLabel(
                f"Cancellation fee: \u00a3{fee:.2f} (50%)   |   Refund: \u00a3{refund:.2f}"
            )
            warn.setFont(body_font(10))
            warn.setStyleSheet(f"color: {DANGER}; background: transparent; font-weight: 500; padding: 4px;")
            self.details_card.add(warn)

            cancel_btn = danger_button("Cancel This Booking")
            cancel_btn.clicked.connect(self._cancel_booking)
            self.details_card.add(cancel_btn)

        self.details_card.show()

    def _cancel_booking(self):
        if not self._booking:
            return

        ref = self._booking["booking_reference"]
        ok = confirm_dialog(
            self,
            "Confirm Cancellation",
            f"Are you sure you want to cancel booking {ref}?\n\n"
            f"A 50% cancellation fee will be charged."
        )
        if not ok:
            return

        try:
            result = api.cancel_booking(ref)
            self._show_cancel_result(result)
            show_toast(self, result.get("message", "Booking cancelled."), success=True)
            self._lookup_booking()
        except Exception as e:
            detail = str(e)
            if hasattr(e, "response"):
                try:
                    detail = e.response.json().get("detail", detail)
                except Exception:
                    pass
            error_dialog(self, detail)

    def _show_cancel_result(self, result: dict):
        while self.result_card._layout.count():
            item = self.result_card._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.result_card.add(subheading_label("Cancellation Processed", 12))
        self.result_card.add(separator())
        self.result_card.add_layout(labelled_value("Reference", result["booking_reference"]))
        self.result_card.add_layout(labelled_value("Status", result["booking_status"].capitalize()))
        self.result_card.add_layout(labelled_value("Fee Charged", f"\u00a3{result['cancellation_fee']:.2f}"))
        self.result_card.add_layout(labelled_value("Refund", f"\u00a3{result['refund_amount']:.2f}"))
        self.result_card.show()
