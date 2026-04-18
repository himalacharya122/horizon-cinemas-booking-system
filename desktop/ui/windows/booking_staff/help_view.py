"""
desktop/ui/windows/booking_staff/help_view.py
User Guide and Contact Admin information.
"""

from PyQt6.QtWidgets import (  # type: ignore
    QLabel,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from desktop.ui.theme import (
    SPACING_LG,
    SPACING_MD,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    body_font,
)
from desktop.ui.widgets import (
    Card,
    heading_label,
    separator,
    subheading_label,
)


class HelpView(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        layout.addWidget(heading_label("Help & Guide"))
        layout.addWidget(separator())

        tabs = QTabWidget()

        # User Guide tab (scrollable)
        tabs.addTab(self._build_guide_tab(), "User Guide")

        # Contact Admin tab (scrollable)
        tabs.addTab(self._build_contact_tab(), "Contact Admin")

        layout.addWidget(tabs, 1)

    def _build_guide_tab(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        guide_page = QWidget()
        gl = QVBoxLayout(guide_page)
        gl.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        gl.setSpacing(SPACING_MD)

        sections = [
            (
                "Film Listings",
                (
                    "Browse films currently showing at your assigned cinema.\n"
                    "Use the date picker to view listings up to 7 days ahead.\n"
                    "Filter by genre, age rating, or showtime period.\n"
                    "Use the search box to find films by title."
                ),
            ),
            (
                "Making a Booking",
                (
                    "1. Go to New Booking from the sidebar.\n"
                    "2. Select the cinema, film, and showing.\n"
                    "3. Choose a date and seat type (Lower Hall / Upper Gallery / VIP).\n"
                    "4. Click 'Check Availability & Price' to see availability.\n"
                    "5. Fill in customer details (name is required).\n"
                    "6. Click 'Confirm Booking' to finalise.\n"
                    "7. The receipt will appear on the right — you can copy it to clipboard."
                ),
            ),
            (
                "Searching Bookings",
                (
                    "Go to Search Bookings from the sidebar.\n"
                    "You can search by booking reference, customer name, email, or phone.\n"
                    "Use the status filter to show only confirmed or cancelled bookings."
                ),
            ),
            (
                "Cancelling a Booking",
                (
                    "Go to Cancel Booking from the sidebar.\n"
                    "Enter the booking reference and click Look Up.\n"
                    "Review the booking details and cancellation fee (50%).\n"
                    "Note: Same-day cancellations are not permitted."
                ),
            ),
            (
                "Booking Rules",
                (
                    "\u2022 Bookings can be made up to 7 days in advance.\n"
                    "\u2022 Cancellations incur a 50% fee.\n"
                    "\u2022 Same-day cancellations are not allowed.\n"
                    "\u2022 Seat types: Lower Hall (standard), Upper Gallery (+20%), VIP (+44%).\n"
                    "\u2022 Pricing varies by city and show period (morning/afternoon/evening)."
                ),
            ),
        ]

        for title, text in sections:
            card = Card()
            card.add(subheading_label(title, 12))
            content = QLabel(text)
            content.setFont(body_font(10))
            content.setStyleSheet(
                f"color: {TEXT_SECONDARY}; background: transparent; line-height: 1.6;"
            )
            content.setWordWrap(True)
            card.add(content)
            gl.addWidget(card)

        gl.addStretch()
        scroll.setWidget(guide_page)
        return scroll

    def _build_contact_tab(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        contact_page = QWidget()
        cl = QVBoxLayout(contact_page)
        cl.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        cl.setSpacing(SPACING_MD)

        card = Card()
        card.setMaximumWidth(500)
        card.add(subheading_label("Contact Your Administrator", 13))
        card.add(separator())

        info = [
            ("For technical issues:", "Contact your cinema's system administrator."),
            ("For booking problems:", "Speak to your shift supervisor or admin on duty."),
            (
                "For account issues:",
                "Password resets and account changes must be\n"
                "requested through your cinema administrator.",
            ),
            (
                "Emergency support:",
                "Contact the Horizon Cinemas IT help desk\nat support@horizoncinemas.co.uk",
            ),
        ]

        for label, value in info:
            lbl = QLabel(label)
            lbl.setFont(body_font(10))
            lbl.setStyleSheet(
                f"color: {TEXT_MUTED}; background: transparent; font-weight: 600; margin-top: 8px;"
            )
            card.add(lbl)

            val = QLabel(value)
            val.setFont(body_font(10))
            val.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent;")
            val.setWordWrap(True)
            card.add(val)

        cl.addWidget(card)
        cl.addStretch()
        scroll.setWidget(contact_page)
        return scroll
