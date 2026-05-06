# ============================================
# Author: Himal Acharya
# Student ID: 22085619
# Last Edited: 2026-04-25
# ============================================

"""
desktop/ui/windows/main_window.py
implements the main application shell for Horizon Cinemas Booking System.
it includes a scrollable sidebar with collapsible navigation sections and a QStackedWidget for
managing content views.
"""

from PyQt6.QtCore import Qt  # type: ignore
from PyQt6.QtGui import QPainter, QPixmap  # type: ignore
from PyQt6.QtSvg import QSvgRenderer  # type: ignore
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
    BG_DARKEST,
    BORDER,
    TEXT_PRIMARY,
    body_font,
    heading_font,
)

# sidebar styling constants
SIDEBAR_BG = "#F9F9F9"
SIDEBAR_BORDER = "#D1D1D1"
SIDEBAR_ITEM_HOVER = "#EEEEEE"
SIDEBAR_TEXT = "#222222"
SIDEBAR_TEXT_MUTED = "#777777"

# SVG path data for sidebar navigation icons
ICONS = {
    "Film Listings": '<path d="M2 18h20V6H2v12zM7 6v12M17 6v12M2 12h20"/>',
    "Browse All Films": (
        '<rect x="3" y="3" width="18" height="18" rx="2"/>'
        '<path d="M3 9h18M3 15h18M9 3v18M15 3v18"/>'
    ),
    "New Booking": '<circle cx="12" cy="12" r="10"/><path d="M12 8v8M8 12h8"/>',
    "Search Bookings": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "My Bookings Today": (
        '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><path d="M16 2v4M8 2v4M3 10h18"/>'
    ),
    "Cancel Booking": '<circle cx="12" cy="12" r="10"/><path d="m15 9-6 6M9 9l6 6"/>',
    "Cancelled Bookings": (
        '<path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 '
        '2 2v2"/>'
    ),
    "Manage Films": (
        '<path d="m22 8-6 4 6 4V8Z"/><rect x="2" y="6" width="14" height="12" rx="2" ry="2"/>'
    ),
    "Manage Listings": '<path d="M3 12h18M3 6h18M3 18h18"/>',
    "Manage Pricing": (
        '<circle cx="12" cy="12" r="10"/><path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8'
        'M12 18V6"/>'
    ),
    "Manage Users": (
        '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>'
        '<path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>'
    ),
    "All Bookings": (
        '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>'
        '<path d="M3 12c0 1.66 4 3 9 3s9-1.34 9-3"/>'
    ),
    "Cancellation Log": (
        '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
        '<path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/>'
    ),
    "AI Insights": '<path d="m13 2-2 10h8l-2 10"/>',
    "Reports": '<path d="M18 20V10M12 20V4M6 20v-6"/>',
    "Dashboard": (
        '<rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><path d="M3 9h18M9 21V9"/>'
    ),
    "Manage Cinemas": (
        '<path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>'
        '<polyline points="9 22 9 12 15 12 15 22"/>'
    ),
    "Create Staff": (
        '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>'
        '<line x1="19" y1="8" x2="19" y2="14"/><line x1="16" y1="11" x2="22" y2="11"/>'
    ),
    "My Profile": (
        '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>'
    ),
    "Help & Guide": (
        '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3M12 17h.01"/>'
    ),
}


