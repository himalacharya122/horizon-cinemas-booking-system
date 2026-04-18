"""
desktop/ui/windows/admin/cancellation_log.py
Admin view: view all cancellations across all cinemas with fees and refund info.
"""

from PyQt6.QtCore import Qt  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from desktop.api_client import api
from desktop.ui.theme import (
    DANGER,
    SPACING_LG,
    SPACING_MD,
    SPACING_SM,
    TEXT_MUTED,
    TEXT_SECONDARY,
    body_font,
)
from desktop.ui.widgets import (
    Card,
    error_dialog,
    heading_label,
    muted_label,
    primary_button,
    separator,
)


class CancellationLogView(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._load_cinemas()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        header = QHBoxLayout()
        header.addWidget(heading_label("Cancellation Log"))
        header.addStretch()
        layout.addLayout(header)
        layout.addWidget(separator())

        # Filter row
        filter_row = QHBoxLayout()
        filter_row.setSpacing(SPACING_SM)

        lbl_cinema = QLabel("Cinema:")
        lbl_cinema.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        filter_row.addWidget(lbl_cinema)
        self.cinema_filter = QComboBox()
        self.cinema_filter.setFixedWidth(260)
        filter_row.addWidget(self.cinema_filter)

        search_btn = primary_button("Load")
        search_btn.clicked.connect(self._load_cancellations)
        filter_row.addWidget(search_btn)

        filter_row.addStretch()
        layout.addLayout(filter_row)

        # Summary cards
        summary_row = QHBoxLayout()
        summary_row.setSpacing(SPACING_MD)

        self.total_card = Card()
        self.total_lbl = QLabel("0")
        self.total_lbl.setFont(body_font(18))
        self.total_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.total_lbl.setStyleSheet(f"color: {DANGER}; background: transparent; font-weight: 700;")
        total_title = QLabel("Cancellations")
        total_title.setFont(body_font(9))
        total_title.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        total_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.total_card.add(self.total_lbl)
        self.total_card.add(total_title)
        summary_row.addWidget(self.total_card)

        self.fees_card = Card()
        self.fees_lbl = QLabel("\u00a30.00")
        self.fees_lbl.setFont(body_font(18))
        self.fees_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fees_lbl.setStyleSheet(
            f"color: {TEXT_SECONDARY}; background: transparent; font-weight: 700;"
        )
        fees_title = QLabel("Fees Collected")
        fees_title.setFont(body_font(9))
        fees_title.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        fees_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fees_card.add(self.fees_lbl)
        self.fees_card.add(fees_title)
        summary_row.addWidget(self.fees_card)

        self.refund_card = Card()
        self.refund_lbl = QLabel("\u00a30.00")
        self.refund_lbl.setFont(body_font(18))
        self.refund_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.refund_lbl.setStyleSheet(
            f"color: {TEXT_SECONDARY}; background: transparent; font-weight: 700;"
        )
        refund_title = QLabel("Total Refunded")
        refund_title.setFont(body_font(9))
        refund_title.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        refund_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.refund_card.add(self.refund_lbl)
        self.refund_card.add(refund_title)
        summary_row.addWidget(self.refund_card)

        layout.addLayout(summary_row)

        # Table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
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
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)

        self.count_label = muted_label("")
        layout.addWidget(self.count_label)

    def _load_cinemas(self):
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
