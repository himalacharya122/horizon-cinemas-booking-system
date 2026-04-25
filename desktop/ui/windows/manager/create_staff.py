# ============================================
# Author: Ridesha khadka
# Student ID: 23002960
# Last Edited: 2026-04-25
# ============================================

"""
desktop/ui/windows/manager/create_staff.py
implements the Manager view for creating and registering new staff user accounts.
assigns default passwords and links new users to specific cinema locations.
"""

from PyQt6.QtCore import Qt  # type: ignore
from PyQt6.QtGui import QShowEvent  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QComboBox,
    QFormLayout,
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
    ACCENT_HOVER,
    BORDER,
    GOLD,
    SPACING_LG,
    SPACING_MD,
    SPACING_SM,
    SUCCESS,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WHITE,
    body_font,
)
from desktop.ui.widgets import (
    Card,
    error_dialog,
    heading_label,
    muted_label,
    primary_button,
    secondary_button,
    separator,
    show_toast,
)


class CreateStaffView(QWidget):
    """a form-based view for Managers to provision new user accounts with specific roles and cinema assignments."""

    def __init__(self):
        """initialises the CreateStaffView and builds the registration form."""
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        """constructs the primary UI layout featuring the registration form and informational banners."""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        # header section with view title and descriptive subtitle
        header_content = QVBoxLayout()
        header_content.setSpacing(4)
        header_content.addWidget(heading_label("Create Staff Account"))
        header_content.addWidget(
            muted_label("Register a new booking staff, admin, or manager account")
        )

        header = QHBoxLayout()
        header.addLayout(header_content)
        header.addStretch()
        layout.addLayout(header)
        layout.addWidget(separator())

        # informational banner regarding the default account password
        info_card = Card()
        info_lbl = QLabel(
            "New accounts are assigned the default password:  Horizon@123  "
            "— the user should change it on first login."
        )
        info_lbl.setFont(body_font(10))
        info_lbl.setStyleSheet(f"color: {GOLD}; background: transparent; padding: 4px 0;")
        info_lbl.setWordWrap(True)
        info_card.add(info_lbl)
        layout.addWidget(info_card)

        # registration form card containing all input fields
        form_card = Card()
        form_inner = QVBoxLayout()
        form_inner.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        form_inner.setSpacing(SPACING_SM)

        form = QFormLayout()
        form.setSpacing(SPACING_SM)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(SPACING_MD)

        def _lbl(text: str) -> QLabel:
            """helper function to create styled form labels."""
            lbl = QLabel(text)
            lbl.setFont(body_font(10, bold=True))
            lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
            return lbl

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("e.g. john.smith")
        form.addRow(_lbl("Username:"), self.username_input)

        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("John")
        form.addRow(_lbl("First Name:"), self.first_name_input)

        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Smith")
        form.addRow(_lbl("Last Name:"), self.last_name_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("john.smith@horizon.com")
        form.addRow(_lbl("Email:"), self.email_input)

        self.role_combo = QComboBox()
        self.role_combo.addItems(["booking_staff", "admin", "manager"])
        form.addRow(_lbl("Role:"), self.role_combo)

        self.cinema_combo = QComboBox()
        form.addRow(_lbl("Cinema:"), self.cinema_combo)

        form_inner.addLayout(form)
        form_card.layout().addLayout(form_inner)
        layout.addWidget(form_card)

        # action buttons for account creation and form clearing
        btn_row = QHBoxLayout()
        btn_row.setSpacing(SPACING_SM)

        create_btn = primary_button("Create Account")
        create_btn.setStyleSheet(
            f"QPushButton {{ background-color: {ACCENT}; color: {WHITE}; border: none; "
            f"min-height: 34px; max-height: 34px; min-width: 140px; font-weight: 700; "
            f"border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}"
        )
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.clicked.connect(self._create_user)
        btn_row.addWidget(create_btn)

        clear_btn = secondary_button("Clear Form")
        clear_btn.setStyleSheet(
            f"QPushButton {{ background-color: {WHITE}; color: {TEXT_PRIMARY}; "
            f"border: 1.5px solid {BORDER}; min-height: 34px; max-height: 34px; "
            f"min-width: 110px; font-weight: 600; border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: #F1F1EF; border-color: #CDCBC6; }}"
        )
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_form)
        btn_row.addWidget(clear_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        # result area displaying feedback upon successful account creation
        self.result_card = Card()
        self.result_card.hide()
        self.result_label = QLabel("")
        self.result_label.setFont(body_font(10))
        self.result_label.setWordWrap(True)
        self.result_label.setStyleSheet(
            f"color: {SUCCESS}; background: transparent; padding: 4px 0;"
        )
        self.result_card.add(self.result_label)
        layout.addWidget(self.result_card)

        layout.addStretch(1)

        scroll.setWidget(content)
        outer.addWidget(scroll)

        # populate the cinema selection dropdown
        self._load_cinemas()

    def showEvent(self, event: QShowEvent):
        """refreshes the cinema list whenever the view is shown to ensure consistency."""
        super().showEvent(event)
        # refresh cinema list in case a new cinema was added elsewhere
        current = self.cinema_combo.currentData()
        self.cinema_combo.clear()
        self._load_cinemas()
        # restore the previous cinema selection if it remains valid
        if current is not None:
            for i in range(self.cinema_combo.count()):
                if self.cinema_combo.itemData(i) == current:
                    self.cinema_combo.setCurrentIndex(i)
                    break

    def _load_cinemas(self):
        """fetches the available cinemas from the api and populates the dropdown."""
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
        """collects form data and submits a user creation request via the api."""
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
            result = api.create_user(
                {
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "role": role,
                    "cinema_id": cinema_id,
                }
            )
            msg = result.get("message", "User created.")
            self.result_label.setText(
                f"{msg}\n"
                f"User ID: {result.get('user_id', '?')}   |   "
                f"Role: {result.get('role', '?')}   |   "
                f"Cinema: {result.get('cinema_name', '?')}"
            )
            self.result_card.show()
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
        """resets all input fields and selection dropdowns to their default states."""
        self.username_input.clear()
        self.first_name_input.clear()
        self.last_name_input.clear()
        self.email_input.clear()
        self.role_combo.setCurrentIndex(0)
        if self.cinema_combo.count() > 0:
            self.cinema_combo.setCurrentIndex(0)