class SidebarButton(QPushButton):
    """custom navigation button with dynamic SVG icons and hover states."""

    def __init__(self, text: str, icon_char: str = ""):
        """initialises the SidebarButton with text and sets up its internal layout for icons."""
        super().__init__()
        self.nav_label = text
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(body_font(10, bold=False))

        # internal layout for icon and text alignment
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(12, 0, 12, 0)
        self.layout.setSpacing(10)

        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(16, 16)
        self.icon_lbl.setStyleSheet("border: none; background: transparent;")
        self.layout.addWidget(self.icon_lbl)

        self.text_lbl = QLabel(text)
        self.text_lbl.setStyleSheet("border: none; background: transparent;")
        self.layout.addWidget(self.text_lbl)
        self.layout.addStretch(1)

        self._update_style(False)

    def _update_style(self, checked: bool):
        """updates the visual style of the button based on its checked state."""
        color = ACCENT if checked else SIDEBAR_TEXT
        font_weight = 700 if checked else 500
        self.text_lbl.setStyleSheet(
            f"color: {color}; font-weight: {font_weight}; border: none; background: transparent;"
        )
        self._set_icon(color)

        self.setStyleSheet(
            "QPushButton { background-color: transparent; border: none; "
            "min-height: 28px; max-height: 28px; }"
        )
        if not checked:
            self.setStyleSheet(
                self.styleSheet()
                + f"QPushButton:hover {{ background-color: {SIDEBAR_ITEM_HOVER}; }}"
            )

    def _set_icon(self, hex_color: str):
        """renders and applies the SVG icon to the SidebarButton using the specified color."""
        path_data = ICONS.get(self.nav_label, "")
        if not path_data:
            return
        svg_data = (
            f'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" '
            f'stroke="{hex_color}" stroke-width="2" stroke-linecap="round" '
            f'stroke-linejoin="round">{path_data}</svg>'
        ).encode("utf-8")
        renderer = QSvgRenderer(svg_data)
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        self.icon_lbl.setPixmap(pixmap)

    def setChecked(self, checked: bool):
        """overrides the default setChecked method to trigger visual style updates."""
        super().setChecked(checked)
        self._update_style(checked)


class CollapsibleSection(QWidget):
    """a sidebar navigation group that can toggle the visibility of its child buttons."""

    def __init__(self, title: str):
        """initialises the section with a title and sets up the toggleable container."""
        super().__init__()
        self._expanded = True
        self._buttons: list[SidebarButton] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(0)

        # header button that toggles the expansion state
        self.header = QPushButton(f"  {title}   -")
        self.header.setFont(body_font(8, bold=True))
        self.header.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header.setStyleSheet(
            f"QPushButton {{ text-align: left; color: {SIDEBAR_TEXT_MUTED}; "
            f"font-weight: 800; letter-spacing: 1px; "
            f"padding: 0px 16px; margin: 0px; border: none; "
            f"min-height: 28px; max-height: 28px; "
            f"background: transparent; border-radius: 0; }}"
            f"QPushButton:hover {{ color: {TEXT_PRIMARY}; }}"
        )
        self.header.clicked.connect(self._toggle)
        layout.addWidget(self.header)

        # layout container for navigation buttons (with indentation)
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(12, 0, 0, 0)
        self.container_layout.setSpacing(0)
        layout.addWidget(self.container)

        self._title = title

    def add_button(self, btn: SidebarButton):
        """adds a SidebarButton to this section's layout."""
        self._buttons.append(btn)
        self.container_layout.addWidget(btn)

    def _toggle(self):
        """toggles the expanded or collapsed state of the section content."""
        self._expanded = not self._expanded
        self.container.setVisible(self._expanded)
        arrow = "-" if self._expanded else "+"
        self.header.setText(f"  {self._title}   {arrow}")


