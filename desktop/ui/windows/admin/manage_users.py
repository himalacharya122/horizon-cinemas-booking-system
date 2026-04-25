# ============================================
# Author: Ridesha khadka
# Student ID: 23002960
# Last Edited: 2026-04-25
# ============================================

"""
desktop/ui/windows/admin/manage_users.py
implements the staff user management interface for Administrators to audit account activity and manage security credentials.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (  # type: ignore
    QComboBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from desktop.api_client import api
from desktop.ui.theme import (
    ACCENT,
    ACCENT_HOVER,
    BG_CARD,
    BORDER,
    DANGER,
    HERO_BG,
    SPACING_LG,
    SPACING_MD,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WHITE,
)
from desktop.ui.widgets import (
    confirm_dialog,
    danger_button,
    error_dialog,
    heading_label,
    muted_label,
    primary_button,
    secondary_button,
    show_toast,
)


class _LeftPaddingDelegate(QStyledItemDelegate):
    """a specialized item delegate to apply left padding to table cell content."""

    def __init__(self, padding: int = 14, parent=None):
        super().__init__(parent)
        self.padding = padding

    def paint(self, painter, option, index):
        padded = QStyleOptionViewItem(option)
        padded.rect.adjust(self.padding, 0, 0, 0)
        super().paint(painter, padded, index)


class ManageUsersView(QWidget):
    """a view for managing cinema staff accounts, including password resets and activity auditing."""

    def __init__(self):
        """initialises the user management view and loads account data."""
        super().__init__()
        self._users = []
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        """constructs the primary interface including account headers, filters, and the users table."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        # header section with view title and account management description
        header_content = QVBoxLayout()
        header_content.setSpacing(4)
        header_content.addWidget(heading_label("Manage Users"))
        desc = muted_label("Staff account management, password resets, and activity audit trails")
        header_content.addWidget(desc)

        header = QHBoxLayout()
        header.addLayout(header_content)
        header.addStretch()

        _combo_style = (
            f"QComboBox {{ border: 1.5px solid {BORDER}; border-radius: 8px; background-color: #F2F1EE; "
            f"padding: 4px 10px; color: {TEXT_PRIMARY}; outline: none; min-height: 34px; max-height: 34px; }}"
            f"QComboBox:focus {{ border-color: {ACCENT}; background-color: {WHITE}; }}"
            f"QComboBox::drop-down {{ border: none; width: 24px; }}"
            f"QComboBox QAbstractItemView {{ background-color: {WHITE}; selection-background-color: {ACCENT}; "
            f"selection-color: {WHITE}; border: 1px solid {BORDER}; outline: none; }}"
        )

        # filter controls for cinema and role-based searching
        lbl_cinema = QLabel("Cinema:")
        lbl_cinema.setStyleSheet(
            f"color: {TEXT_SECONDARY}; background: transparent; font-weight: 600;"
        )
        header.addWidget(lbl_cinema)
        self.cinema_filter = QComboBox()
        self.cinema_filter.setFixedWidth(220)
        self.cinema_filter.setStyleSheet(_combo_style)
        self.cinema_filter.setFixedHeight(34)
        self.cinema_filter.currentIndexChanged.connect(self._load_users)
        header.addWidget(self.cinema_filter)

        lbl_role = QLabel("Role:")
        lbl_role.setStyleSheet(
            f"color: {TEXT_SECONDARY}; background: transparent; font-weight: 600;"
        )
        header.addWidget(lbl_role)
        self.role_filter = QComboBox()
        self.role_filter.addItems(["All Roles", "booking_staff", "admin", "manager"])
        self.role_filter.setFixedWidth(150)
        self.role_filter.setStyleSheet(_combo_style)
        self.role_filter.setFixedHeight(34)
        self.role_filter.currentIndexChanged.connect(self._load_users)
        header.addWidget(self.role_filter)

        refresh_btn = secondary_button("Refresh")
        refresh_btn.setStyleSheet(
            f"QPushButton {{ background-color: {HERO_BG}; color: {WHITE}; border: none; "
            f"min-height: 34px; max-height: 34px; min-width: 90px; font-weight: 700; "
            f"border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: #2E2C28; }}"
        )
        refresh_btn.clicked.connect(self._load_data)
        header.addWidget(refresh_btn)

        layout.addLayout(header)

        # Users table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Username", "Full Name", "Email", "Role", "Cinema", "Status", "Last Login"]
        )

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 170)  # Full Name
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Email
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # Cinema
        hh.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setStyleSheet(
            f"QTableWidget {{ border: 1.5px solid {BORDER}; border-radius: 8px; }}"
            f"QHeaderView::section {{ border-right: 1px solid {BORDER}; border-bottom: 2.5px solid {BORDER}; }}"
            "QTableWidget::item:selected { background-color: #FEF2F2; color: #0A0908; }"
        )
        self.table.setItemDelegate(_LeftPaddingDelegate(14, self.table))
        layout.addWidget(self.table, 1)

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        reset_btn = primary_button("Reset Password")
        reset_btn.setStyleSheet(
            f"QPushButton {{ background-color: {ACCENT}; color: {WHITE}; border: none; "
            f"min-height: 34px; max-height: 34px; min-width: 140px; font-weight: 700; "
            f"border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}"
        )
        reset_btn.clicked.connect(self._reset_password)
        btn_row.addWidget(reset_btn)

        toggle_btn = danger_button("Toggle Active")
        toggle_btn.setStyleSheet(
            f"QPushButton {{ background-color: {DANGER}; color: {WHITE}; border: none; "
            f"min-height: 34px; max-height: 34px; min-width: 130px; font-weight: 700; "
            f"border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: #B91C1C; }}"
        )
        toggle_btn.clicked.connect(self._toggle_active)
        btn_row.addWidget(toggle_btn)

        activity_btn = secondary_button("View Activity")
        activity_btn.setStyleSheet(
            f"QPushButton {{ background-color: {HERO_BG}; color: {WHITE}; border: none; "
            f"min-height: 34px; max-height: 34px; min-width: 120px; font-weight: 700; "
            f"border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: #2E2C28; }}"
        )
        activity_btn.clicked.connect(self._view_activity)
        btn_row.addWidget(activity_btn)

        btn_row.addStretch()

        self.count_label = muted_label("")
        btn_row.addWidget(self.count_label)

        layout.addLayout(btn_row)

    def _load_data(self):
        """Load cinema filter options and user data."""
        try:
            cinemas = api.get_cinemas()
            self.cinema_filter.blockSignals(True)
            self.cinema_filter.clear()
            self.cinema_filter.addItem("All Cinemas", None)
            for c in cinemas:
                self.cinema_filter.addItem(
                    f"{c['cinema_name']} ({c.get('city_name', '')})",
                    c["cinema_id"],
                )
            self.cinema_filter.blockSignals(False)
            self._load_users()
        except Exception as e:
            error_dialog(self, f"Failed to load data: {e}")

    def _load_users(self):
        """Load users with current filters."""
        cinema_id = self.cinema_filter.currentData()
        role = self.role_filter.currentText()
        if role == "All Roles":
            role = None

        try:
            self._users = api.get_users(
                cinema_id=cinema_id,
                role=role,
                active_only=False,
            )
            self._fill_table(self._users)
        except Exception as e:
            error_dialog(self, f"Failed to load users: {e}")

    def _fill_table(self, users: list):
        self.table.setRowCount(len(users))
        for row, u in enumerate(users):
            self.table.setItem(row, 0, QTableWidgetItem(str(u["user_id"])))
            self.table.setItem(row, 1, QTableWidgetItem(u["username"]))
            self.table.setItem(row, 2, QTableWidgetItem(u["full_name"]))
            self.table.setItem(row, 3, QTableWidgetItem(u["email"]))
            self.table.setItem(row, 4, QTableWidgetItem(u["role"].replace("_", " ").title()))
            self.table.setItem(row, 5, QTableWidgetItem(u["cinema_name"]))

            status = "Active" if u["is_active"] else "Inactive"
            status_item = QTableWidgetItem(status)
            self.table.setItem(row, 6, status_item)

            last_login = u.get("last_login") or "\u2014"
            if last_login != "\u2014":
                last_login = last_login[:19].replace("T", " ")
            self.table.setItem(row, 7, QTableWidgetItem(last_login))

        self.count_label.setText(f"{len(users)} user(s)")

    def _get_selected_user(self) -> dict | None:
        row = self.table.currentRow()
        if row < 0:
            error_dialog(self, "Please select a user first.")
            return None
        if row < len(self._users):
            return self._users[row]
        return None

    def _reset_password(self):
        user = self._get_selected_user()
        if not user:
            return

        ok = confirm_dialog(
            self,
            "Reset Password",
            f"Reset password for '{user['username']}' to default (Horizon@123)?",
        )
        if not ok:
            return

        try:
            result = api.reset_user_password(user["user_id"])
            show_toast(self, result.get("message", "Password reset."), success=True)
        except Exception as e:
            error_dialog(self, str(e))

    def _toggle_active(self):
        user = self._get_selected_user()
        if not user:
            return

        action = "deactivate" if user["is_active"] else "activate"
        ok = confirm_dialog(
            self,
            f"{action.title()} User",
            f"Are you sure you want to {action} user '{user['username']}'?",
        )
        if not ok:
            return

        try:
            result = api.toggle_user_active(user["user_id"])
            show_toast(self, result.get("message", "Done."), success=True)
            self._load_users()
        except Exception as e:
            error_dialog(self, str(e))

    def _view_activity(self):
        user = self._get_selected_user()
        if not user:
            return

        try:
            activity = api.get_user_activity(user["user_id"])
            dlg = ActivityDialog(self, user, activity)
            dlg.exec()
        except Exception as e:
            error_dialog(self, str(e))


