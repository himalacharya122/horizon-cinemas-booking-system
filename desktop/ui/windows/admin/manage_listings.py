# ============================================
# Author: Astha Gurung
# Student ID: 24036542
# Last Edited: 2026-04-25
# ============================================

"""
desktop/ui/windows/admin/manage_listings.py
implements the listing management interface for Administrators to coordinate film schedules
across cinema screens.
"""

from PyQt6.QtCore import QDate, Qt, QTime
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QScrollArea,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableWidget,
    QTableWidgetItem,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from desktop.api_client import api
from desktop.ui.theme import (
    ACCENT,
    ACCENT_HOVER,
    BG_CARD,
    BG_INPUT,
    BORDER,
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

    def __init__(self, padding: int = 8, parent=None):
        super().__init__(parent)
        self.padding = padding

    def paint(self, painter, option, index):
        padded = QStyleOptionViewItem(option)
        padded.rect.adjust(self.padding, 0, 0, 0)
        super().paint(painter, padded, index)


class ManageListingsView(QWidget):
    """a view for managing cinema film listings, allowing Administrators to schedule movie showings."""  # noqa: E501

    def __init__(self):
        """initialises the listings management view and loads current scheduling data."""
        super().__init__()
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        """
        constructs the primary interface including scheduling headers, cinema filters,
        and the listings table.
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        # header section with view title and scheduling description
        header_content = QVBoxLayout()
        header_content.setSpacing(4)
        header_content.addWidget(heading_label("Manage Listings"))
        desc = muted_label("Schedule movie showings, manage screens, and coordinate session times")
        header_content.addWidget(desc)

        header = QHBoxLayout()
        header.addLayout(header_content)
        header.addStretch()

        cinema_lbl = QLabel("Cinema:")
        cinema_lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        cinema_lbl.setFixedHeight(34)
        cinema_lbl.setStyleSheet(
            f"color: {TEXT_SECONDARY}; background: transparent; font-size: 10pt; font-weight: 600;"
        )
        self.cinema_filter = QComboBox()
        self.cinema_filter.setFixedWidth(260)
        self.cinema_filter.setFixedHeight(34)
        self.cinema_filter.currentIndexChanged.connect(self._load_listings)
        header.addWidget(cinema_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(self.cinema_filter, 0, Qt.AlignmentFlag.AlignVCenter)

        add_btn = primary_button("+ New Listing")
        add_btn.setStyleSheet(
            f"QPushButton {{ background-color: {ACCENT}; color: {WHITE}; border: none; "
            f"min-height: 30px; max-height: 30px; min-width: 130px; font-weight: 700; "
            f"border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}"
        )
        add_btn.clicked.connect(self._add_listing)
        header.addWidget(add_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        # title block grouping the header row and secondary description
        title_block = QVBoxLayout()
        title_block.setSpacing(3)
        title_block.addLayout(header)
        subtitle = QLabel("Assign films to screens and manage active showings")
        subtitle.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent; font-size: 10pt;")
        title_block.addWidget(subtitle)
        layout.addLayout(title_block)

        # listings table displaying detailed film schedule metadata
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(42)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Film", "Screen", "Start", "End", "Showings", "Status"]
        )
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 55)
        self.table.setColumnWidth(2, 260)
        self.table.setColumnWidth(3, 110)
        self.table.setColumnWidth(4, 110)
        self.table.setColumnWidth(5, 200)
        self.table.setColumnWidth(6, 100)
        self.table.setStyleSheet(
            f"QTableWidget {{ border: 1.5px solid {BORDER}; border-radius: 8px; }}"
            f"QHeaderView::section {{ border-right: 1px solid {BORDER}; border-bottom: 2.5px solid {BORDER}; }}"  # noqa: E501
            "QTableWidget::item:selected { background-color: #FEF2F2; color: #0A0908; }"
        )
        self.table.setItemDelegate(_LeftPaddingDelegate(8, self.table))
        layout.addWidget(self.table, 1)

        # control row featuring batch actions and refresh tools
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        del_btn = danger_button("Remove Selected")
        del_btn.setStyleSheet(
            "QPushButton { background: transparent; color: #EF4444; border: 1.5px solid #EF4444; "
            "border-radius: 8px; padding: 4px 16px; min-height: 34px; max-height: 34px; "
            "font-size: 10pt; font-weight: 700; }"
            "QPushButton:hover { background: #FEF2F2; }"
        )
        del_btn.clicked.connect(self._delete_listing)
        btn_row.addWidget(del_btn)

        refresh_btn = secondary_button("Refresh")
        refresh_btn.setStyleSheet(
            f"QPushButton {{ background-color: {HERO_BG}; color: {WHITE}; border: none; "
            f"min-height: 34px; max-height: 34px; min-width: 100px; font-weight: 700; "
            f"border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: #2E2C28; }}"
        )
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
        """retrieves and displays film listings based on the current cinema filter."""
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
        """opens a dialog to create a new film listing and showing schedule."""
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
        """processes a request to deactivate the selected film listing."""
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
    """a specialized modal dialog for configuring new film listing schedules."""

    def __init__(self, parent):
        """initialises the listing form, setting the default modal layout and size."""
        super().__init__(parent)
        self.setWindowTitle("New Listing")
        self.setMinimumSize(640, 640)
        self.setMaximumHeight(820)
        self.setStyleSheet(f"QDialog {{ background: {BG_CARD}; }}")
        self._showings = []
        self._build()
        self._load_data()

    def _build(self):
        """constructs the primary form layout including scrollable metadata sections."""
        # outer layout: fixed header, scrollable body, and fixed footer
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # header section for modal context and instructions
        header = QWidget()
        header.setObjectName("modalHeader")
        header.setStyleSheet(f"QWidget#modalHeader {{ background: {WHITE}; }}")
        hl = QVBoxLayout(header)
        hl.setContentsMargins(24, 20, 24, 16)
        hl.setSpacing(4)

        title_lbl = QLabel("New Listing")
        title_lbl.setStyleSheet(
            f"color: {TEXT_PRIMARY}; background: transparent; border: none; "
            "font-size: 14pt; font-weight: 700;"
        )
        hl.addWidget(title_lbl)

        sub_lbl = QLabel("Assign a film to a screen with up to 3 showings per day")
        sub_lbl.setStyleSheet(
            f"color: {TEXT_MUTED}; background: transparent; border: none; font-size: 10pt;"
        )
        hl.addWidget(sub_lbl)
        root.addWidget(header)

        # visual divider for header separation
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"background: {BORDER}; max-height: 1px; border: none;")
        root.addWidget(div)

        # scrollable body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
            f"QScrollBar:vertical {{ width: 6px; background: transparent; }}"
            f"QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 3px; }}"
        )

        body = QWidget()
        body.setObjectName("modalBody")
        body.setStyleSheet(f"QWidget#modalBody {{ background: {WHITE}; }}")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(24, 20, 24, 20)
        bl.setSpacing(20)

        _combo_style = f"QComboBox {{ border: 1.5px solid {BORDER}; border-radius: 8px; background: {BG_INPUT}; }}"  # noqa: E501

        self.film_combo = QComboBox()
        self.film_combo.setStyleSheet(_combo_style)
        bl.addLayout(self._field_row("Film", self.film_combo))

        self.cinema_combo = QComboBox()
        self.cinema_combo.setStyleSheet(_combo_style)
        self.cinema_combo.currentIndexChanged.connect(self._on_cinema_changed)
        bl.addLayout(self._field_row("Cinema", self.cinema_combo))

        self.screen_combo = QComboBox()
        self.screen_combo.setStyleSheet(_combo_style)
        bl.addLayout(self._field_row("Screen", self.screen_combo))

        # Date row
        dates_row = QHBoxLayout()
        dates_row.setSpacing(16)

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setStyleSheet(
            f"QDateEdit {{ border: 1.5px solid {BORDER}; border-radius: 8px; background: {BG_INPUT}; }}"  # noqa: E501
        )
        start_col = QVBoxLayout()
        start_lbl = QLabel("Start Date")
        start_lbl.setStyleSheet(
            f"color: {TEXT_SECONDARY}; background: transparent; border: none; "
            "font-size: 10pt; font-weight: 600;"
        )
        start_col.addWidget(start_lbl)
        start_col.addWidget(self.start_date)
        dates_row.addLayout(start_col)

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate().addDays(14))
        self.end_date.setStyleSheet(
            f"QDateEdit {{ border: 1.5px solid {BORDER}; border-radius: 8px; background: {BG_INPUT}; }}"  # noqa: E501
        )
        end_col = QVBoxLayout()
        end_lbl = QLabel("End Date")
        end_lbl.setStyleSheet(
            f"color: {TEXT_SECONDARY}; background: transparent; border: none; "
            "font-size: 10pt; font-weight: 600;"
        )
        end_col.addWidget(end_lbl)
        end_col.addWidget(self.end_date)
        dates_row.addLayout(end_col)

        bl.addLayout(dates_row)

        # Divider + showings
        sdiv = QFrame()
        sdiv.setFrameShape(QFrame.Shape.HLine)
        sdiv.setStyleSheet(f"background: {BORDER}; max-height: 1px; border: none;")
        bl.addWidget(sdiv)

        show_lbl = QLabel("Showings  (1–3 per day)")
        show_lbl.setStyleSheet(
            f"color: {TEXT_PRIMARY}; background: transparent; border: none; "
            "font-size: 10pt; font-weight: 700;"
        )
        bl.addWidget(show_lbl)

        self.showings_layout = QVBoxLayout()
        self.showings_layout.setSpacing(8)
        self._add_showing_row()
        bl.addLayout(self.showings_layout)

        add_showing_btn = secondary_button("+ Add Showing")
        add_showing_btn.setStyleSheet(
            f"QPushButton {{ background-color: {WHITE}; color: {ACCENT}; "
            f"border: 1.5px solid {BORDER}; border-radius: 8px; "
            "min-height: 32px; font-size: 10pt; font-weight: 700; }"
            f"QPushButton:hover {{ background-color: #FEF2F2; border-color: {ACCENT}; }}"
        )
        add_showing_btn.clicked.connect(self._add_showing_row)
        bl.addWidget(add_showing_btn)

        # Push content to top so it doesn't stretch vertically
        bl.addStretch()

        scroll.setWidget(body)
        root.addWidget(scroll, 1)  # stretch=1 so scroll area fills available space

        # fixed footer
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

        save_btn = primary_button("Create Listing")
        save_btn.setStyleSheet(
            f"QPushButton {{ background-color: {ACCENT}; color: {WHITE}; border: none; "
            f"min-height: 34px; max-height: 34px; min-width: 140px; font-weight: 700; "
            f"border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}"
        )
        save_btn.clicked.connect(self.accept)
        fl.addWidget(save_btn)

        root.addWidget(footer)

    def _field_row(self, label_text: str, widget: QWidget) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(5)
        lbl = QLabel(label_text)
        lbl.setStyleSheet(
            f"color: {TEXT_SECONDARY}; background: transparent; border: none; "
            "font-size: 10pt; font-weight: 600;"
        )
        col.addWidget(lbl)
        col.addWidget(widget)
        return col

    def _add_showing_row(self):
        if len(self._showings) >= 3:
            return

        row_widget = QWidget()
        row_widget.setStyleSheet("background: transparent;")
        row = QHBoxLayout(row_widget)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)

        time_lbl = QLabel("Time:")
        time_lbl.setStyleSheet(
            f"color: {TEXT_SECONDARY}; background: transparent; border: none; "
            "font-size: 10pt; font-weight: 600;"
        )
        time_edit = QTimeEdit()
        time_edit.setDisplayFormat("HH:mm")
        time_edit.setTime(QTime(10, 0))
        time_edit.setFixedWidth(110)
        time_edit.setStyleSheet(
            f"QTimeEdit {{ border: 1.5px solid {BORDER}; border-radius: 8px; background: {BG_INPUT}; padding: 4px 10px; color: {TEXT_PRIMARY}; }}"  # noqa: E501
            f"QTimeEdit:focus {{ border-color: {ACCENT}; background: {WHITE}; }}"
        )

        type_lbl = QLabel("Type:")
        type_lbl.setStyleSheet(
            f"color: {TEXT_SECONDARY}; background: transparent; border: none; "
            "font-size: 10pt; font-weight: 600;"
        )
        type_combo = QComboBox()
        type_combo.addItems(["morning", "afternoon", "evening"])
        type_combo.setFixedWidth(140)
        type_combo.setStyleSheet(
            f"QComboBox {{ border: 1.5px solid {BORDER}; border-radius: 8px; background-color: #F2F1EE; "  # noqa: E501
            f"padding: 4px 10px; color: {TEXT_PRIMARY}; outline: none; }}"
            f"QComboBox:focus {{ border-color: {ACCENT}; background-color: {WHITE}; }}"
            f"QComboBox::drop-down {{ border: none; width: 24px; }}"
            f"QComboBox QAbstractItemView {{ background-color: {WHITE}; selection-background-color: {ACCENT}; "  # noqa: E501
            f"selection-color: {WHITE}; border: 1px solid {BORDER}; outline: none; }}"
        )

        row.addWidget(time_lbl)
        row.addWidget(time_edit)
        row.addWidget(type_lbl)
        row.addWidget(type_combo)
        row.addStretch()

        self._showings.append((time_edit, type_combo))
        self.showings_layout.addWidget(row_widget)

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
