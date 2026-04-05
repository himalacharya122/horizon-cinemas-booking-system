"""
desktop/ui/windows/login_window.py
Login screen — dark cinema theme, centred card with username/password.
"""

from PyQt6.QtCore import Qt, QSize  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QWidget, QVBoxLayout, QLineEdit, QLabel, QPushButton, QFrame,
)

from desktop.ui.theme import (
    ACCENT, ACCENT_HOVER, WHITE,
    BG_DARKEST, BG_CARD, BG_INPUT, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    heading_font, body_font, SPACING_MD, SPACING_LG, SPACING_XL,
)
from desktop.api_client import api


class LoginWindow(QWidget):

    def __init__(self, on_login_success: callable):
        super().__init__()
        self.on_login_success = on_login_success
        self._build_ui()

    def _build_ui(self):
        self.setMinimumSize(QSize(480, 580))
        self.setStyleSheet(f"background-color: {BG_DARKEST};")

        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.setContentsMargins(SPACING_XL, SPACING_XL, SPACING_XL, SPACING_XL)

        # Brand
        brand = QLabel("HORIZON CINEMAS")
        brand.setFont(heading_font(28))
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand.setStyleSheet(f"color: {ACCENT}; background: transparent; letter-spacing: 3px;")
        outer.addWidget(brand)

        tagline = QLabel("Booking Management System")
        tagline.setFont(body_font(11))
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        outer.addWidget(tagline)

        outer.addSpacing(SPACING_LG)

        # Login Card
        card = QFrame()
        card.setFixedWidth(400)
        card.setStyleSheet(
            f"QFrame {{ background: {BG_CARD}; border: 1px solid {BORDER}; "
            f"border-radius: 10px; }}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(32, 32, 32, 32)
        cl.setSpacing(8)

        title = QLabel("Staff Login")
        title.setFont(heading_font(16))
        title.setStyleSheet(f"color: {WHITE}; background: transparent; border: none; margin-bottom: 8px;")
        cl.addWidget(title)

        subtitle = QLabel("Sign in to access the booking system")
        subtitle.setFont(body_font(10))
        subtitle.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent; border: none; margin-bottom: 16px;")
        cl.addWidget(subtitle)

        # Username
        user_lbl = QLabel("Username")
        user_lbl.setFont(body_font(10))
        user_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent; font-weight: 500; border: none;")
        cl.addWidget(user_lbl)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setStyleSheet(self._input_style())
        cl.addWidget(self.username_input)

        cl.addSpacing(8)

        # Password
        pass_lbl = QLabel("Password")
        pass_lbl.setFont(body_font(10))
        pass_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent; font-weight: 500; border: none;")
        cl.addWidget(pass_lbl)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(self._input_style())
        cl.addWidget(self.password_input)

        # Error label
        self.error_label = QLabel("")
        self.error_label.setFont(body_font(10))
        self.error_label.setStyleSheet(
            f"color: {ACCENT}; background: {ACCENT}22; border: none; "
            f"border-radius: 4px; padding: 8px; margin-top: 4px;"
        )
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        cl.addWidget(self.error_label)

        cl.addSpacing(SPACING_MD)

        # Login button — explicit style for guaranteed visibility
        self.login_btn = QPushButton("Sign In")
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setStyleSheet(
            f"QPushButton {{ background-color: {ACCENT}; color: {WHITE}; "
            f"border: none; border-radius: 6px; padding: 12px; "
            f"font-weight: 700; font-size: 12pt; min-height: 44px; }}"
            f"QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}"
            f"QPushButton:pressed {{ background-color: #9B2C2C; }}"
            f"QPushButton:disabled {{ background-color: {BORDER}; color: {TEXT_MUTED}; }}"
        )
        self.login_btn.clicked.connect(self._do_login)
        cl.addWidget(self.login_btn)

        outer.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)

        outer.addSpacing(SPACING_MD)
        footer = QLabel("\u00a9 2025 Horizon Cinemas \u2014 Internal Use Only")
        footer.setFont(body_font(9))
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        outer.addWidget(footer)

        self.password_input.returnPressed.connect(self._do_login)
        self.username_input.returnPressed.connect(self.password_input.setFocus)

    def _input_style(self) -> str:
        return (
            f"QLineEdit {{ background: {BG_INPUT}; border: 1px solid {BORDER}; "
            f"border-radius: 6px; padding: 10px 14px; color: {TEXT_PRIMARY}; "
            f"font-size: 11pt; min-height: 40px; }}"
            f"QLineEdit:focus {{ border: 1.5px solid {ACCENT}; }}"
        )

    def _do_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            self._show_error("Please enter both username and password")
            return

        self.login_btn.setEnabled(False)
        self.login_btn.setText("Signing in...")

        try:
            api.login(username, password)
            self.error_label.hide()
            self.on_login_success()
        except Exception as exc:
            detail = ""
            if hasattr(exc, "response"):
                try:
                    detail = exc.response.json().get("detail", str(exc))
                except Exception:
                    detail = str(exc)
            else:
                detail = str(exc)
            self._show_error(detail)
        finally:
            self.login_btn.setEnabled(True)
            self.login_btn.setText("Sign In")

    def _show_error(self, msg: str):
        self.error_label.setText(msg)
        self.error_label.show()
