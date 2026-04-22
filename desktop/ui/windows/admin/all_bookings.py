# ============================================
# Author: Himal Acharya
# Student ID: 22085619
# Last Edited: 2026-04-25
# ============================================

"""
desktop/ui/windows/admin/all_bookings.py
implements the All Bookings ledger view for Administrators.
provides comprehensive access to booking records across all cinemas with integrated filtering by Cinema, Status, and Customer Name.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (  # type: ignore
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
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
    BG_INPUT,
    BORDER,
    SPACING_LG,
    SPACING_MD,
    SPACING_SM,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WHITE,
)
from desktop.ui.widgets import (
    error_dialog,
    heading_label,
    muted_label,
    primary_button,
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


class AllBookingsView(QWidget):
    """a view providing a global overview of all bookings processed within the system."""

    def __init__(self):
        """initialises the view, builds the interface, and loads the list of cinemas."""
        super().__init__()
        self._build_ui()
        self._load_cinemas()

    def _build_ui(self):
        """constructs the primary layout including headers, filter controls, and the bookings ledger table."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        # header section with view title and global ledger description
        header_content = QVBoxLayout()
        header_content.setSpacing(4)
        header_content.addWidget(heading_label("All Bookings"))
        desc = muted_label("Centralized booking ledger across all cinemas and statuses")
        header_content.addWidget(desc)

        header = QHBoxLayout()
        header.addLayout(header_content)
        header.addStretch()
        layout.addLayout(header)

        _combo_style = (
            f"QComboBox {{ border: 1.5px solid {BORDER}; border-radius: 8px; background-color: #F2F1EE; "
            f"padding: 4px 10px; color: {TEXT_PRIMARY}; outline: none; min-height: 34px; max-height: 34px; }}"
            f"QComboBox:focus {{ border-color: {ACCENT}; background-color: {WHITE}; }}"
            f"QComboBox::drop-down {{ border: none; width: 24px; }}"
            f"QComboBox QAbstractItemView {{ background-color: {WHITE}; selection-background-color: {ACCENT}; "
            f"selection-color: {WHITE}; border: 1px solid {BORDER}; outline: none; }}"
        )

        # filter row grouping selection and search controls
        filter_row = QHBoxLayout()
        filter_row.setSpacing(SPACING_SM)

        lbl_cinema = QLabel("Cinema:")
        lbl_cinema.setStyleSheet(
            f"color: {TEXT_SECONDARY}; background: transparent; font-weight: 600;"
        )
        filter_row.addWidget(lbl_cinema)
        self.cinema_filter = QComboBox()
        self.cinema_filter.setFixedWidth(220)
        self.cinema_filter.setStyleSheet(_combo_style)
        self.cinema_filter.setFixedHeight(34)
        filter_row.addWidget(self.cinema_filter)

        lbl_status = QLabel("Status:")
        lbl_status.setStyleSheet(
            f"color: {TEXT_SECONDARY}; background: transparent; font-weight: 600;"
        )
        filter_row.addWidget(lbl_status)
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "confirmed", "cancelled"])
        self.status_filter.setFixedWidth(120)
        self.status_filter.setStyleSheet(_combo_style)
        self.status_filter.setFixedHeight(34)
        filter_row.addWidget(self.status_filter)

        lbl_name = QLabel("Customer:")
        lbl_name.setStyleSheet(
            f"color: {TEXT_SECONDARY}; background: transparent; font-weight: 600;"
        )
        filter_row.addWidget(lbl_name)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Search name...")
        self.name_input.setFixedWidth(160)
        self.name_input.setFixedHeight(34)
        self.name_input.setStyleSheet(
            f"QLineEdit {{ border: 1.5px solid {BORDER}; border-radius: 8px; background: {BG_INPUT}; padding: 0 10px; }}"
            f"QLineEdit:focus {{ border-color: {ACCENT}; background: {WHITE}; }}"
        )
        filter_row.addWidget(self.name_input)

        search_btn = primary_button("Search")
        search_btn.setStyleSheet(
            f"QPushButton {{ background-color: {ACCENT}; color: {WHITE}; border: none; "
            f"min-height: 34px; max-height: 34px; min-width: 90px; font-weight: 700; "
            f"border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}"
        )
        search_btn.setFixedHeight(34)
        search_btn.clicked.connect(self._load_bookings)
        filter_row.addWidget(search_btn)

        filter_row.addStretch()
        layout.addLayout(filter_row)

        # bookings ledger table displaying detailed transaction records
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(
            [
                "Reference",
                "Film",
                "Cinema",
                "Date",
                "Time",
                "Customer",
                "Phone",
                "Tickets",
                "Total",
                "Status",
            ]
        )

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 180)  # Film
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Cinema
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 160)  # Customer
        hh.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(9, QHeaderView.ResizeMode.Stretch)

        self.table.setStyleSheet(
            f"QTableWidget {{ border: 1.5px solid {BORDER}; border-radius: 8px; }}"
            f"QHeaderView::section {{ border-right: 1px solid {BORDER}; border-bottom: 2.5px solid {BORDER}; }}"
            "QTableWidget::item:selected { background-color: #FEF2F2; color: #0A0908; }"
        )
        self.table.setItemDelegate(_LeftPaddingDelegate(14, self.table))
        layout.addWidget(self.table, 1)

        self.count_label = muted_label("")
        layout.addWidget(self.count_label)

        self.name_input.returnPressed.connect(self._load_bookings)

    def _load_cinemas(self):
        """fetches all available cinemas from the api and populates the cinema selector."""
        try:
            cinemas = api.get_cinemas()
            self.cinema_filter.clear()
            self.cinema_filter.addItem("All Cinemas", None)
            for c in cinemas:
                self.cinema_filter.addItem(
                    f"{c['cinema_name']} ({c.get('city_name', '')})",
                    c["cinema_id"],
                )
            self._load_bookings()
        except Exception as e:
            error_dialog(self, str(e))

    def _load_bookings(self):
        """retrieves booking records from the api based on selected filters and updates the view."""
        params = {}
        cinema_id = self.cinema_filter.currentData()
        if cinema_id:
            params["cinema_id"] = cinema_id

        status = self.status_filter.currentText()
        if status != "All":
            params["status"] = status

        name = self.name_input.text().strip()
        if name:
            params["customer_name"] = name

        try:
            bookings = api.search_bookings(**params)
            self._fill_table(bookings)
            self.count_label.setText(f"{len(bookings)} booking(s) found")
        except Exception as e:
            error_dialog(self, f"Failed to load bookings: {e}")

    def _fill_table(self, bookings: list):
        """populates the QTableWidget with the provided list of booking records."""
        self.table.setRowCount(len(bookings))
        for row, b in enumerate(bookings):
            self.table.setItem(row, 0, QTableWidgetItem(b["booking_reference"]))
            self.table.setItem(row, 1, QTableWidgetItem(b.get("film_title", "")))
            self.table.setItem(row, 2, QTableWidgetItem(b.get("cinema_name", "")))
            self.table.setItem(row, 3, QTableWidgetItem(str(b["show_date"])))
            self.table.setItem(row, 4, QTableWidgetItem(str(b.get("show_time", ""))[:5]))
            self.table.setItem(row, 5, QTableWidgetItem(b["customer_name"]))
            self.table.setItem(row, 6, QTableWidgetItem(b.get("customer_phone", "") or "\u2014"))
            self.table.setItem(row, 7, QTableWidgetItem(str(b["num_tickets"])))
            self.table.setItem(row, 8, QTableWidgetItem(f"\u00a3{b['total_cost']:.2f}"))
            self.table.setItem(row, 9, QTableWidgetItem(b["booking_status"].capitalize()))