class MainWindow(QWidget):
    """the primary application window that orchestrates sidebar navigation and content views."""

    def __init__(self, on_logout: callable):
        """initialises the MainWindow and builds the global UI shell."""
        super().__init__()
        self.on_logout = on_logout
        self._nav_buttons: list[SidebarButton] = []
        self._build_ui()

    def _build_ui(self):
        """constructs the primary layout including the sidebar, scroll area, and content stack."""
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # sidebar structure
        sidebar_frame = QFrame()
        sidebar_frame.setFixedWidth(300)
        sidebar_frame.setStyleSheet(
            f"QFrame {{ background-color: {SIDEBAR_BG}; "
            f"border-right: 1px solid {SIDEBAR_BORDER}; }}"
        )
        sidebar_outer = QVBoxLayout(sidebar_frame)
        sidebar_outer.setContentsMargins(0, 0, 0, 0)
        sidebar_outer.setSpacing(0)

        # brand section containing the logo and cinema information
        brand_frame = QFrame()
        brand_frame.setFixedHeight(80)
        brand_frame.setStyleSheet(
            f"background: transparent; border: none; border-bottom: 1px solid {BORDER};"
        )
        bl = QHBoxLayout(brand_frame)
        bl.setContentsMargins(16, 0, 16, 0)
        bl.setSpacing(12)

        logo_label = self._make_logo_label(32)
        logo_label.setStyleSheet("border: none; background: transparent;")
        bl.addWidget(logo_label)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        brand_title = QLabel('Horizon <span style="color: #B91C1C;">Cinemas</span>')
        brand_title.setFont(heading_font(11, bold=True))
        brand_title.setStyleSheet("color: #0A0908; background: transparent; border: none;")
        text_layout.addWidget(brand_title)

        cinema_lbl = QLabel(api.cinema_name)
        cinema_lbl.setFont(body_font(8, bold=True))
        cinema_lbl.setStyleSheet(
            f"color: {SIDEBAR_TEXT_MUTED}; background: transparent; border: none;"
        )
        text_layout.addWidget(cinema_lbl)
        bl.addLayout(text_layout)
        bl.addStretch(1)
        sidebar_outer.addWidget(brand_frame)

        # scrollable navigation area for sidebar sections
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet(
            f"QScrollArea {{ border: none; background: transparent; }}"
            f"QScrollBar:vertical {{ width: 7px; background: {SIDEBAR_BG}; "
            f"border: none; margin-right: 1px; }}"
            f"QScrollBar::handle:vertical {{ background: {ACCENT}; border-radius: 3px; "
            f"min-height: 40px; border: none; }}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; "
            f"border: none; background: none; }}"
            f"QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ "
            f"background: {SIDEBAR_BG}; border: none; }}"
        )

        nav_widget = QWidget()
        nav_widget.setStyleSheet("background: transparent; border: none;")
        sb = QVBoxLayout(nav_widget)
        sb.setContentsMargins(0, 5, 0, 5)
        sb.setSpacing(0)

        # role-based generation of sidebar menu items
        role = api.role

        # films and bookings section accessible to all staff
        fb_sec = CollapsibleSection("Films and Bookings")
        self._add_nav(fb_sec, "Film Listings")
        self._add_nav(fb_sec, "Browse All Films")
        self._add_nav(fb_sec, "New Booking")
        self._add_nav(fb_sec, "Search Bookings")
        self._add_nav(fb_sec, "My Bookings Today")
        sb.addWidget(fb_sec)

        # cancellations management section
        cancel_sec = CollapsibleSection("Cancellations")
        self._add_nav(cancel_sec, "Cancel Booking")
        self._add_nav(cancel_sec, "Cancelled Bookings")
        sb.addWidget(cancel_sec)

        # administrative tools for Admin and Manager roles
        if role in ("admin", "manager"):
            admin_sec = CollapsibleSection("Administration")
            self._add_nav(admin_sec, "Manage Films")
            self._add_nav(admin_sec, "Manage Listings")
            self._add_nav(admin_sec, "Manage Pricing")
            self._add_nav(admin_sec, "Manage Users")
            self._add_nav(admin_sec, "All Bookings")
            self._add_nav(admin_sec, "Cancellation Log")
            self._add_nav(admin_sec, "AI Insights")
            self._add_nav(admin_sec, "Reports")
            sb.addWidget(admin_sec)

        # management exclusive tools for the Manager role
        if role == "manager":
            mgr_sec = CollapsibleSection("Management")
            self._add_nav(mgr_sec, "Dashboard")
            self._add_nav(mgr_sec, "Manage Cinemas")
            self._add_nav(mgr_sec, "Create Staff")
            sb.addWidget(mgr_sec)

        # personal account management section
        acct_sec = CollapsibleSection("Account")
        self._add_nav(acct_sec, "My Profile")
        self._add_nav(acct_sec, "Help & Guide")
        sb.addWidget(acct_sec)

        sb.addStretch(1)
        scroll.setWidget(nav_widget)
        sidebar_outer.addWidget(scroll, 1)

        # bottom user profile section with logout trigger
        user_frame = QFrame()
        user_frame.setFixedHeight(90)
        user_frame.setStyleSheet(
            f"background: transparent; border: none; border-top: 1px solid {BORDER};"
        )
        ul = QHBoxLayout(user_frame)
        ul.setContentsMargins(16, 0, 16, 12)
        ul.setSpacing(10)
        ul.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # avatar circle showing the user's initials
        initials = "".join([n[0] for n in api.display_name.split()[:2]]).upper()
        avatar = QLabel(initials)
        avatar.setFixedSize(34, 34)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFont(body_font(9, bold=True))
        avatar.setStyleSheet(
            "background-color: #0A0908; color: #FFFFFF; border-radius: 17px; border: none;"
        )
        ul.addWidget(avatar)

        # user details including name and role
        info_layout = QVBoxLayout()
        info_layout.setSpacing(0)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        name_lbl = QLabel(api.display_name)
        name_lbl.setFont(body_font(10, bold=True))
        name_lbl.setStyleSheet("color: #0A0908; border: none; background: transparent;")
        info_layout.addWidget(name_lbl)
        role_lbl = QLabel(api.role.replace("_", " ").title())
        role_lbl.setFont(body_font(7, bold=True))
        role_lbl.setStyleSheet(
            f"color: {SIDEBAR_TEXT_MUTED}; border: none; background: transparent;"
        )
        info_layout.addWidget(role_lbl)
        ul.addLayout(info_layout)
        ul.addStretch(1)

        # button to trigger the logout process
        logout_btn = QPushButton("Sign Out")
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.setFont(body_font(8, bold=True))
        logout_btn.setStyleSheet(
            f"QPushButton {{ color: {SIDEBAR_TEXT_MUTED}; background: transparent; "
            f"border: none; padding: 4px; }} "
            f"QPushButton:hover {{ color: {ACCENT}; }}"
        )
        logout_btn.clicked.connect(self._do_logout)
        ul.addWidget(logout_btn)
        sidebar_outer.addWidget(user_frame)

        root.addWidget(sidebar_frame)

        # main QStackedWidget to host content views
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background-color: {BG_DARKEST};")
        root.addWidget(self.stack, 1)

        self._pages: dict[str, QWidget] = {}
        if self._nav_buttons:
            self._nav_buttons[0].click()

    def _make_logo_label(self, size: int) -> QLabel:
        """renders a circular application logo using SVG data as a QLabel pixmap."""
        lbl = QLabel()
        lbl.setFixedSize(size, size)
        svg_data = (
            f'<svg width="{size}" height="{size}" viewBox="0 0 64 64" fill="none" '
            f'xmlns="http://www.w3.org/2000/svg"><circle cx="32" cy="32" r="32" '
            f'fill="black"/><rect x="20" y="15" width="6" height="34" fill="white"/>'
            f'<rect x="38" y="15" width="6" height="34" fill="white"/>'
            f'<rect x="20" y="29" width="24" height="6" fill="white"/></svg>'
        ).encode("utf-8")
        renderer = QSvgRenderer(svg_data)
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        lbl.setPixmap(pixmap)
        return lbl

    def _add_nav(self, section: CollapsibleSection, label: str):
        """instantiates a SidebarButton and connects it to the navigation logic."""
        btn = SidebarButton(label)
        btn.clicked.connect(lambda checked, label_val=label: self._navigate(label_val))
        section.add_button(btn)
        self._nav_buttons.append(btn)

    def _navigate(self, label: str):
        """updates sidebar selection and switches the content stack to the requested view."""
        for btn in self._nav_buttons:
            btn.setChecked(btn.nav_label == label)
        if label not in self._pages:
            page = self._create_page(label)
            self._pages[label] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self._pages[label])

    def _create_page(self, label: str) -> QWidget:
        """factory method to instantiate the appropriate view widget based on the navigation
        label.
        """
        # staff views
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

        # admin and analytics views
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
            elif label == "AI Insights":
                from desktop.ui.windows.admin.ai_insights import AIInsightsView

                return AIInsightsView()

        # manager exclusive views
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

        # fallback for undefined routes
        from desktop.ui.theme import TEXT_MUTED

        placeholder = QLabel(f"{label}\n\nComing soon...")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setFont(body_font(14))
        placeholder.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        return placeholder

    def _do_logout(self):
        """clears the session via API and triggers the on_logout callback."""
        api.logout()
        self.on_logout()
