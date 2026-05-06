# ============================================
# Author: Himal Acharya
# Student ID: 22085619
# Last Edited: 2026-04-25
# ============================================

"""
desktop/ui/windows/login_window.py
implements the login screen with a split layout featuring a branding section and a credential form.
the design follows the Horizon Cinemas brand guidelines for consistency and security.
"""

from PyQt6.QtCore import QByteArray, QSize, Qt  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from desktop.api_client import api
from desktop.ui.theme import (
    ACCENT,
    ACCENT_HOVER,
    BG_DARK,
    BG_INPUT,
    BORDER,
    SPACING_MD,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WHITE,
    body_font,
    heading_font,
)

# configuration for user roles available on the login screen
_ROLES = [
    {"id": "staff", "label": "Staff", "hint": "Counter & box-office sign-in"},
    {"id": "manager", "label": "Manager", "hint": "Branch operations & reports"},
    {"id": "admin", "label": "Admin", "hint": "System configuration access"},
]

_LOGO_SVG = b"""<svg width="36" height="36" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <circle cx="24" cy="24" r="22" fill="none" stroke="#000000" stroke-width="2.5"/>
  <circle cx="39" cy="24" r="2.6" fill="#000000"/>
  <circle cx="31.5" cy="37" r="2.6" fill="#000000"/>
  <circle cx="16.5" cy="37" r="2.6" fill="#000000"/>
  <circle cx="9"    cy="24" r="2.6" fill="#000000"/>
  <circle cx="16.5" cy="11" r="2.6" fill="#000000"/>
  <circle cx="31.5" cy="11" r="2.6" fill="#000000"/>
  <circle cx="24" cy="24" r="9.5" fill="#000000"/>
  <rect x="19"  y="19"   width="2.2" height="10" fill="#ffffff"/>
  <rect x="26.8" y="19"  width="2.2" height="10" fill="#ffffff"/>
  <rect x="19"  y="23.2" width="10"  height="1.6" fill="#B91C1C"/>
</svg>"""


def _make_logo_label(size: int = 36) -> QLabel:
    """renders the brand logo from embedded SVG data as a QLabel pixmap."""
    lbl = QLabel()
    lbl.setStyleSheet("background: transparent; border: none;")
    lbl.setFixedSize(size, size)
    try:
        from PyQt6.QtGui import QPainter, QPixmap  # type: ignore
        from PyQt6.QtSvg import QSvgRenderer  # type: ignore

        renderer = QSvgRenderer(QByteArray(_LOGO_SVG))
        px = QPixmap(size, size)
        px.fill(Qt.GlobalColor.transparent)
        painter = QPainter(px)
        renderer.render(painter)
        painter.end()
        lbl.setPixmap(px)
    except Exception:
        # fallback text-based logo if SVG rendering fails
        lbl.setText("HC")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(
            f"background: #000000; color: #fff; border-radius: {size // 2}px; "
            f"font-weight: 800; font-size: 11pt;"
        )
    return lbl


class _RoleTabs(QWidget):
    """a custom tab selector widget for switching between Staff, Manager, and Admin login modes."""

    def __init__(self, parent=None):
        """initialises the role selector and builds its internal layout."""
        super().__init__(parent)
        self._selected = "staff"
        self._buttons: dict[str, QPushButton] = {}
        self._callbacks: list = []
        self._build()

    def _build(self):
        """constructs the horizontal layout and buttons for role selection."""
        self.setFixedHeight(48)
        self.setObjectName("roleTabs")
        self.setStyleSheet(f"#roleTabs {{ background: {BG_DARK}; border-radius: 10px; }}")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(3)

        for role in _ROLES:
            btn = QPushButton(role["label"])
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(0)
            btn.setMaximumHeight(40)
            self._buttons[role["id"]] = btn
            btn.clicked.connect(lambda checked, r=role["id"]: self._select(r))
            layout.addWidget(btn)

        self._refresh_styles()

    def _select(self, role_id: str):
        """internal handler for role selection changes."""
        self._selected = role_id
        self._refresh_styles()
        for cb in self._callbacks:
            cb(role_id)

    def _refresh_styles(self):
        """updates the visual appearance of role buttons to reflect the current selection."""
        for role_id, btn in self._buttons.items():
            active = role_id == self._selected
            btn.setChecked(active)
            if active:
                btn.setStyleSheet(
                    f"QPushButton {{ background: {WHITE}; color: {TEXT_PRIMARY}; "
                    f"border: 1.5px solid {BORDER}; border-radius: 8px; "
                    f"padding: 3px 10px; min-height: 0px; max-height: 40px; "
                    f"font-weight: 700; font-size: 10pt; }}"
                )
            else:
                btn.setStyleSheet(
                    f"QPushButton {{ background: {BG_DARK}; color: {TEXT_MUTED}; "
                    f"border: 1.5px solid transparent; border-radius: 8px; "
                    f"padding: 3px 10px; min-height: 0px; max-height: 40px; "
                    f"font-weight: 500; font-size: 10pt; }}"
                    f"QPushButton:hover {{ background: {WHITE}; color: {TEXT_PRIMARY}; "
                    f"border-color: {BORDER}; }}"
                )

    def on_change(self, callback):
        """registers a callback to be invoked when the selected role changes."""
        self._callbacks.append(callback)

    @property
    def selected_id(self) -> str:
        """returns the internal ID of the currently selected role."""
        return self._selected

    @property
    def selected_label(self) -> str:
        """returns the human-readable label of the currently selected role."""
        return next(r["label"] for r in _ROLES if r["id"] == self._selected)

    @property
    def selected_hint(self) -> str:
        """returns the descriptive hint for the currently selected role."""
        return next(r["hint"] for r in _ROLES if r["id"] == self._selected)


