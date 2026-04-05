"""
desktop/ui/windows/manager/create_staff.py
Manager view: create new staff user accounts.
"""

from PyQt6.QtCore import Qt  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QFormLayout, QScrollArea,
)

from desktop.ui.theme import (
    ACCENT, SUCCESS, GOLD,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    heading_font, body_font, SPACING_SM, SPACING_MD, SPACING_LG,
)
from desktop.ui.widgets import (
    heading_label, primary_button, secondary_button,
    separator, show_toast, error_dialog, Card, muted_label,
)
from desktop.api_client import api


class CreateStaffView(QWidget):

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

        layout.addWidget(heading_label("Create Staff Account"))
        layout.addWidget(separator())

        # Info
        info_card = Card()
        info_lbl = QLabel(
            "Create a new staff account. Default password: Horizon@123. "
            "The user should change their password on first login."
        )
        info_lbl.setFont(body_font(10))
        info_lbl.setStyleSheet(f"color: {GOLD}; background: transparent; padding: 4px;")
        info_lbl.setWordWrap(True)
        info_card.add(info_lbl)
        layout.addWidget(info_card)

        # Form
        form_card = Card()
        form = QFormLayout()
        form.setSpacing(SPACING_SM)

        def _form_label(text):
            lbl = QLabel(text)
            lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent; font-weight: 500;")
            return lbl

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("e.g. john.smith")
        form.addRow(_form_label("Username:"), self.username_input)

        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("John")
        form.addRow(_form_label("First Name:"), self.first_name_input)

        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Smith")
        form.addRow(_form_label("Last Name:"), self.last_name_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("john.smith@horizon.com")
        form.addRow(_form_label("Email:"), self.email_input)

        self.role_combo = QComboBox()
        self.role_combo.addItems(["booking_staff", "admin", "manager"])
        form.addRow(_form_label("Role:"), self.role_combo)

        self.cinema_combo = QComboBox()
        self._load_cinemas()
        form.addRow(_form_label("Cinema:"), self.cinema_combo)

        form_card.layout().addLayout(form)
        layout.addWidget(form_card)

        # Buttons
        btn_row = QHBoxLayout()
        create_btn = primary_button("Create Account")
        create_btn.clicked.connect(self._create_user)
        btn_row.addWidget(create_btn)

        clear_btn = secondary_button("Clear Form")
        clear_btn.clicked.connect(self._clear_form)
        btn_row.addWidget(clear_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Result area
        self.result_label = QLabel("")
        self.result_label.setFont(body_font(10))
        self.result_label.setWordWrap(True)
        self.result_label.setStyleSheet(f"color: {SUCCESS}; background: transparent; padding: 8px;")
        layout.addWidget(self.result_label)

        layout.addStretch(1)

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _load_cinemas(self):
        try:
            cinemas = api.get_cinemas()
            for c in cinemas:
                self.cinema_combo.addItem(
                    f"{c['cinema_name']} ({c.get('city_name', '')})",
                    c["cinema_id"],
                )
        except Exception:
            pass

    def _create_user(self):
        username = self.username_input.text().strip()
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        email = self.email_input.text().strip()
        role = self.role_combo.currentText()
        cinema_id = self.cinema_combo.currentData()

        if not all([username, first_name, last_name, email]):
            error_dialog(self, "All fields are required.")
            return

        if not cinema_id:
            error_dialog(self, "Please select a cinema.")
            return

        try:
            result = api.create_user({
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "role": role,
                "cinema_id": cinema_id,
            })
            msg = result.get("message", "User created.")
            self.result_label.setText(
                f"\u2705 {msg}\n"
                f"User ID: {result.get('user_id', '?')}  |  "
                f"Role: {result.get('role', '?')}  |  "
                f"Cinema: {result.get('cinema_name', '?')}"
            )
            show_toast(self, msg, success=True)
            self._clear_form()
        except Exception as e:
            detail = str(e)
            if hasattr(e, "response"):
                try:
                    detail = e.response.json().get("detail", detail)
                except Exception:
                    pass
            error_dialog(self, detail)

    def _clear_form(self):
        self.username_input.clear()
        self.first_name_input.clear()
        self.last_name_input.clear()
        self.email_input.clear()
        self.role_combo.setCurrentIndex(0)
        if self.cinema_combo.count() > 0:
            self.cinema_combo.setCurrentIndex(0)
