# ============================================
# Author: Smriti Ale
# Student ID: 24036547
# Last Edited: 2026-04-25
# ============================================

"""
desktop/ui/windows/booking_staff/profile_view.py
implements the Profile view for Booking Staff to view personal account details and manage security settings.
"""

from PyQt6.QtCore import Qt  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from desktop.api_client import api
from desktop.ui.theme import (
    ACCENT,
    BLACK,
    DANGER,
    SPACING_LG,
    SPACING_MD,
    SUCCESS,
    TEXT_MUTED,
    WHITE,
    body_font,
    heading_font,
)
from desktop.ui.widgets import (
    Card,
    badge_label,
    heading_label,
    labelled_value,
    muted_label,
    separator,
    subheading_label,
)


class ProfileView(QWidget):
    """a view displaying the current staff member's account information and password management tools."""

    def __init__(self):
        """initialises the profile view and builds the interface."""
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        """constructs the primary layout featuring profile details and password security cards."""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        main_layout.setSpacing(SPACING_MD)

        main_layout.addWidget(heading_label("My Profile"))

        # horizontal layout split for side-by-side card arrangement
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(SPACING_LG)
        cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        # left column: Profile Details card
        card = Card()
        card.setFixedWidth(470)

        # avatar and name header display
        name = QLabel(api.display_name)
        name.setFont(heading_font(24))
        name.setStyleSheet(f"color: {BLACK}; background: transparent;")
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

        card.add(subheading_label("Assignment", 12))
        card.add_layout(labelled_value("Home Cinema", api.cinema_name))
        card.add_layout(labelled_value("Cinema ID", str(api.cinema_id)))

        card.add(subheading_label("Session Status", 12))
        status_text = "Active Session" if api.is_authenticated else "Not Authenticated"
        card.add_layout(labelled_value("Status", status_text))
        card.add_layout(labelled_value("Auth Token", "Valid" if api.token else "None"))

        cards_layout.addWidget(card)

        # right column: Security and Password Change card
        pw_card = Card()
        pw_card.setFixedWidth(470)

        pw_card.add(subheading_label("Security", 12))
        pw_card.add(muted_label("Manage your account security and password."))
        pw_card.add(separator())

        pw_card.add(subheading_label("Change Password", 11))

        # input fields for password update
        self.current_pass = QLineEdit()
        self.current_pass.setPlaceholderText("Current Password")
        self.current_pass.setEchoMode(QLineEdit.EchoMode.Password)
        pw_card.add(self.current_pass)

        self.new_pass = QLineEdit()
        self.new_pass.setPlaceholderText("New Password (min 8 chars)")
        self.new_pass.setEchoMode(QLineEdit.EchoMode.Password)
        pw_card.add(self.new_pass)

        self.confirm_pass = QLineEdit()
        self.confirm_pass.setPlaceholderText("Confirm New Password")
        self.confirm_pass.setEchoMode(QLineEdit.EchoMode.Password)
        pw_card.add(self.confirm_pass)

        # status label for error and success messages
        self.status_lbl = QLabel("")
        self.status_lbl.setFont(body_font(9))
        self.status_lbl.setWordWrap(True)
        self.status_lbl.hide()
        pw_card.add(self.status_lbl)

        # submit button for updating the account password
        self.update_btn = QPushButton("Update Password")
        self.update_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_btn.setProperty("primary", True)  # use theme primary style
        self.update_btn.setStyleSheet(
            f"color: {WHITE}; background-color: {TEXT_MUTED}; border: none;"
        )
        self.update_btn.clicked.connect(self._do_change_password)
        pw_card.add(self.update_btn)

        cards_layout.addWidget(pw_card)

        main_layout.addLayout(cards_layout)
        main_layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _do_change_password(self):
        """validates inputs and submits a password change request to the api."""
        curr = self.current_pass.text()
        new_p = self.new_pass.text()
        conf = self.confirm_pass.text()

        if not curr or not new_p or not conf:
            self._show_status("All fields are required.", is_error=True)
            return

        if new_p != conf:
            self._show_status("New passwords do not match.", is_error=True)
            return

        if len(new_p) < 8:
            self._show_status("New password must be at least 8 characters.", is_error=True)
            return

        self.update_btn.setEnabled(False)
        self.update_btn.setText("Updating...")

        try:
            api.change_password(curr, new_p)
            self._show_status("Password updated successfully!", is_error=False)
            self.current_pass.clear()
            self.new_pass.clear()
            self.confirm_pass.clear()
        except Exception as exc:
            detail = str(exc)
            if hasattr(exc, "response"):
                try:
                    detail = exc.response.json().get("detail", str(exc))
                except Exception:
                    pass
            self._show_status(detail, is_error=True)
        finally:
            self.update_btn.setEnabled(True)
            self.update_btn.setText("Update Password")

    def _show_status(self, msg: str, is_error: bool):
        """displays a formatted status message in the security card."""
        color = DANGER if is_error else SUCCESS
        bg = f"{color}11"
        self.status_lbl.setText(msg)
        self.status_lbl.setStyleSheet(
            f"color: {WHITE}; background-color: {ACCENT};border-radius: 4px; padding: 10px;"
        )
        self.status_lbl.show()