class LoginWindow(QWidget):
    """the primary login interface for the application, handling user authentication and role
    verification.
    """

    def __init__(self, on_login_success: callable):
        """initialises the LoginWindow and sets its minimum dimensions."""
        super().__init__()
        self.on_login_success = on_login_success
        self.setMinimumSize(QSize(960, 640))
        self._build_ui()

    def _build_ui(self):
        """constructs the root layout and centers the login card."""
        self.setStyleSheet(f"background-color: {BG_DARK};")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addStretch(1)

        # horizontal center layout for the login card
        h_center = QHBoxLayout()
        h_center.addStretch(1)
        h_center.addWidget(self._build_login_card())
        h_center.addStretch(1)
        root.addLayout(h_center)

        root.addStretch(1)

    def _build_login_card(self) -> QFrame:
        """builds the login card containing the branding header, role selector, and credential
        form.
        """
        panel = QFrame()
        panel.setObjectName("loginCard")
        panel.setFixedWidth(600)
        panel.setStyleSheet(
            f"#loginCard {{ background-color: {WHITE}; border: 1px solid {BORDER}; "
            f"border-radius: 16px; }}"
        )

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(0)

        # branding header section with the logo and name
        brand_row = QHBoxLayout()
        brand_row.setSpacing(12)
        brand_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_lbl = _make_logo_label(36)
        brand_row.addWidget(logo_lbl)

        wordmark = QVBoxLayout()
        wordmark.setSpacing(1)

        brand = QLabel('Horizon <span style="color: #EF4444;">Cinemas</span>')
        brand.setTextFormat(Qt.TextFormat.RichText)
        brand.setFont(heading_font(18))
        brand.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent;")
        wordmark.addWidget(brand)

        booking_sys = QLabel("BOOKING SYSTEM")
        booking_sys.setFont(body_font(8))
        booking_sys.setStyleSheet(
            f"color: {TEXT_MUTED}; background: transparent; font-weight: 700; letter-spacing: 1px;"
        )
        wordmark.addWidget(booking_sys)

        brand_row.addLayout(wordmark)
        layout.addLayout(brand_row)

        layout.addSpacing(32)

        welcome = QLabel("Welcome back")
        welcome.setStyleSheet(
            f"color: {TEXT_PRIMARY}; background: transparent; font-weight: 800; font-size: 22pt;"
        )
        layout.addWidget(welcome)

        layout.addSpacing(6)

        subtitle = QLabel("Pick your role to continue.")
        subtitle.setFont(body_font(11))
        subtitle.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        layout.addWidget(subtitle)

        layout.addSpacing(24)

        # role selector tabs
        self.role_tabs = _RoleTabs()
        layout.addWidget(self.role_tabs)

        layout.addSpacing(10)

        self.role_hint = QLabel(self.role_tabs.selected_hint)
        self.role_hint.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        layout.addWidget(self.role_hint)

        layout.addSpacing(22)

        # username input field
        user_lbl = QLabel("Username")
        user_lbl.setFont(body_font(10))
        user_lbl.setStyleSheet(
            f"color: {TEXT_SECONDARY}; background: transparent; font-weight: 600;"
        )
        layout.addWidget(user_lbl)
        layout.addSpacing(6)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setFixedHeight(46)
        self.username_input.setStyleSheet(self._input_style())
        layout.addWidget(self.username_input)

        layout.addSpacing(14)

        # password input field
        pass_lbl = QLabel("Password")
        pass_lbl.setFont(body_font(10))
        pass_lbl.setStyleSheet(
            f"color: {TEXT_SECONDARY}; background: transparent; font-weight: 600;"
        )
        layout.addWidget(pass_lbl)
        layout.addSpacing(6)

        # password wrapper providing a show and hide toggle
        pw_frame = QFrame()
        pw_frame.setObjectName("pwFrame")
        pw_frame.setFixedHeight(46)
        pw_frame.setStyleSheet(
            f"#pwFrame {{ background: {BG_INPUT}; border: 1.5px solid {BORDER}; "
            f"border-radius: 8px; }}"
        )
        pw_layout = QHBoxLayout(pw_frame)
        pw_layout.setContentsMargins(12, 0, 8, 0)
        pw_layout.setSpacing(4)
        pw_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(44)
        self.password_input.setStyleSheet(
            f"QLineEdit {{ background: transparent; border: none; color: {TEXT_PRIMARY}; "
            f"font-size: 11pt; padding: 0; }}"
        )
        pw_layout.addWidget(self.password_input, 1, Qt.AlignmentFlag.AlignVCenter)

        self._show_pw_btn = QPushButton("Show")
        self._show_pw_btn.setFixedHeight(28)
        self._show_pw_btn.setMinimumWidth(40)
        self._show_pw_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._show_pw_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {TEXT_MUTED}; "
            f"border: none; font-size: 9pt; font-weight: 500; padding: 0 4px; }}"
            f"QPushButton:hover {{ color: {TEXT_PRIMARY}; }}"
        )
        self._show_pw_btn.clicked.connect(self._toggle_password)
        pw_layout.addWidget(self._show_pw_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(pw_frame)

        layout.addSpacing(16)

        # error message label for authentication failures
        self.error_label = QLabel("")
        self.error_label.setFont(body_font(10))
        self.error_label.setStyleSheet(
            "color: #B91C1C; background: #FEF2F2; "
            "border: 1px solid #FECACA; border-radius: 6px; padding: 8px 12px;"
        )
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        layout.addSpacing(22)

        # sign in submission button
        self.login_btn = QPushButton(f"Sign in as {self.role_tabs.selected_label}")
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setMinimumHeight(38)
        self.login_btn.setStyleSheet(
            f"QPushButton {{ background-color: {ACCENT}; color: {WHITE}; "
            f"border: none; border-radius: 10px; padding: 8px 18px; "
            f"font-weight: 700; font-size: 12pt; }}"
            f"QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}"
            f"QPushButton:pressed {{ background-color: #7F1D1D; }}"
            f"QPushButton:disabled {{ background-color: {BORDER}; color: {TEXT_MUTED}; }}"
        )
        self.login_btn.clicked.connect(self._do_login)
        layout.addWidget(self.login_btn)

        layout.addSpacing(40)

        # security notice for internal users
        security = QLabel("Internal use only. All sign-in attempts are logged.")
        security.setAlignment(Qt.AlignmentFlag.AlignCenter)
        security.setFont(body_font(9))
        security.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        layout.addWidget(security)

        layout.addSpacing(SPACING_MD)

        # connect role selection change events
        self.role_tabs.on_change(self._on_role_changed)

        # trigger login or focus change on Enter key press
        self.password_input.returnPressed.connect(self._do_login)
        self.username_input.returnPressed.connect(self.password_input.setFocus)

        return panel

    def _on_role_changed(self, role_id: str):
        """updates the UI elements when a new role is selected in the tabs."""
        self.role_hint.setText(self.role_tabs.selected_hint)
        self.login_btn.setText(f"Sign in as {self.role_tabs.selected_label}")
        self.error_label.hide()

    def _input_style(self) -> str:
        """returns the standard QSS style for input fields."""
        return (
            f"QLineEdit {{ background: {BG_INPUT}; border: 1.5px solid {BORDER}; "
            f"border-radius: 8px; padding: 10px 12px; color: {TEXT_PRIMARY}; "
            f"font-size: 11pt; min-height: 0px; }}"
            f"QLineEdit:focus {{ border-color: {ACCENT}; background: {WHITE}; }}"
        )

    def _toggle_password(self):
        """toggles the password field between hidden and plain text visibility."""
        if self.password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self._show_pw_btn.setText("Hide")
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self._show_pw_btn.setText("Show")

    # Maps the tab id \u2192 the role string the server returns
    _TAB_ROLE_MAP = {
        "staff": "booking_staff",
        "manager": "manager",
        "admin": "admin",
    }

    def _do_login(self):
        """authenticates the user with the backend and verifies role permissions."""
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            self._show_error("Please enter both username and password")
            return

        self.login_btn.setEnabled(False)
        self.login_btn.setText("Signing in\u2026")

        try:
            api.login(username, password)

            # enforce role matching between the selected tab and the user account
            selected_tab = self.role_tabs.selected_id
            expected_role = self._TAB_ROLE_MAP.get(selected_tab, "")
            if api.role != expected_role:
                api.logout()  # clear the session if roles do not match
                tab_label = self.role_tabs.selected_label
                self._show_error(
                    f"This account cannot sign in as {tab_label}. "
                    f"Please select the correct role tab."
                )
                return

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
            self.login_btn.setText(f"Sign in as {self.role_tabs.selected_label}")

    def _show_error(self, msg: str):
        """displays an error message in the login card."""
        self.error_label.setText(msg)
        self.error_label.show()
