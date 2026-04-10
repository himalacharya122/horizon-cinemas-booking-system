"""
desktop/ui/windows/booking_staff/cancellation.py
implements the Booking Cancellation view for Booking Staff.
facilitates booking lookups by reference, fee calculations, and cancellation processing.
"""

from PyQt6.QtWidgets import (  # type: ignore
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from desktop.api_client import api
from desktop.ui.theme import (
    ACCENT,
    BORDER,
    DANGER,
    HERO_BG,
    SPACING_LG,
    SPACING_MD,
    TEXT_SECONDARY,
    WHITE,
    body_font,
)
from desktop.ui.widgets import (
    Card,
    confirm_dialog,
    danger_button,
    error_dialog,
    heading_label,
    labelled_value,
    muted_label,
    primary_button,
    separator,
    show_toast,
    status_badge,
    subheading_label,
)


class CancellationView(QWidget):
    """a view that enables staff to search for bookings and process cancellations with automated fee calculations."""

    def __init__(self):
        """initialises the view and prepares the internal booking state."""
        super().__init__()
        self._booking = None
        self._build_ui()

    def _build_ui(self):
        """constructs the primary layout including the search interface and dynamic result cards."""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        # header section with view title and cancellation service description
        header_content = QVBoxLayout()
        header_content.setSpacing(4)
        header_content.addWidget(heading_label("Booking Cancellation"))
        desc = muted_label(
            "Search and process booking voidance, fee calculations, and customer refunds"
        )
        header_content.addWidget(desc)
        layout.addLayout(header_content)

        # search card for entering the Booking Reference
        search_card = Card()
        search_card.setFixedWidth(400)

        ref_lbl = QLabel("Booking Reference")
        ref_lbl.setFont(body_font(10, bold=True))
        ref_lbl.setStyleSheet(
            f"color: {TEXT_SECONDARY}; background: transparent; margin-bottom: 2px;"
        )
        search_card.add(ref_lbl)

        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("e.g. HC-2025-00001")
        self.ref_input.setStyleSheet(
            f"border: 1.5px solid {BORDER}; border-radius: 8px; min-height: 34px; max-height: 34px; padding: 0 10px;"
        )
        search_card.add(self.ref_input)

        self.search_btn = primary_button("Look Up Booking")
        self.search_btn.setStyleSheet(
            f"QPushButton {{ background-color: {HERO_BG}; color: {WHITE}; border: none; "
            f"min-height: 34px; max-height: 34px; font-weight: 700; border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: #2E2C28; }}"
        )
        self.search_btn.clicked.connect(self._lookup_booking)
        search_card.add(self.search_btn)

        layout.addWidget(search_card)

        # dynamic card for displaying retrieved booking details
        self.details_card = Card()
        self.details_card.hide()
        layout.addWidget(self.details_card)

        # dynamic card for displaying cancellation results
        self.result_card = Card()
        self.result_card.hide()
        layout.addWidget(self.result_card)

        layout.addStretch()

        self.ref_input.returnPressed.connect(self._lookup_booking)

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _lookup_booking(self):
        """fetches booking details from the api using the provided reference."""
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

    def _clear_card(self, card: Card):
        """recursively removes all widgets and layouts from a Card to prepare for new data."""
        layout = card._layout
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_sub_layout(item.layout())

    def _clear_sub_layout(self, layout):
        """recursively clears a sub-layout of all nested items."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_sub_layout(item.layout())

    def _show_details(self, b: dict):
        """populates the details card with comprehensive information about the retrieved booking."""
        self._clear_card(self.details_card)

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
            warn.setStyleSheet(
                f"color: {DANGER}; background: transparent; font-weight: 500; padding: 4px;"
            )
            self.details_card.add(warn)

            cancel_btn = danger_button("Cancel This Booking")
            cancel_btn.setStyleSheet(
                f"background-color: {ACCENT}; color: {WHITE}; border: none; min-height: 34px; max-height: 34px;"
            )
            cancel_btn.clicked.connect(self._cancel_booking)
            self.details_card.add(cancel_btn)

        self.details_card.show()

    def _cancel_booking(self):
        """initiates the cancellation process after user confirmation via a QDialog."""
        if not self._booking:
            return

        ref = self._booking["booking_reference"]
        ok = confirm_dialog(
            self,
            "Confirm Cancellation",
            f"Are you sure you want to cancel booking {ref}?\n\n"
            f"A 50% cancellation fee will be charged.",
        )
        if not ok:
            return

        try:
            result = api.cancel_booking(ref)
            self.details_card.hide()  # Hide the old details to avoid clutter
            self._show_cancel_result(result)
            show_toast(self, result.get("message", "Booking cancelled."), success=True)
            # No need to call _lookup_booking here as result_card shows the outcome
        except Exception as e:
            detail = str(e)
            if hasattr(e, "response"):
                try:
                    detail = e.response.json().get("detail", detail)
                except Exception:
                    pass
            error_dialog(self, detail)

    def _show_cancel_result(self, result: dict):
        """updates the UI to show the outcome of the cancellation including fees and refunds."""
        self._clear_card(self.result_card)

        self.result_card.add(subheading_label("Cancellation Processed", 12))
        self.result_card.add(separator())
        self.result_card.add_layout(labelled_value("Reference", result["booking_reference"]))
        self.result_card.add_layout(labelled_value("Status", result["booking_status"].capitalize()))
        self.result_card.add_layout(
            labelled_value("Fee Charged", f"\u00a3{result['cancellation_fee']:.2f}")
        )
        self.result_card.add_layout(
            labelled_value("Refund", f"\u00a3{result['refund_amount']:.2f}")
        )
        self.result_card.show()
