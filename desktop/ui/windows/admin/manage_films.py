# ============================================
# Author: Garima Adhikari
# Student ID: 24000896
# Last Edited: 2026-04-25
# ============================================

"""
desktop/ui/windows/admin/manage_films.py
implements the movie catalogue management interface for Administrators.
supports CRUD operations including adding new movie records, editing existing entries, and performing soft-deletions.
"""

import csv
import io

from PyQt6.QtCore import Qt  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from desktop.api_client import api
from desktop.ui.theme import (
    ACCENT,
    ACCENT_HOVER,
    BG_INPUT,
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
    error_dialog,
    heading_label,
    muted_label,
    primary_button,
    secondary_button,
    show_toast,
)

GENRES = [
    "Action",
    "Animation",
    "Comedy",
    "Documentary",
    "Drama",
    "Family",
    "Horror",
    "Romance",
    "Sci-Fi",
    "Thriller",
]

AGE_RATINGS = ["U", "PG", "12A", "15", "18"]

_CERT_COLORS = {
    "U": ("#10B981", "#fff"),
    "PG": ("#F59E0B", "#fff"),
    "12A": ("#F59E0B", "#fff"),
    "15": ("#EF4444", "#fff"),
    "18": ("#0A0908", "#fff"),
}

_POSTER_PALETTE = ["#0A0908", "#2E2C28", "#4A4844", "#6E6C68", "#B91C1C", "#1A1814"]


def _poster_color(title: str) -> str:
    """generates a consistent background color for film posters based on the title string."""
    h = 0
    for ch in title:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return _POSTER_PALETTE[h % len(_POSTER_PALETTE)]


def _poster_widget(title: str) -> QLabel:
    """creates a stylized placeholder widget representing a film poster with initials."""
    letters = "".join(w[0] for w in title.split()[:2]).upper() or "?"
    lbl = QLabel(letters)
    lbl.setObjectName("filmPoster")
    lbl.setFixedSize(32, 44)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet(
        f"QLabel#filmPoster {{ background: {_poster_color(title)}; color: #fff; "
        f"border-radius: 4px; font-weight: 800; font-size: 10pt; border: none; "
        f"min-height: 0px; max-height: 44px; min-width: 32px; max-width: 32px; }}"
    )
    return lbl


def _cert_label(cert: str) -> QLabel:
    """creates a colored label representing the film's age rating certificate."""
    bg, fg = _CERT_COLORS.get(cert, ("#E4E3E0", TEXT_PRIMARY))
    lbl = QLabel(cert or "?")
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setFixedHeight(22)
    lbl.setMinimumWidth(32)
    lbl.setStyleSheet(
        f"background: {bg}; color: {fg}; border-radius: 4px; border: none; "
        f"font-size: 10pt; font-weight: 800; padding: 0 6px;"
    )
    return lbl


def _status_label(is_active: bool) -> QLabel:
    """creates a pill-style status label indicating if a film is Active or Inactive."""
    if is_active:
        text, bg, fg = "Active", "#D1FAE5", "#065F46"
    else:
        text, bg, fg = "Inactive", "#F3F4F6", "#6E6C68"
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setFixedHeight(22)
    lbl.setStyleSheet(
        f"background: {bg}; color: {fg}; border-radius: 10px; border: none; "
        f"font-size: 10pt; font-weight: 600; padding: 0 10px;"
    )
    return lbl


def _centered(widget: QWidget) -> QWidget:
    """wraps a widget in a centered layout for consistent table cell alignment."""
    wrap = QWidget()
    wrap.setStyleSheet("background: transparent;")
    lay = QHBoxLayout(wrap)
    lay.setContentsMargins(8, 0, 8, 0)
    lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lay.addWidget(widget)
    return wrap


