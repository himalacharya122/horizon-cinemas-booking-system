"""
desktop/ui/windows/booking_staff/profile_view.py
View own profile and shift details.
"""

from PyQt6.QtCore import Qt  # type: ignore
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea  # type: ignore

from desktop.ui.theme import (
    ACCENT, WHITE,
    BG_CARD, BG_HOVER, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    heading_font, body_font, SPACING_MD, SPACING_LG,
)
from desktop.ui.widgets import (
    heading_label, subheading_label, muted_label,
    Card, separator, labelled_value, badge_label,
)
from desktop.api_client import api


class ProfileView(QWidget):

    def __init__(self):
        super().__init__()
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

        layout.addWidget(heading_label("My Profile"))
        layout.addWidget(separator())

        # Profile card
        card = Card()
        card.setMaximumWidth(600)

        # Avatar / name header
        name = QLabel(api.display_name)
        name.setFont(heading_font(20))
        name.setStyleSheet(f"color: {WHITE}; background: transparent;")
        card.add(name)

        role_text = api.role.replace("_", " ").title()
        role = badge_label(role_text, ACCENT)
        card.add(role)

        card.add(separator())

        card.add(subheading_label("Account Details", 12))

        card.add_layout(labelled_value("Full Name", api.display_name))
        card.add_layout(labelled_value("Username", api.username))
        card.add_layout(labelled_value("Role", role_text))
        card.add_layout(labelled_value("User ID", str(api.user_id)))

        card.add(separator())

        card.add(subheading_label("Assignment", 12))

        card.add_layout(labelled_value("Home Cinema", api.cinema_name))
        card.add_layout(labelled_value("Cinema ID", str(api.cinema_id)))

        card.add(separator())

        card.add(subheading_label("Session", 12))

        status_text = "Active" if api.is_authenticated else "Not Authenticated"
        card.add_layout(labelled_value("Status", status_text))
        card.add_layout(labelled_value("Token", "Valid" if api.token else "None"))

        layout.addWidget(card)
        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)
