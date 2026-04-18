"""
desktop/ui/windows/main_window.py

Main application shell after login.
Scrollable left sidebar with collapsible sections + stacked content panel.
Sidebar items are role-gated and match the HCBS specification menus.
"""

from PyQt6.QtCore import Qt  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from desktop.api_client import api
from desktop.ui.theme import (
    ACCENT,
    ACCENT_LIGHT,
    BG_DARK,
    BG_DARKEST,
    BG_HOVER,
    BORDER,
    BORDER_LIGHT,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WHITE,
    body_font,
    heading_font,
)

# Sidebar button


class SidebarButton(QPushButton):
    """Navigation button in the sidebar."""

    def __init__(self, text: str, icon_char: str = ""):
        # Ignore icon_char completely to remove emojis for a professional look
        display = f"  {text}"
        super().__init__(display)
        self.nav_label = text  # store clean label for matching
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(body_font(10))
        self._update_style(False)

    def _update_style(self, checked: bool):
        if checked:
            self.setStyleSheet(
                f"QPushButton {{ text-align: left; padding: 0px 24px; margin: 0px; "
                f"background-color: {ACCENT_LIGHT}; color: {ACCENT}; "
                f"border: none; border-left: 4px solid {ACCENT}; "
                f"font-weight: 600; border-radius: 0; min-height: 34px; max-height: 34px; }}"
            )
        else:
            self.setStyleSheet(
                f"QPushButton {{ text-align: left; padding: 0px 24px; margin: 0px; "
                f"background-color: transparent; color: {TEXT_SECONDARY}; "
                f"border: none; border-left: 4px solid transparent; "
                f"font-weight: 500; border-radius: 0; min-height: 34px; max-height: 34px; }}"
                f"QPushButton:hover {{ background-color: {BG_HOVER}; color: {TEXT_PRIMARY}; "
                f"border-left: 4px solid {BORDER_LIGHT}; }}"
            )

    def setChecked(self, checked: bool):
        super().setChecked(checked)
        self._update_style(checked)


# Collapsible section


class CollapsibleSection(QWidget):
    """A sidebar section header that can expand/collapse its child nav buttons."""

    def __init__(self, title: str):
        super().__init__()
        self._expanded = True
        self._buttons: list[SidebarButton] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Section header (clickable)
        self.header = QPushButton(f"  {title}   —")
        self.header.setFont(body_font(9))
        self.header.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header.setStyleSheet(
            f"QPushButton {{ text-align: left; color: {TEXT_SECONDARY}; "
            f"font-weight: 600; letter-spacing: 0.5px; "
            f"padding: 0px 16px; margin: 0px; border: none; "
            f"min-height: 32px; max-height: 32px; "
            f"background: transparent; border-radius: 0; }}"
            f"QPushButton:hover {{ color: {WHITE}; background: rgba(255,255,255,0.03); }}"
        )
        self.header.clicked.connect(self._toggle)
        layout.addWidget(self.header)

        # Container for buttons
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(0)
        layout.addWidget(self.container)

        self._title = title

    def add_button(self, btn: SidebarButton):
        self._buttons.append(btn)
        self.container_layout.addWidget(btn)

    def _toggle(self):
        self._expanded = not self._expanded
        self.container.setVisible(self._expanded)
        arrow = "—" if self._expanded else "+"
        self.header.setText(f"  {self._title}   {arrow}")


# Main window