class ActivityDialog(QDialog):
    """Shows recent booking activity for a staff member."""

    def __init__(self, parent, user: dict, activity: list):
        super().__init__(parent)
        self.setWindowTitle(f"Activity — {user['full_name']}")
        self.setMinimumSize(800, 560)
        self.setStyleSheet(f"QDialog {{ background: {BG_CARD}; }}")
        self._build(user, activity)

    def _build(self, user: dict, activity: list):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QWidget()
        header.setObjectName("modalHeader")
        header.setStyleSheet(f"QWidget#modalHeader {{ background: {WHITE}; }}")
        hl = QVBoxLayout(header)
        hl.setContentsMargins(24, 20, 24, 16)
        hl.setSpacing(4)
        title_lbl = QLabel(f"{user['full_name']} — Activity Log")
        title_lbl.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 14pt; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        hl.addWidget(title_lbl)
        sub_lbl = QLabel(f"Role: {user['role'].title()} | Cinema: {user['cinema_name']}")
        sub_lbl.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 10pt; background: transparent; border: none;"
        )
        hl.addWidget(sub_lbl)
        root.addWidget(header)

        # Divider
        div = QWidget()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background: {BORDER};")
        root.addWidget(div)

        # Body
        body = QWidget()
        body.setObjectName("modalBody")
        body.setStyleSheet(f"QWidget#modalBody {{ background: {WHITE}; }}")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(24, 24, 24, 24)
        bl.setSpacing(12)

        table = QTableWidget()
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(40)
        table.setShowGrid(False)
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(
            ["Reference", "Customer", "Tickets", "Total", "Status", "Date"]
        )
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.setStyleSheet(
            f"QTableWidget {{ border: 1.5px solid {BORDER}; border-radius: 8px; }}"
            f"QHeaderView::section {{ border-right: 1px solid {BORDER}; border-bottom: 2px solid {BORDER}; }}"
        )
        table.setItemDelegate(_LeftPaddingDelegate(12, table))

        table.setRowCount(len(activity))
        for row, a in enumerate(activity):
            table.setItem(row, 0, QTableWidgetItem(a["booking_reference"]))
            table.setItem(row, 1, QTableWidgetItem(a["customer_name"]))
            table.setItem(row, 2, QTableWidgetItem(str(a["num_tickets"])))
            table.setItem(row, 3, QTableWidgetItem(f"\u00a3{a['total_cost']:.2f}"))
            table.setItem(row, 4, QTableWidgetItem(a["booking_status"].capitalize()))
            bdate = a.get("booking_date") or "\u2014"
            if bdate != "\u2014":
                bdate = bdate[:19].replace("T", " ")
            table.setItem(row, 5, QTableWidgetItem(bdate))

        bl.addWidget(table, 1)

        count = QLabel(f"{len(activity)} recent action(s)")
        count.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 9pt; font-weight: 500;")
        bl.addWidget(count)

        root.addWidget(body, 1)

        # Footer
        footer = QWidget()
        footer.setObjectName("modalFooter")
        footer.setStyleSheet(
            f"QWidget#modalFooter {{ background: {WHITE}; border-top: 1.5px solid {BORDER}; }}"
        )
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(24, 14, 24, 14)
        fl.addStretch()

        close_btn = secondary_button("Close")
        close_btn.setStyleSheet(
            f"QPushButton {{ background-color: {HERO_BG}; color: {WHITE}; border: none; "
            f"min-height: 34px; max-height: 34px; min-width: 100px; font-weight: 700; "
            f"border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: #2E2C28; }}"
        )
        close_btn.clicked.connect(self.reject)
        fl.addWidget(close_btn)

        root.addWidget(footer)
