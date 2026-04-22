# ============================================
# Author: Himal Acharya
# Student ID: 22085619
# Last Edited: 2026-04-25
# ============================================

"""
desktop/ui/windows/admin/cancellation_log.py
implements the Cancellation Log view for Administrators to audit cancelled bookings and financial impacts.
provides insights into Fees Collected and Total Refunded amounts across all cinemas.
"""

from PyQt6.QtCore import Qt  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QComboBox,
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
    BORDER,
    DANGER,
    SPACING_LG,
    SPACING_MD,
    SPACING_SM,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WHITE,
    body_font,
)
from desktop.ui.widgets import (
    Card,
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


class CancellationLogView(QWidget):
    """a view providing a detailed audit trail of all booking cancellations across the cinema network."""

    def __init__(self):
        """initialises the cancellation log view and builds the interface."""
        super().__init__()
        self._build_ui()
        self._load_cinemas()

    def _build_ui(self):
        """constructs the primary layout featuring financial summary cards and the cancellation audit table."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        # header section with view title and audit trail description
        header_content = QVBoxLayout()
        header_content.setSpacing(4)
        header_content.addWidget(heading_label("Cancellation Log"))
        desc = muted_label(
            "Audit trail for all booking cancellations, refund amounts, and fee collections"
        )
        header_content.addWidget(desc)

        header = QHBoxLayout()
        header.addLayout(header_content)
        header.addStretch()
        layout.addLayout(header)

        # filter row for selecting specific cinemas
        filter_row = QHBoxLayout()
        filter_row.setSpacing(SPACING_SM)

        lbl_cinema = QLabel("Cinema:")
        lbl_cinema.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        filter_row.addWidget(lbl_cinema)
        self.cinema_filter = QComboBox()
        self.cinema_filter.setFixedWidth(260)
        self.cinema_filter.setStyleSheet(
            f"QComboBox {{ border: 1.5px solid {BORDER}; border-radius: 8px; background-color: #F2F1EE; "
            f"padding: 4px 10px; color: {TEXT_PRIMARY}; outline: none; min-height: 34px; max-height: 34px; }}"
            f"QComboBox:focus {{ border-color: {ACCENT}; background-color: {WHITE}; }}"
            f"QComboBox::drop-down {{ border: none; width: 24px; }}"
            f"QComboBox QAbstractItemView {{ background-color: {WHITE}; selection-background-color: {ACCENT}; "
            f"selection-color: {WHITE}; border: 1px solid {BORDER}; outline: none; }}"
        )
        self.cinema_filter.setFixedHeight(34)
        filter_row.addWidget(self.cinema_filter)

        search_btn = primary_button("Load")
        search_btn.setStyleSheet(
            f"QPushButton {{ background-color: {ACCENT}; color: {WHITE}; border: none; "
            f"min-height: 34px; max-height: 34px; min-width: 100px; font-weight: 700; "
            f"border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}"
        )
        search_btn.setFixedHeight(34)
        search_btn.clicked.connect(self._load_cancellations)
        filter_row.addWidget(search_btn)

        filter_row.addStretch()
        layout.addLayout(filter_row)

        # summary cards for high-level financial metrics
        summary_row = QHBoxLayout()
        summary_row.setSpacing(SPACING_MD)

        card_style = (
            f"Card {{ border: 1.5px solid {BORDER}; border-radius: 8px; background: {WHITE}; }}"
        )

        self.total_card = Card()
        self.total_card.setStyleSheet(card_style)
        self.total_lbl = QLabel("0")
        self.total_lbl.setFont(body_font(18, bold=True))
        self.total_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.total_lbl.setStyleSheet(f"color: {DANGER}; background: transparent;")
        total_title = QLabel("Cancellations")
        total_title.setStyleSheet(
            f"color: {TEXT_MUTED}; background: transparent; font-weight: 600;"
        )
        total_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.total_card.add(self.total_lbl)
        self.total_card.add(total_title)
        summary_row.addWidget(self.total_card)

        self.fees_card = Card()
        self.fees_card.setStyleSheet(card_style)
        self.fees_lbl = QLabel("\u00a30.00")
        self.fees_lbl.setFont(body_font(18, bold=True))
        self.fees_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fees_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent;")
        fees_title = QLabel("Fees Collected")
        fees_title.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent; font-weight: 600;")
        fees_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fees_card.add(self.fees_lbl)
        self.fees_card.add(fees_title)
        summary_row.addWidget(self.fees_card)

        self.refund_card = Card()
        self.refund_card.setStyleSheet(card_style)
        self.refund_lbl = QLabel("\u00a30.00")
        self.refund_lbl.setFont(body_font(18, bold=True))
        self.refund_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.refund_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent;")
        refund_title = QLabel("Total Refunded")
        refund_title.setStyleSheet(
            f"color: {TEXT_MUTED}; background: transparent; font-weight: 600;"
        )
        refund_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.refund_card.add(self.refund_lbl)
        self.refund_card.add(refund_title)
        summary_row.addWidget(self.refund_card)

        layout.addLayout(summary_row)

        # audit table displaying individual cancellation records
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(
            [
                "Reference",
                "Film",
                "Cinema",
                "Show Date",
                "Customer",
                "Original Cost",
                "Fee (50%)",
                "Refund",
                "Cancelled At",
            ]
        )

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 180)  # Film
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 150)  # Customer
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)

        self.table.setStyleSheet(
            f"QTableWidget {{ border: 1.5px solid {BORDER}; border-radius: 8px; }}"
            f"QHeaderView::section {{ border-right: 1px solid {BORDER}; border-bottom: 2.5px solid {BORDER}; }}"
            "QTableWidget::item:selected { background-color: #FEF2F2; color: #0A0908; }"
        )
        self.table.setItemDelegate(_LeftPaddingDelegate(14, self.table))
        layout.addWidget(self.table, 1)

        self.count_label = muted_label("")
        layout.addWidget(self.count_label)

    def _load_cinemas(self):
        """fetches all available cinemas from the api and populates the filter selector."""
        try:
            cinemas = api.get_cinemas()
            self.cinema_filter.clear()
            self.cinema_filter.addItem("All Cinemas", None)
            for c in cinemas:
                self.cinema_filter.addItem(
                    f"{c['cinema_name']} ({c.get('city_name', '')})",
                    c["cinema_id"],
                )
            self._load_cancellations()
        except Exception as e:
            error_dialog(self, str(e))

    def _load_cancellations(self):
        """retrieves cancelled booking data from the api and updates the summary metrics."""
        params = {"status": "cancelled"}
        cinema_id = self.cinema_filter.currentData()
        if cinema_id:
            params["cinema_id"] = cinema_id

        try:
            bookings = api.search_bookings(**params)
            self._fill_table(bookings)

            total = len(bookings)
            fees = sum(b.get("cancellation_fee", 0) for b in bookings)
            refunds = sum(b.get("refund_amount", 0) for b in bookings)

            self.total_lbl.setText(str(total))
            self.fees_lbl.setText(f"\u00a3{fees:.2f}")
            self.refund_lbl.setText(f"\u00a3{refunds:.2f}")
            self.count_label.setText(f"{total} cancelled booking(s)")
        except Exception as e:
            error_dialog(self, f"Failed to load cancellations: {e}")

    def _fill_table(self, bookings: list):
        """populates the audit table with detailed cancellation data."""
        self.table.setRowCount(len(bookings))
        for row, b in enumerate(bookings):
            self.table.setItem(row, 0, QTableWidgetItem(b["booking_reference"]))
            self.table.setItem(row, 1, QTableWidgetItem(b.get("film_title", "")))
            self.table.setItem(row, 2, QTableWidgetItem(b.get("cinema_name", "")))
            self.table.setItem(row, 3, QTableWidgetItem(str(b["show_date"])))
            self.table.setItem(row, 4, QTableWidgetItem(b["customer_name"]))
            self.table.setItem(row, 5, QTableWidgetItem(f"\u00a3{b['total_cost']:.2f}"))
            self.table.setItem(
                row, 6, QTableWidgetItem(f"\u00a3{b.get('cancellation_fee', 0):.2f}")
            )
            self.table.setItem(row, 7, QTableWidgetItem(f"\u00a3{b.get('refund_amount', 0):.2f}"))
            cancelled_at = b.get("cancelled_at") or "\u2014"
            if cancelled_at != "\u2014":
                cancelled_at = str(cancelled_at)[:19].replace("T", " ")
            self.table.setItem(row, 8, QTableWidgetItem(cancelled_at))
