"""
desktop/ui/windows/admin/manage_films.py
Admin view: film catalogue CRUD — add, edit, soft-delete films.
"""

from PyQt6.QtCore import Qt, QDate # type: ignore
from PyQt6.QtWidgets import ( # type: ignore
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QLineEdit, QComboBox, QSpinBox, QDateEdit,
    QDoubleSpinBox, QTextEdit, QFormLayout, QDialogButtonBox,
)

from desktop.ui.theme import (
    ACCENT, CHARCOAL, SMOKE, SPACING_MD, SPACING_LG,
    heading_font, body_font,
)
from desktop.ui.widgets import (
    heading_label, primary_button, secondary_button, danger_button,
    separator, show_toast, error_dialog, confirm_dialog,
)
from desktop.api_client import api

GENRES = ["Action", "Comedy", "Drama", "Horror", "Sci-Fi", "Romance",
          "Thriller", "Animation", "Documentary"]


class ManageFilmsView(QWidget):

    def __init__(self):
        super().__init__()
        self._build_ui()
        self._load_films()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        header = QHBoxLayout()
        header.addWidget(heading_label("Manage Films"))
        header.addStretch()

        add_btn = primary_button("+ Add Film")
        add_btn.clicked.connect(self._add_film)
        header.addWidget(add_btn)

        refresh_btn = secondary_button("Refresh")
        refresh_btn.clicked.connect(self._load_films)
        header.addWidget(refresh_btn)

        layout.addLayout(header)
        layout.addWidget(separator())

        # Table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Title", "Genre", "Rating", "Duration", "Release", "IMDb", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)

        # Action buttons
        btn_row = QHBoxLayout()
        edit_btn = secondary_button("Edit Selected")
        edit_btn.clicked.connect(self._edit_film)
        btn_row.addWidget(edit_btn)

        del_btn = danger_button("Remove Selected")
        del_btn.clicked.connect(self._delete_film)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _load_films(self):
        try:
            films = api.get_films(active_only=False)
            self.table.setRowCount(len(films))
            for row, f in enumerate(films):
                self.table.setItem(row, 0, QTableWidgetItem(str(f["film_id"])))
                self.table.setItem(row, 1, QTableWidgetItem(f["title"]))
                self.table.setItem(row, 2, QTableWidgetItem(f["genre"]))
                self.table.setItem(row, 3, QTableWidgetItem(f["age_rating"]))
                self.table.setItem(row, 4, QTableWidgetItem(f"{f['duration_mins']} min"))
                self.table.setItem(row, 5, QTableWidgetItem(str(f.get("release_date", ""))))
                self.table.setItem(row, 6, QTableWidgetItem(str(f.get("imdb_rating", ""))))
                status = "Active" if f["is_active"] else "Removed"
                self.table.setItem(row, 7, QTableWidgetItem(status))
        except Exception as e:
            error_dialog(self, f"Failed to load films: {e}")

    def _get_selected_film_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            error_dialog(self, "Please select a film first.")
            return None
        return int(self.table.item(row, 0).text())

    def _add_film(self):
        dlg = FilmDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                api.create_film(dlg.get_data())
                show_toast(self, "Film added successfully.")
                self._load_films()
            except Exception as e:
                error_dialog(self, str(e))

    def _edit_film(self):
        film_id = self._get_selected_film_id()
        if not film_id:
            return
        row = self.table.currentRow()
        current = {
            "title": self.table.item(row, 1).text(),
            "genre": self.table.item(row, 2).text(),
            "age_rating": self.table.item(row, 3).text(),
            "duration_mins": int(self.table.item(row, 4).text().replace(" min", "")),
        }
        dlg = FilmDialog(self, current)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                api.update_film(film_id, dlg.get_data())
                show_toast(self, "Film updated.")
                self._load_films()
            except Exception as e:
                error_dialog(self, str(e))

    def _delete_film(self):
        film_id = self._get_selected_film_id()
        if not film_id:
            return
        if confirm_dialog(self, "Remove Film", "This will deactivate the film. Continue?"):
            try:
                api.delete_film(film_id)
                show_toast(self, "Film removed.")
                self._load_films()
            except Exception as e:
                error_dialog(self, str(e))


class FilmDialog(QDialog):
    """Add / Edit film dialog."""

    def __init__(self, parent, data: dict = None):
        super().__init__(parent)
        self.setWindowTitle("Edit Film" if data else "Add Film")
        self.setMinimumWidth(480)
        self._data = data or {}
        self._build()

    def _build(self):
        form = QFormLayout(self)

        self.title_input = QLineEdit(self._data.get("title", ""))
        form.addRow("Title:", self.title_input)

        self.genre_combo = QComboBox()
        self.genre_combo.addItems(GENRES)
        if self._data.get("genre"):
            idx = self.genre_combo.findText(self._data["genre"])
            if idx >= 0:
                self.genre_combo.setCurrentIndex(idx)
        form.addRow("Genre:", self.genre_combo)

        self.rating_input = QLineEdit(self._data.get("age_rating", ""))
        self.rating_input.setPlaceholderText("PG, PG-13, 15, 18, U")
        form.addRow("Age Rating:", self.rating_input)

        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 600)
        self.duration_spin.setValue(self._data.get("duration_mins", 120))
        self.duration_spin.setSuffix(" min")
        form.addRow("Duration:", self.duration_spin)

        self.director_input = QLineEdit(self._data.get("director", ""))
        form.addRow("Director:", self.director_input)

        self.cast_input = QLineEdit(self._data.get("cast_list", ""))
        self.cast_input.setPlaceholderText("Comma-separated")
        form.addRow("Cast:", self.cast_input)

        self.desc_input = QTextEdit()
        self.desc_input.setPlainText(self._data.get("description", ""))
        self.desc_input.setMaximumHeight(100)
        form.addRow("Description:", self.desc_input)

        self.imdb_spin = QDoubleSpinBox()
        self.imdb_spin.setRange(0, 10)
        self.imdb_spin.setDecimals(1)
        self.imdb_spin.setValue(self._data.get("imdb_rating", 0) or 0)
        form.addRow("IMDb Rating:", self.imdb_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def get_data(self) -> dict:
        d = {
            "title": self.title_input.text().strip(),
            "genre": self.genre_combo.currentText(),
            "age_rating": self.rating_input.text().strip(),
            "duration_mins": self.duration_spin.value(),
            "director": self.director_input.text().strip() or None,
            "cast_list": self.cast_input.text().strip() or None,
            "description": self.desc_input.toPlainText().strip() or None,
        }
        imdb = self.imdb_spin.value()
        if imdb > 0:
            d["imdb_rating"] = imdb
        return d