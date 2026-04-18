"""
desktop/ui/windows/admin/manage_listings.py
Admin view: listing management — assign films to screens with showings.
"""

from PyQt6.QtCore import QDate, QTime  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from desktop.api_client import api
from desktop.ui.theme import SPACING_LG, SPACING_MD
from desktop.ui.widgets import (
    confirm_dialog,
    danger_button,
    error_dialog,
    heading_label,
    primary_button,
    secondary_button,
    separator,
    show_toast,
)


class ManageListingsView(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        header = QHBoxLayout()
        header.addWidget(heading_label("Manage Listings"))
        header.addStretch()

        self.cinema_filter = QComboBox()
        self.cinema_filter.setFixedWidth(260)
        self.cinema_filter.currentIndexChanged.connect(self._load_listings)
        header.addWidget(QLabel("Cinema:"))
        header.addWidget(self.cinema_filter)

        add_btn = primary_button("+ New Listing")
        add_btn.clicked.connect(self._add_listing)
        header.addWidget(add_btn)

        layout.addLayout(header)
        layout.addWidget(separator())

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Film", "Screen", "Start", "End", "Showings", "Status"]
        )
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)

        btn_row = QHBoxLayout()
        del_btn = danger_button("Remove Selected")
        del_btn.clicked.connect(self._delete_listing)
        btn_row.addWidget(del_btn)

        refresh_btn = secondary_button("Refresh")
        refresh_btn.clicked.connect(self._load_data)
        btn_row.addWidget(refresh_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _load_data(self):
        try:
            cinemas = api.get_cinemas()
            self.cinema_filter.blockSignals(True)
            self.cinema_filter.clear()
            self.cinema_filter.addItem("All Cinemas", None)
            for c in cinemas:
                self.cinema_filter.addItem(
                    f"{c['cinema_name']}  ({c.get('city_name', '')})", c["cinema_id"]
                )
            self.cinema_filter.blockSignals(False)
            self._load_listings()
        except Exception as e:
            error_dialog(self, str(e))

    def _load_listings(self):
        try:
            cinema_id = self.cinema_filter.currentData()
            if cinema_id:
                listings = api.get(f"/films/listings/cinema/{cinema_id}")
            else:
                listings = api.get_all_listings()

            self.table.setRowCount(len(listings))
            for row, listing in enumerate(listings):
                self.table.setItem(row, 0, QTableWidgetItem(str(listing["listing_id"])))
                self.table.setItem(row, 1, QTableWidgetItem(listing.get("film_title", "")))
                self.table.setItem(
                    row,
                    2,
                    QTableWidgetItem(
                        f"Screen {listing.get('screen_number', '?')} @ "
                        f"{listing.get('cinema_name', '')}"
                    ),
                )
                self.table.setItem(row, 3, QTableWidgetItem(str(listing["start_date"])))
                self.table.setItem(row, 4, QTableWidgetItem(str(listing["end_date"])))

                showings = listing.get("showings", [])
                times = ", ".join(str(s.get("show_time", ""))[:5] for s in showings)
                self.table.setItem(row, 5, QTableWidgetItem(times or "—"))

                status = "Active" if listing["is_active"] else "Removed"
                self.table.setItem(row, 6, QTableWidgetItem(status))

        except Exception as e:
            error_dialog(self, str(e))

    def _add_listing(self):
        dlg = ListingDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                api.create_listing(dlg.get_data())
                show_toast(self, "Listing created.")
                self._load_listings()
            except Exception as e:
                detail = str(e)
                if hasattr(e, "response"):
                    try:
                        detail = e.response.json().get("detail", detail)
                    except Exception:
                        pass
                error_dialog(self, detail)

    def _delete_listing(self):
        row = self.table.currentRow()
        if row < 0:
            error_dialog(self, "Select a listing first.")
            return
        lid = int(self.table.item(row, 0).text())
        if confirm_dialog(self, "Remove Listing", "Deactivate this listing and its showings?"):
            try:
                api.delete_listing(lid)
                show_toast(self, "Listing removed.")
                self._load_listings()
            except Exception as e:
                error_dialog(self, str(e))


class ListingDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("New Listing")
        self.setMinimumWidth(500)
        self._showings = []
        self._build()
        self._load_data()

    def _build(self):
        self.form = QFormLayout(self)

        self.film_combo = QComboBox()
        self.form.addRow("Film:", self.film_combo)

        self.cinema_combo = QComboBox()
        self.cinema_combo.currentIndexChanged.connect(self._on_cinema_changed)
        self.form.addRow("Cinema:", self.cinema_combo)

        self.screen_combo = QComboBox()
        self.form.addRow("Screen:", self.screen_combo)

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        self.form.addRow("Start Date:", self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate().addDays(14))
        self.form.addRow("End Date:", self.end_date)

        # Showings section
        self.form.addRow(separator())
        self.form.addRow(QLabel("Showings (1-3):"))

        self.showings_layout = QVBoxLayout()
        self._add_showing_row()
        self.form.addRow(self.showings_layout)

        add_showing_btn = QPushButton("+ Add Showing")
        add_showing_btn.clicked.connect(self._add_showing_row)
        self.form.addRow(add_showing_btn)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.form.addRow(buttons)

    def _add_showing_row(self):
        if len(self._showings) >= 3:
            return
        row = QHBoxLayout()
        time_edit = QTimeEdit()
        time_edit.setDisplayFormat("HH:mm")
        time_edit.setTime(QTime(10, 0))

        type_combo = QComboBox()
        type_combo.addItems(["morning", "afternoon", "evening"])

        row.addWidget(QLabel("Time:"))
        row.addWidget(time_edit)
        row.addWidget(QLabel("Type:"))
        row.addWidget(type_combo)

        self._showings.append((time_edit, type_combo))
        self.showings_layout.addLayout(row)

    def _load_data(self):
        try:
            films = api.get_films()
            for f in films:
                self.film_combo.addItem(f["title"], f["film_id"])

            cinemas = api.get_cinemas()
            for c in cinemas:
                self.cinema_combo.addItem(f"{c['cinema_name']}  ({c.get('city_name', '')})", c)
        except Exception:
            pass

    def _on_cinema_changed(self):
        self.screen_combo.clear()
        cinema_data = self.cinema_combo.currentData()
        if not cinema_data:
            return
        for s in cinema_data.get("screens", []):
            if s["is_active"]:
                self.screen_combo.addItem(
                    f"Screen {s['screen_number']}  ({s['total_seats']} seats)",
                    s["screen_id"],
                )

    def get_data(self) -> dict:
        showings = []
        for time_edit, type_combo in self._showings:
            showings.append(
                {
                    "show_time": time_edit.time().toString("HH:mm:ss"),
                    "show_type": type_combo.currentText(),
                }
            )
        return {
            "film_id": self.film_combo.currentData(),
            "screen_id": self.screen_combo.currentData(),
            "start_date": self.start_date.date().toPyDate().isoformat(),
            "end_date": self.end_date.date().toPyDate().isoformat(),
            "showings": showings,
        }
