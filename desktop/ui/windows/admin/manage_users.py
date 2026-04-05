"""
desktop/ui/windows/admin/manage_users.py
Admin view: staff user management — view, reset passwords, activity logs.
"""

from PyQt6.QtCore import Qt  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QLabel, QDialog, QFormLayout,
    QDialogButtonBox,
)

from desktop.ui.theme import (
    ACCENT, SUCCESS, DANGER, WHITE,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    heading_font, body_font, SPACING_SM, SPACING_MD, SPACING_LG,
)
from desktop.ui.widgets import (
    heading_label, primary_button, secondary_button, danger_button,
    separator, show_toast, error_dialog, confirm_dialog, Card,
    muted_label,
)
from desktop.api_client import api


class ManageUsersView(QWidget):

    def __init__(self):
        super().__init__()
        self._users = []
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        header = QHBoxLayout()
        header.addWidget(heading_label("Manage Users"))
        header.addStretch()

        # Filters
        lbl_cinema = QLabel("Cinema:")
        lbl_cinema.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        header.addWidget(lbl_cinema)
        self.cinema_filter = QComboBox()
        self.cinema_filter.setFixedWidth(220)
        self.cinema_filter.currentIndexChanged.connect(self._load_users)
        header.addWidget(self.cinema_filter)

        lbl_role = QLabel("Role:")
        lbl_role.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        header.addWidget(lbl_role)
        self.role_filter = QComboBox()
        self.role_filter.addItems(["All Roles", "booking_staff", "admin", "manager"])
        self.role_filter.setFixedWidth(150)
        self.role_filter.currentIndexChanged.connect(self._load_users)
        header.addWidget(self.role_filter)

        refresh_btn = secondary_button("Refresh")
        refresh_btn.clicked.connect(self._load_data)
        header.addWidget(refresh_btn)

        layout.addLayout(header)
        layout.addWidget(separator())

        # Users table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Username", "Full Name", "Email", "Role",
            "Cinema", "Status", "Last Login"
        ])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)

        # Action buttons
        btn_row = QHBoxLayout()

        reset_btn = primary_button("Reset Password")
        reset_btn.clicked.connect(self._reset_password)
        btn_row.addWidget(reset_btn)

        toggle_btn = danger_button("Toggle Active")
        toggle_btn.clicked.connect(self._toggle_active)
        btn_row.addWidget(toggle_btn)

        activity_btn = secondary_button("View Activity")
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
        self.setMinimumSize(700, 500)
        self._build(user, activity)

    def _build(self, user: dict, activity: list):
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING_MD)

        info = QLabel(
            f"Staff: {user['full_name']}  |  Username: {user['username']}  |  "
            f"Cinema: {user['cinema_name']}"
        )
        info.setFont(body_font(10))
        info.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent; padding: 4px;")
        layout.addWidget(info)

        table = QTableWidget()
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.verticalHeader().setVisible(False)
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Reference", "Customer", "Tickets", "Total", "Status", "Date"
        ])
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        table.setRowCount(len(activity))
        for row, a in enumerate(activity):
            table.setItem(row, 0, QTableWidgetItem(a["booking_reference"]))
            table.setItem(row, 1, QTableWidgetItem(a["customer_name"]))
            table.setItem(row, 2, QTableWidgetItem(str(a["num_tickets"])))
            table.setItem(row, 3, QTableWidgetItem(f"\u00a3{a['total_cost']:.2f}"))
            table.setItem(row, 4, QTableWidgetItem(a["booking_status"].capitalize()))
            bdate = (a.get("booking_date") or "\u2014")
            if bdate != "\u2014":
                bdate = bdate[:19].replace("T", " ")
            table.setItem(row, 5, QTableWidgetItem(bdate))

        layout.addWidget(table, 1)

        count = QLabel(f"{len(activity)} recent action(s)")
        count.setFont(body_font(9))
        count.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        layout.addWidget(count)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