class ManageFilmsView(QWidget):
    """a view for managing the cinema's film catalogue, including filtering and export functionality."""

    def __init__(self):
        """initialises the film management view and loads the movie catalogue."""
        super().__init__()
        self._all_films: list[dict] = []
        self._build_ui()
        self._load_films()

    def _build_ui(self):
        """constructs the primary interface including headers, filter controls, and the films table."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(0)

        # header section with view title and catalogue description
        header_content = QVBoxLayout()
        header_content.setSpacing(4)
        header_content.addWidget(heading_label("Manage Films"))
        desc = muted_label(
            "Central database for movie titles, genres, ratings, and cinematic assets"
        )
        header_content.addWidget(desc)

        title_row = QHBoxLayout()
        title_row.setSpacing(12)
        title_row.addLayout(header_content)
        title_row.addStretch()

        export_btn = secondary_button("Export CSV")
        export_btn.setStyleSheet(
            f"QPushButton {{ background-color: {HERO_BG}; color: {WHITE}; border: none; "
            f"min-height: 34px; max-height: 34px; min-width: 120px; font-weight: 700; "
            f"border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: #2E2C28; }}"
        )
        export_btn.clicked.connect(self._export_csv)
        title_row.addWidget(export_btn)

        add_btn = primary_button("+ Add Film")
        add_btn.setStyleSheet(
            f"QPushButton {{ background-color: {ACCENT}; color: {WHITE}; border: none; "
            f"min-height: 34px; max-height: 34px; min-width: 130px; font-weight: 700; "
            f"border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}"
        )
        add_btn.clicked.connect(self._add_film)
        title_row.addWidget(add_btn)

        layout.addLayout(title_row)
        layout.addSpacing(4)

        self.subtitle_lbl = QLabel("Loading films…")
        self.subtitle_lbl.setStyleSheet(
            f"color: {TEXT_MUTED}; background: transparent; font-size: 10pt;"
        )
        layout.addWidget(self.subtitle_lbl)
        layout.addSpacing(SPACING_MD)

        # filter row grouping search input and category selectors
        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by title…")
        self.search_input.setFixedHeight(32)
        self.search_input.setMinimumWidth(200)
        self.search_input.setStyleSheet(
            f"QLineEdit {{ background: {WHITE}; border: 1.5px solid {BORDER}; "
            f"border-radius: 8px; padding: 2px 10px; font-size: 10pt; color: {TEXT_PRIMARY}; }}"
            f"QLineEdit:focus {{ border-color: {ACCENT}; }}"
        )
        self.search_input.textChanged.connect(self._apply_filters)
        filter_row.addWidget(self.search_input)

        status_lbl = QLabel("Status:")
        status_lbl.setStyleSheet(
            f"color: {TEXT_SECONDARY}; background: transparent; font-size: 10pt; font-weight: 600;"
        )
        filter_row.addWidget(status_lbl)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["All", "Active", "Inactive"])
        self.status_combo.setFixedHeight(32)
        self.status_combo.setStyleSheet(self._combo_style())
        self.status_combo.currentTextChanged.connect(self._apply_filters)
        filter_row.addWidget(self.status_combo)

        genre_lbl = QLabel("Genre:")
        genre_lbl.setStyleSheet(
            f"color: {TEXT_SECONDARY}; background: transparent; font-size: 10pt; font-weight: 600;"
        )
        filter_row.addWidget(genre_lbl)

        self.genre_filter = QComboBox()
        self.genre_filter.addItems(["All"] + GENRES)
        self.genre_filter.setFixedHeight(32)
        self.genre_filter.setStyleSheet(self._combo_style())
        self.genre_filter.currentTextChanged.connect(self._apply_filters)
        filter_row.addWidget(self.genre_filter)

        filter_row.addStretch()

        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet(
            f"color: {TEXT_MUTED}; background: transparent; font-size: 10pt;"
        )
        filter_row.addWidget(self.count_lbl)

        layout.addLayout(filter_row)
        layout.addSpacing(SPACING_MD)

        # films catalogue table displaying detailed movie metadata
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(54)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setStyleSheet(
            f"QTableWidget {{ border: 1.5px solid {BORDER}; border-radius: 8px; }}"
            f"QHeaderView::section {{ border-bottom: 1.5px solid {BORDER}; "
            f"border-right: 1px solid {BORDER}; }}"
        )
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Title", "Rating", "Genre", "Release", "IMDb", "Status", ""]
        )
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col, w in enumerate([0, 90, 130, 130, 90, 130, 190], start=0):
            if col > 0:
                hh.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
                self.table.setColumnWidth(col, w)

        layout.addWidget(self.table, 1)

    def _combo_style(self) -> str:
        """returns the common QSS styling for combo box filters."""
        return (
            f"QComboBox {{ background: {WHITE}; border: 1.5px solid {BORDER}; "
            f"border-radius: 8px; padding: 2px 10px; font-size: 10pt; color: {TEXT_PRIMARY}; }}"
            f"QComboBox:focus {{ border-color: {ACCENT}; }}"
            f"QComboBox::drop-down {{ border: none; width: 24px; }}"
        )

    def _load_films(self):
        """fetches the complete film catalogue from the api and applies current filters."""
        try:
            self._all_films = api.get_films(active_only=False)
            self._apply_filters()
        except Exception as e:
            error_dialog(self, f"Failed to load films: {e}")

    def _apply_filters(self):
        """filters the film list based on search keywords, status, and genre selections."""
        search = self.search_input.text().strip().lower()
        status_f = self.status_combo.currentText()
        genre_f = self.genre_filter.currentText()

        filtered = []
        for f in self._all_films:
            if search and search not in f["title"].lower():
                continue
            if status_f == "Active" and not f["is_active"]:
                continue
            if status_f == "Inactive" and f["is_active"]:
                continue
            if genre_f != "All" and f.get("genre") != genre_f:
                continue
            filtered.append(f)

        total = len(self._all_films)
        active_count = sum(1 for f in self._all_films if f["is_active"])
        self.subtitle_lbl.setText(f"{total} films in catalogue · {active_count} active")
        self.count_lbl.setText(f"{len(filtered)} of {total}")
        self._populate_table(filtered)

    def _populate_table(self, films: list[dict]):
        """populates the QTableWidget with movie records and interactive action buttons."""
        self.table.setRowCount(len(films))

        for row, f in enumerate(films):
            title_w = QWidget()
            title_w.setStyleSheet("background: transparent;")
            tl = QHBoxLayout(title_w)
            tl.setContentsMargins(8, 4, 8, 4)
            tl.setSpacing(10)
            tl.addWidget(_poster_widget(f["title"]), 0, Qt.AlignmentFlag.AlignVCenter)
            name_col = QVBoxLayout()
            name_col.setSpacing(2)
            name_lbl = QLabel(f["title"])
            name_lbl.setStyleSheet(
                f"color: {TEXT_PRIMARY}; font-weight: 700; font-size: 10pt; "
                f"background: transparent; border: none;"
            )
            name_col.addWidget(name_lbl)
            dur_lbl = QLabel(f"{f.get('duration_mins', '?')} min")
            dur_lbl.setStyleSheet(
                f"color: {TEXT_MUTED}; font-size: 9pt; background: transparent; border: none;"
            )
            name_col.addWidget(dur_lbl)
            tl.addLayout(name_col, 1)
            self.table.setCellWidget(row, 0, title_w)

            self.table.setCellWidget(row, 1, _centered(_cert_label(f.get("age_rating", ""))))

            genre_item = QTableWidgetItem(f.get("genre", ""))
            genre_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 2, genre_item)

            release_item = QTableWidgetItem(str(f.get("release_date", "") or "—"))
            release_item.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(row, 3, release_item)

            imdb = f.get("imdb_rating")
            imdb_item = QTableWidgetItem(f"{imdb:.1f}" if imdb else "—")
            imdb_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 4, imdb_item)

            self.table.setCellWidget(row, 5, _centered(_status_label(f["is_active"])))

            actions_w = QWidget()
            actions_w.setStyleSheet("background: transparent;")
            al = QHBoxLayout(actions_w)
            al.setContentsMargins(8, 8, 8, 8)
            al.setSpacing(6)

            edit_btn = QPushButton("Edit")
            edit_btn.setFixedHeight(28)
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.setStyleSheet(
                f"QPushButton {{ background-color: {HERO_BG}; color: {WHITE}; border: none; "
                f"border-radius: 6px; padding: 0 12px; font-size: 9pt; font-weight: 700; "
                f"min-height: 28px; max-height: 28px; }}"
                f"QPushButton:hover {{ background-color: #2E2C28; }}"
            )
            film_snap = dict(f)
            edit_btn.clicked.connect(lambda checked, fd=film_snap: self._edit_film(fd))
            al.addWidget(edit_btn)

            remove_btn = QPushButton("Remove")
            remove_btn.setFixedHeight(28)
            remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            remove_btn.setStyleSheet(
                f"QPushButton {{ background-color: transparent; color: {DANGER}; "
                f"border: 1.5px solid {DANGER}; border-radius: 6px; padding: 0 12px; "
                f"font-size: 9pt; font-weight: 700; min-height: 28px; max-height: 28px; }}"
                f"QPushButton:hover {{ background-color: #FEF2F2; }}"
            )
            fid = f["film_id"]
            remove_btn.clicked.connect(lambda checked, fid=fid: self._delete_film(fid))
            al.addWidget(remove_btn)

            self.table.setCellWidget(row, 6, actions_w)

    def _export_csv(self):
        """exports the current film catalogue metadata to a CSV file."""
        if not self._all_films:
            error_dialog(self, "No films to export. Load the catalogue first.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Export Films CSV", "HCBS_Films.csv", "CSV Files (*.csv)"
        )
        if not path:
            return

        try:
            out = io.StringIO()
            writer = csv.writer(out)
            writer.writerow(
                [
                    "ID",
                    "Title",
                    "Age Rating",
                    "Genre",
                    "Duration (min)",
                    "Release Date",
                    "Director",
                    "IMDb Rating",
                    "Status",
                ]
            )
            for f in self._all_films:
                writer.writerow(
                    [
                        f.get("film_id", ""),
                        f.get("title", ""),
                        f.get("age_rating", ""),
                        f.get("genre", ""),
                        f.get("duration_mins", ""),
                        f.get("release_date", ""),
                        f.get("director", ""),
                        f.get("imdb_rating", ""),
                        "Active" if f.get("is_active") else "Inactive",
                    ]
                )
            with open(path, "w", newline="", encoding="utf-8") as fh:
                fh.write(out.getvalue())
            show_toast(self, f"Exported {len(self._all_films)} films to CSV.")
        except Exception as e:
            error_dialog(self, f"Export failed: {e}")

    def _add_film(self):
        """opens a dialog to create a new movie record in the catalogue."""
        dlg = FilmDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                api.create_film(dlg.get_data())
                show_toast(self, "Film added successfully.")
                self._load_films()
            except Exception as e:
                error_dialog(self, str(e))

    def _edit_film(self, film_data: dict):
        """opens a dialog to modify an existing film record."""
        dlg = FilmDialog(self, film_data)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                api.update_film(film_data["film_id"], dlg.get_data())
                show_toast(self, "Film updated.")
                self._load_films()
            except Exception as e:
                error_dialog(self, str(e))

    def _delete_film(self, film_id: int):
        """processes a request to deactivate a film from the catalogue."""
        if confirm_dialog(self, "Remove Film", "This will deactivate the film. Continue?"):
            try:
                api.delete_film(film_id)
                show_toast(self, "Film removed.")
                self._load_films()
            except Exception as e:
                error_dialog(self, str(e))


class FilmDialog(QDialog):
    """a specialized modal dialog for adding or editing film catalogue entries."""

    def __init__(self, parent, data: dict = None):
        """initialises the film form dialog, supporting both create and edit modes."""
        super().__init__(parent)
        self._data = data or {}
        self._is_edit = bool(data)
        self.setWindowTitle("Edit film" if self._is_edit else "Add film")
        self.setMinimumWidth(600)
        self.setModal(True)
        self._build()

    def _build(self):
        """constructs the multi-column form layout for film metadata input."""
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QWidget()
        header.setObjectName("modalHeader")
        header.setStyleSheet(f"QWidget#modalHeader {{ background: {WHITE}; }}")
        hl = QVBoxLayout(header)
        hl.setContentsMargins(24, 20, 24, 16)
        hl.setSpacing(4)
        title_lbl = QLabel("Edit film" if self._is_edit else "Add film")
        title_lbl.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 15pt; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        hl.addWidget(title_lbl)
        sub_text = (
            f'Editing "{self._data.get("title", "")}"'
            if self._is_edit
            else "Add a new film to the catalogue"
        )
        sub_lbl = QLabel(sub_text)
        sub_lbl.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 10pt; background: transparent; border: none;"
        )
        hl.addWidget(sub_lbl)
        root.addWidget(header)

        body = QWidget()
        body.setObjectName("modalBody")
        body.setStyleSheet(f"QWidget#modalBody {{ background: {WHITE}; }}")
        grid = QGridLayout(body)
        grid.setContentsMargins(24, 20, 24, 20)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(4)

        r = 0

        grid.addWidget(self._lbl("Title *"), r, 0, 1, 2)
        r += 1
        self.title_input = self._line("e.g. The Quiet Horizon", self._data.get("title", ""))
        grid.addWidget(self.title_input, r, 0, 1, 2)
        r += 1

        grid.addLayout(self._vspace(10), r, 0, 1, 2)
        r += 1

        grid.addWidget(self._lbl("Certificate *"), r, 0)
        grid.addWidget(self._lbl("Genre *"), r, 1)
        r += 1
        self.cert_combo = self._combo(AGE_RATINGS, self._data.get("age_rating", ""))
        self.genre_combo = self._combo(GENRES, self._data.get("genre", ""))
        grid.addWidget(self.cert_combo, r, 0)
        grid.addWidget(self.genre_combo, r, 1)
        r += 1

        grid.addLayout(self._vspace(10), r, 0, 1, 2)
        r += 1

        grid.addWidget(self._lbl("Runtime (min) *"), r, 0)
        grid.addWidget(self._lbl("Director"), r, 1)
        r += 1
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 600)
        self.duration_spin.setValue(self._data.get("duration_mins", 120))
        self.duration_spin.setFixedHeight(36)
        self.duration_spin.setStyleSheet(self._spin_style())
        self.director_input = self._line("Director name", self._data.get("director", "") or "")
        grid.addWidget(self.duration_spin, r, 0)
        grid.addWidget(self.director_input, r, 1)
        r += 1

        grid.addLayout(self._vspace(10), r, 0, 1, 2)
        r += 1

        grid.addWidget(self._lbl("Release date"), r, 0)
        grid.addWidget(self._lbl("IMDb Rating"), r, 1)
        r += 1
        self.release_input = self._line("YYYY-MM-DD", str(self._data.get("release_date", "") or ""))
        self.imdb_spin = QDoubleSpinBox()
        self.imdb_spin.setRange(0, 10)
        self.imdb_spin.setDecimals(1)
        self.imdb_spin.setValue(float(self._data.get("imdb_rating", 0) or 0))
        self.imdb_spin.setFixedHeight(36)
        self.imdb_spin.setStyleSheet(self._spin_style())
        grid.addWidget(self.release_input, r, 0)
        grid.addWidget(self.imdb_spin, r, 1)
        r += 1

        grid.addLayout(self._vspace(10), r, 0, 1, 2)
        r += 1

        grid.addWidget(self._lbl("Synopsis"), r, 0, 1, 2)
        r += 1
        self.desc_input = QTextEdit()
        self.desc_input.setPlainText(self._data.get("description", "") or "")
        self.desc_input.setPlaceholderText("A short synopsis to display on the booking screen…")
        self.desc_input.setFixedHeight(80)
        self.desc_input.setStyleSheet(
            f"QTextEdit {{ background: {BG_INPUT}; border: 1.5px solid {BORDER}; "
            f"border-radius: 8px; padding: 8px 10px; font-size: 10pt; color: {TEXT_PRIMARY}; }}"
            f"QTextEdit:focus {{ border-color: {ACCENT}; background: {WHITE}; }}"
        )
        grid.addWidget(self.desc_input, r, 0, 1, 2)

        root.addWidget(body)

        footer = QWidget()
        footer.setObjectName("modalFooter")
        footer.setStyleSheet(
            f"QWidget#modalFooter {{ background: {WHITE}; border-top: 1.5px solid {BORDER}; }}"
        )
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(24, 14, 24, 14)
        fl.setSpacing(10)
        fl.addStretch()

        cancel_btn = secondary_button("Cancel")
        cancel_btn.setStyleSheet(
            f"QPushButton {{ background-color: {HERO_BG}; color: {WHITE}; border: none; "
            f"min-height: 34px; max-height: 34px; min-width: 100px; font-weight: 700; "
            f"border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: #2E2C28; }}"
        )
        cancel_btn.clicked.connect(self.reject)
        fl.addWidget(cancel_btn)

        save_btn = primary_button("Save changes" if self._is_edit else "Add film")
        save_btn.setStyleSheet(
            f"QPushButton {{ background-color: {ACCENT}; color: {WHITE}; border: none; "
            f"min-height: 34px; max-height: 34px; min-width: 130px; font-weight: 700; "
            f"border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}"
        )
        save_btn.clicked.connect(self.accept)
        fl.addWidget(save_btn)

        root.addWidget(footer)

    def _lbl(self, text: str) -> QLabel:
        """helper to create consistently styled form labels."""
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 10pt; font-weight: 600; "
            f"background: transparent; border: none;"
        )
        return lbl

    def _line(self, placeholder: str = "", value: str = "") -> QLineEdit:
        """helper to create styled text input fields."""
        inp = QLineEdit(value)
        inp.setPlaceholderText(placeholder)
        inp.setFixedHeight(36)
        inp.setStyleSheet(
            f"QLineEdit {{ background: {BG_INPUT}; border: 1.5px solid {BORDER}; "
            f"border-radius: 8px; padding: 4px 10px; font-size: 10pt; color: {TEXT_PRIMARY}; }}"
            f"QLineEdit:focus {{ border-color: {ACCENT}; background: {WHITE}; }}"
        )
        return inp

    def _combo(self, options: list, current: str = "") -> QComboBox:
        """helper to create styled dropdown selectors."""
        cb = QComboBox()
        cb.addItems(options)
        cb.setFixedHeight(36)
        cb.setStyleSheet(
            f"QComboBox {{ background: {BG_INPUT}; border: 1.5px solid {BORDER}; "
            f"border-radius: 8px; padding: 4px 10px; font-size: 10pt; color: {TEXT_PRIMARY}; }}"
            f"QComboBox:focus {{ border-color: {ACCENT}; background: {WHITE}; }}"
            f"QComboBox::drop-down {{ border: none; width: 24px; }}"
        )
        if current:
            idx = cb.findText(current)
            if idx >= 0:
                cb.setCurrentIndex(idx)
        return cb

    def _spin_style(self) -> str:
        """returns the common QSS styling for numerical spin box inputs."""
        return (
            f"QSpinBox, QDoubleSpinBox {{ background: {BG_INPUT}; border: 1.5px solid {BORDER}; "
            f"border-radius: 8px; padding: 4px 10px; font-size: 10pt; color: {TEXT_PRIMARY}; }}"
            f"QSpinBox:focus, QDoubleSpinBox:focus {{ border-color: {ACCENT}; background: {WHITE}; }}"
        )

    @staticmethod
    def _vspace(px: int):
        """helper to create vertical spacing within the grid layout."""
        spacer = QVBoxLayout()
        spacer.addSpacing(px)
        return spacer

    def get_data(self) -> dict:
        """compiles and returns the validated form data as a dictionary."""
        d = {
            "title": self.title_input.text().strip(),
            "age_rating": self.cert_combo.currentText(),
            "genre": self.genre_combo.currentText(),
            "duration_mins": self.duration_spin.value(),
            "director": self.director_input.text().strip() or None,
            "description": self.desc_input.toPlainText().strip() or None,
        }
        release = self.release_input.text().strip()
        if release:
            d["release_date"] = release
        imdb = self.imdb_spin.value()
        if imdb > 0:
            d["imdb_rating"] = imdb
        return d