class MainWindow(QWidget):
    def __init__(self, on_logout: callable):
        super().__init__()
        self.on_logout = on_logout
        self._nav_buttons: list[SidebarButton] = []
        self._build_ui()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar outer frame
        sidebar_frame = QFrame()
        sidebar_frame.setFixedWidth(260)
        sidebar_frame.setStyleSheet(
            f"QFrame {{ background-color: {BG_DARK}; border-right: 1px solid {BORDER}; }}"
        )
        sidebar_outer = QVBoxLayout(sidebar_frame)
        sidebar_outer.setContentsMargins(0, 0, 0, 0)
        sidebar_outer.setSpacing(0)

        # Brand header (fixed, not scrollable)
        brand_frame = QFrame()
        brand_frame.setFixedHeight(60)
        brand_frame.setStyleSheet(f"border-bottom: 1px solid {BORDER}; background: {BG_DARK};")
        bl = QVBoxLayout(brand_frame)
        bl.setContentsMargins(16, 8, 16, 8)
        brand = QLabel("HORIZON CINEMAS")
        brand.setFont(heading_font(10))
        brand.setStyleSheet(
            f"color: {ACCENT}; background: transparent; border: none; letter-spacing: 1px;"
        )
        bl.addWidget(brand)
        cinema_lbl = QLabel(api.cinema_name)
        cinema_lbl.setFont(body_font(7))
        cinema_lbl.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent; border: none;")
        bl.addWidget(cinema_lbl)
        sidebar_outer.addWidget(brand_frame)

        # Scrollable nav area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            f"QScrollArea {{ border: none; background: {BG_DARK}; }}"
            f"QScrollBar:vertical {{ width: 6px; background: {BG_DARK}; border: none; "
            f"margin: 0px; }}"
            f"QScrollBar::handle:vertical {{ background: {BORDER_LIGHT}; "
            f"border-radius: 3px; min-height: 30px; }}"
            f"QScrollBar::handle:vertical:hover {{ background: {ACCENT}; }}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ "
            f"height: 0; border: none; }}"
            f"QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ "
            f"background: none; }}"
        )

        nav_widget = QWidget()
        nav_widget.setStyleSheet(f"background: {BG_DARK};")
        sb = QVBoxLayout(nav_widget)
        sb.setContentsMargins(0, 4, 0, 4)
        sb.setSpacing(0)

        role = api.role

        # FILMS
        films_sec = CollapsibleSection("FILMS")
        self._add_nav(films_sec, "Film Listings", "\U0001f3ac")
        self._add_nav(films_sec, "Browse All Films", "\U0001f4fd")
        sb.addWidget(films_sec)

        # BOOKINGS
        bookings_sec = CollapsibleSection("BOOKINGS")
        self._add_nav(bookings_sec, "New Booking", "\U0001f3ab")
        self._add_nav(bookings_sec, "Search Bookings", "\U0001f50d")
        self._add_nav(bookings_sec, "My Bookings Today", "\U0001f4c5")
        sb.addWidget(bookings_sec)

        # CANCELLATIONS
        cancel_sec = CollapsibleSection("CANCELLATIONS")
        self._add_nav(cancel_sec, "Cancel Booking", "\u2716")
        self._add_nav(cancel_sec, "Cancelled Bookings", "\U0001f4cb")
        sb.addWidget(cancel_sec)

        # ADMIN (admin/manager only)
        if role in ("admin", "manager"):
            admin_sec = CollapsibleSection("ADMINISTRATION")
            self._add_nav(admin_sec, "Manage Films", "\U0001f3ac")
            self._add_nav(admin_sec, "Manage Listings", "\U0001f4cb")
            self._add_nav(admin_sec, "Manage Pricing", "\U0001f4b0")
            self._add_nav(admin_sec, "Manage Users", "\U0001f465")
            self._add_nav(admin_sec, "All Bookings", "\U0001f4ca")
            self._add_nav(admin_sec, "Cancellation Log", "\U0001f4dc")
            self._add_nav(admin_sec, "Reports", "\U0001f4c8")
            sb.addWidget(admin_sec)

        # MANAGER (manager only)
        if role == "manager":
            mgr_sec = CollapsibleSection("MANAGEMENT")
            self._add_nav(mgr_sec, "Dashboard", "\U0001f4ca")
            self._add_nav(mgr_sec, "Manage Cinemas", "\U0001f3e2")
            self._add_nav(mgr_sec, "Create Staff", "\U0001f464")
            sb.addWidget(mgr_sec)

        # ACCOUNT
        acct_sec = CollapsibleSection("ACCOUNT")
        self._add_nav(acct_sec, "My Profile", "\U0001f464")
        self._add_nav(acct_sec, "Help & Guide", "\u2753")
        sb.addWidget(acct_sec)

        sb.addStretch(1)

        scroll.setWidget(nav_widget)
        sidebar_outer.addWidget(scroll, 1)

        # User info + logout (fixed at bottom, not scrollable)
        user_frame = QFrame()
        user_frame.setFixedHeight(120)
        user_frame.setStyleSheet(f"border-top: 1px solid {BORDER}; background: {BG_DARKEST};")
        uf = QVBoxLayout(user_frame)
        uf.setContentsMargins(16, 8, 16, 8)
        uf.setSpacing(2)

        name_lbl = QLabel(api.display_name)
        name_lbl.setFont(body_font(10))
        name_lbl.setStyleSheet(
            f"color: {TEXT_PRIMARY}; background: transparent; font-weight: 600; border: none;"
        )
        uf.addWidget(name_lbl)

        role_lbl = QLabel(api.role.replace("_", " ").title())
        role_lbl.setFont(body_font(9))
        role_lbl.setStyleSheet(
            f"color: {TEXT_MUTED}; background: transparent; border: none; font-weight: 500;"
        )
        uf.addWidget(role_lbl)

        logout_btn = QPushButton("Sign Out")
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.setFont(body_font(10))
        logout_btn.setStyleSheet(
            f"QPushButton {{ color: {TEXT_SECONDARY}; background: transparent; "
            f"border: 1px solid {BORDER}; border-radius: 4px; padding: 5px; "
            f"margin-top: 4px; font-weight: 500; }}"
            f"QPushButton:hover {{ background: {BG_HOVER}; color: {TEXT_PRIMARY}; }}"
        )
        logout_btn.clicked.connect(self._do_logout)
        uf.addWidget(logout_btn)

        sidebar_outer.addWidget(user_frame)
        root.addWidget(sidebar_frame)

        # Content area
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background-color: {BG_DARKEST};")
        root.addWidget(self.stack, 1)

        self._pages: dict[str, QWidget] = {}

        if self._nav_buttons:
            self._nav_buttons[0].click()

    # Navigation helpers

    def _add_nav(self, section: CollapsibleSection, label: str, icon: str = ""):
        btn = SidebarButton(label, icon)
        btn.clicked.connect(lambda checked, label_val=label: self._navigate(label_val))
        section.add_button(btn)
        self._nav_buttons.append(btn)

    def _navigate(self, label: str):
        for btn in self._nav_buttons:
            btn.setChecked(btn.nav_label == label)

        if label not in self._pages:
            page = self._create_page(label)
            self._pages[label] = page
            self.stack.addWidget(page)

        self.stack.setCurrentWidget(self._pages[label])

    def _create_page(self, label: str) -> QWidget:
        """Create the appropriate view widget for a nav label."""
        # ─── Booking Staff pages ───
        if label == "Film Listings":
            from desktop.ui.windows.booking_staff.film_listings import FilmListingsView

            return FilmListingsView()
        elif label == "Browse All Films":
            from desktop.ui.windows.booking_staff.browse_films import BrowseAllFilmsView

            return BrowseAllFilmsView()
        elif label == "New Booking":
            from desktop.ui.windows.booking_staff.new_booking import NewBookingView

            return NewBookingView()
        elif label == "Search Bookings":
            from desktop.ui.windows.booking_staff.search_booking import SearchBookingView

            return SearchBookingView()
        elif label == "My Bookings Today":
            from desktop.ui.windows.booking_staff.my_bookings_today import MyBookingsTodayView

            return MyBookingsTodayView()
        elif label == "Cancel Booking":
            from desktop.ui.windows.booking_staff.cancellation import CancellationView

            return CancellationView()
        elif label == "Cancelled Bookings":
            from desktop.ui.windows.booking_staff.cancelled_bookings import CancelledBookingsView

            return CancelledBookingsView()
        elif label == "My Profile":
            from desktop.ui.windows.booking_staff.profile_view import ProfileView

            return ProfileView()
        elif label == "Help & Guide":
            from desktop.ui.windows.booking_staff.help_view import HelpView

            return HelpView()

        # Admin pages
        if api.role in ("admin", "manager"):
            if label == "Manage Films":
                from desktop.ui.windows.admin.manage_films import ManageFilmsView

                return ManageFilmsView()
            elif label == "Manage Listings":
                from desktop.ui.windows.admin.manage_listings import ManageListingsView

                return ManageListingsView()
            elif label == "Manage Pricing":
                from desktop.ui.windows.admin.manage_pricing import ManagePricingView

                return ManagePricingView()
            elif label == "Manage Users":
                from desktop.ui.windows.admin.manage_users import ManageUsersView

                return ManageUsersView()
            elif label == "All Bookings":
                from desktop.ui.windows.admin.all_bookings import AllBookingsView

                return AllBookingsView()
            elif label == "Cancellation Log":
                from desktop.ui.windows.admin.cancellation_log import CancellationLogView

                return CancellationLogView()
            elif label == "Reports":
                from desktop.ui.windows.admin.reports import ReportsView

                return ReportsView()

        # Manager pages
        if api.role == "manager":
            if label == "Dashboard":
                from desktop.ui.windows.manager.dashboard import DashboardView

                return DashboardView()
            elif label == "Manage Cinemas":
                from desktop.ui.windows.manager.manage_cinemas import ManageCinemasView

                return ManageCinemasView()
            elif label == "Create Staff":
                from desktop.ui.windows.manager.create_staff import CreateStaffView

                return CreateStaffView()

        # Fallback
        placeholder = QLabel(f"{label}\n\nComing soon...")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setFont(body_font(14))
        placeholder.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        return placeholder

    def _do_logout(self):
        api.logout()
        self.on_logout()
