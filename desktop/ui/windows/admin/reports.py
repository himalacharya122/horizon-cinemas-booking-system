"""
desktop/ui/windows/admin/reports.py
Admin reports: monthly revenue, bookings per listing, top films,
staff leaderboard, occupancy, cancellation rates + CSV export.
"""

import csv
import io
from datetime import date
from PyQt6.QtCore import Qt  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QSpinBox, QLabel,
    QApplication, QFileDialog,
)

from desktop.ui.theme import SPACING_MD, SPACING_LG, ACCENT, TEXT_MUTED, TEXT_SECONDARY
from desktop.ui.widgets import (
    heading_label, primary_button, secondary_button, separator,
    error_dialog, show_toast, muted_label,
)
from desktop.ui.theme import body_font
from desktop.api_client import api


class ReportsView(QWidget):

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        layout.addWidget(heading_label("Reports"))

        # Filters
        filters = QHBoxLayout()
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2026, 2046)
        self.year_spin.setValue(date.today().year)
        self.year_spin.setMinimumWidth(100)
        year_lbl = QLabel("Year:")
        year_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        filters.addWidget(year_lbl)
        filters.addWidget(self.year_spin)

        self.month_spin = QSpinBox()
        self.month_spin.setRange(1, 12)
        self.month_spin.setValue(date.today().month)
        self.month_spin.setMinimumWidth(85)
        month_lbl = QLabel("Month:")
        month_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        filters.addWidget(month_lbl)
        filters.addWidget(self.month_spin)

        gen_btn = primary_button("Generate")
        gen_btn.clicked.connect(self._generate_all)
        filters.addWidget(gen_btn)

        export_btn = secondary_button("Export CSV")
        export_btn.clicked.connect(self._export_csv)
        filters.addWidget(export_btn)

        copy_btn = secondary_button("Copy to Clipboard")
        copy_btn.clicked.connect(self._copy_to_clipboard)
        filters.addWidget(copy_btn)

        filters.addStretch()
        layout.addLayout(filters)

        layout.addWidget(separator())

        # Tabs
        self.tabs = QTabWidget()

        self.rev_table = self._make_table(
            ["City", "Cinema", "Bookings", "Revenue", "Cancellations", "Cancel Fees"]
        )
        self.tabs.addTab(self.rev_table, "Monthly Revenue")

        self.listing_table = self._make_table(
            ["Film", "Screen", "Cinema", "Start", "End", "Bookings", "Tickets"]
        )
        self.tabs.addTab(self.listing_table, "Bookings per Listing")

        self.top_table = self._make_table(["Film", "Revenue", "Bookings"])
        self.tabs.addTab(self.top_table, "Top Films")

        self.staff_table = self._make_table(
            ["Staff", "Username", "Cinema", "Bookings", "Revenue"]
        )
        self.tabs.addTab(self.staff_table, "Staff Bookings")

        self.occ_table = self._make_table(
            ["Cinema", "Screen", "Capacity", "Bookings", "Tickets Sold", "Occupancy %"]
        )
        self.tabs.addTab(self.occ_table, "Occupancy")

        self.cancel_table = self._make_table(
            ["Cinema", "Total Bookings", "Cancelled", "Rate %", "Fees Collected", "Refunded"]
        )
        self.tabs.addTab(self.cancel_table, "Cancellation Rate")

        layout.addWidget(self.tabs, 1)

    def _make_table(self, headers: list) -> QTableWidget:
        t = QTableWidget()
        t.setAlternatingRowColors(True)
        t.setColumnCount(len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.horizontalHeader().setStretchLastSection(True)
        t.verticalHeader().setVisible(False)
        t.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        return t

    def _fill_table(self, table: QTableWidget, rows: list[list]):
        table.setRowCount(len(rows))
        for r, row_data in enumerate(rows):
            for c, val in enumerate(row_data):
                table.setItem(r, c, QTableWidgetItem(str(val)))

    def _generate_all(self):
        y = self.year_spin.value()
        m = self.month_spin.value()
        try:
            # Revenue
            data = api.report_revenue(y, m)
            self._fill_table(self.rev_table, [
                [d["city_name"], d["cinema_name"], d["total_bookings"],
                 f"\u00a3{d['total_revenue']:.2f}", d["cancellations"],
                 f"\u00a3{d['cancellation_fees']:.2f}"]
                for d in data
            ])

            # Bookings per listing
            data = api.report_bookings_per_listing()
            self._fill_table(self.listing_table, [
                [d["film_title"], d["screen_number"], d["cinema_name"],
                 d["start_date"], d["end_date"], d["booking_count"], d["tickets_sold"]]
                for d in data
            ])

            # Top films
            data = api.report_top_films(y, m)
            self._fill_table(self.top_table, [
                [d["film_title"], f"\u00a3{d['revenue']:.2f}", d["bookings"]]
                for d in data
            ])

            # Staff
            data = api.report_staff_bookings(y, m)
            self._fill_table(self.staff_table, [
                [d["staff_name"], d["username"], d["cinema_name"],
                 d["total_bookings"], f"\u00a3{d['total_revenue']:.2f}"]
                for d in data
            ])

            # Occupancy
            data = api.report_occupancy(y, m)
            self._fill_table(self.occ_table, [
                [d["cinema_name"], f"Screen {d['screen_number']}",
                 d["total_seats"], d["total_bookings"],
                 d["tickets_sold"], f"{d['occupancy_pct']}%"]
                for d in data
            ])

            # Cancellation rate
            data = api.report_cancellation_rate(y, m)
            self._fill_table(self.cancel_table, [
                [d["cinema_name"], d["total_bookings"], d["cancelled"],
                 f"{d['cancellation_rate']}%",
                 f"\u00a3{d['fees_collected']:.2f}",
                 f"\u00a3{d['total_refunded']:.2f}"]
                for d in data
            ])

            show_toast(self, "Reports generated.", success=True)

        except Exception as e:
            error_dialog(self, str(e))

    def _get_current_table(self) -> QTableWidget:
        """Return the currently visible table from the tab widget."""
        return self.tabs.currentWidget()

    def _table_to_csv_string(self, table: QTableWidget) -> str:
        """Convert a QTableWidget to a CSV string."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Headers
        headers = []
        for c in range(table.columnCount()):
            item = table.horizontalHeaderItem(c)
            headers.append(item.text() if item else f"Col{c}")
        writer.writerow(headers)

        # Rows
        for r in range(table.rowCount()):
            row = []
            for c in range(table.columnCount()):
                item = table.item(r, c)
                row.append(item.text() if item else "")
            writer.writerow(row)

        return output.getvalue()

    def _export_csv(self):
        """Export the current tab's table to a CSV file."""
        table = self._get_current_table()
        if not table or table.rowCount() == 0:
            error_dialog(self, "No data to export. Generate reports first.")
            return

        tab_name = self.tabs.tabText(self.tabs.currentIndex()).replace(" ", "_")
        y = self.year_spin.value()
        m = self.month_spin.value()
        default_name = f"HCBS_{tab_name}_{y}_{m:02d}.csv"

        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", default_name, "CSV Files (*.csv)"
        )
        if not path:
            return

        try:
            csv_text = self._table_to_csv_string(table)
            with open(path, "w", newline="", encoding="utf-8") as f:
                f.write(csv_text)
            show_toast(self, f"Exported to {path}", success=True)
        except Exception as e:
            error_dialog(self, f"Export failed: {e}")

    def _copy_to_clipboard(self):
        """Copy the current tab's table data to clipboard as tab-separated text."""
        table = self._get_current_table()
        if not table or table.rowCount() == 0:
            error_dialog(self, "No data to copy. Generate reports first.")
            return

        lines = []
        # Headers
        headers = []
        for c in range(table.columnCount()):
            item = table.horizontalHeaderItem(c)
            headers.append(item.text() if item else "")
        lines.append("\t".join(headers))

        # Rows
        for r in range(table.rowCount()):
            row = []
            for c in range(table.columnCount()):
                item = table.item(r, c)
                row.append(item.text() if item else "")
            lines.append("\t".join(row))

        text = "\n".join(lines)
        QApplication.clipboard().setText(text)
        show_toast(self, "Copied to clipboard!", success=True)
