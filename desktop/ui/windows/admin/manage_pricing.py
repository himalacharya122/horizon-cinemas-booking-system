"""
desktop/ui/windows/admin/manage_pricing.py
Admin view: view and update base pricing per city and time period.
"""

from PyQt6.QtCore import Qt  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QLabel, QDialog, QFormLayout,
    QDialogButtonBox, QDoubleSpinBox,
)

from desktop.ui.theme import (
    ACCENT, SUCCESS, GOLD, WHITE,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    heading_font, body_font, SPACING_SM, SPACING_MD, SPACING_LG,
)
from desktop.ui.widgets import (
    heading_label, primary_button, secondary_button,
    separator, show_toast, error_dialog, Card, muted_label,
)
from desktop.api_client import api


class ManagePricingView(QWidget):

    def __init__(self):
        super().__init__()
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        header = QHBoxLayout()
        header.addWidget(heading_label("Ticket Pricing"))
        header.addStretch()

        set_btn = primary_button("Set / Update Price")
        set_btn.clicked.connect(self._set_price)
        header.addWidget(set_btn)

        refresh_btn = secondary_button("Refresh")
        refresh_btn.clicked.connect(self._load_data)
        header.addWidget(refresh_btn)

        layout.addLayout(header)
        layout.addWidget(separator())

        # Info card
        info_card = Card()
        info_lbl = QLabel(
            "Pricing is set per city and time period. "
            "Upper Gallery = Lower Hall \u00d7 1.20  |  VIP = Lower Hall \u00d7 1.44"
        )
        info_lbl.setFont(body_font(10))
        info_lbl.setStyleSheet(f"color: {GOLD}; background: transparent; padding: 4px;")
        info_lbl.setWordWrap(True)
        info_card.add(info_lbl)
        layout.addWidget(info_card)

        # Pricing table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "City", "Period", "Lower Hall", "Upper Gallery", "VIP"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)

        self.count_label = muted_label("")
        layout.addWidget(self.count_label)

    def _load_data(self):
        try:
            prices = api.get_prices()
            cities = {c["city_id"]: c["city_name"] for c in api.get_cities()}

            self.table.setRowCount(len(prices))
            for row, p in enumerate(prices):
                self.table.setItem(row, 0, QTableWidgetItem(cities.get(p["city_id"], "?")))
                self.table.setItem(row, 1, QTableWidgetItem(p["show_period"].capitalize()))
                self.table.setItem(row, 2, QTableWidgetItem(f"\u00a3{p['lower_hall_price']:.2f}"))
                self.table.setItem(row, 3, QTableWidgetItem(f"\u00a3{p['upper_gallery_price']:.2f}"))
                self.table.setItem(row, 4, QTableWidgetItem(f"\u00a3{p['vip_price']:.2f}"))

            self.count_label.setText(f"{len(prices)} pricing rule(s)")
        except Exception as e:
            error_dialog(self, f"Failed to load prices: {e}")

    def _set_price(self):
        dlg = PricingDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                api.set_price(dlg.get_data())
                show_toast(self, "Price updated successfully.", success=True)
                self._load_data()
            except Exception as e:
                error_dialog(self, str(e))


class PricingDialog(QDialog):

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Set Base Price")
        self.setMinimumWidth(400)
        self._build()

    def _build(self):
        form = QFormLayout(self)

        self.city_combo = QComboBox()
        try:
            for c in api.get_cities():
                self.city_combo.addItem(c["city_name"], c["city_id"])
        except Exception:
            pass
        form.addRow("City:", self.city_combo)

        self.period_combo = QComboBox()
        self.period_combo.addItems(["morning", "afternoon", "evening"])
        form.addRow("Period:", self.period_combo)

        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(1, 100)
        self.price_spin.setDecimals(2)
        self.price_spin.setPrefix("\u00a3")
        self.price_spin.setValue(5.00)
        form.addRow("Lower Hall Price:", self.price_spin)

        # Preview
        self.preview_upper = QLabel("")
        self.preview_vip = QLabel("")
        self.preview_upper.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        self.preview_vip.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        form.addRow("Upper Gallery:", self.preview_upper)
        form.addRow("VIP:", self.preview_vip)

        self.price_spin.valueChanged.connect(self._update_preview)
        self._update_preview()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _update_preview(self):
        base = self.price_spin.value()
        self.preview_upper.setText(f"\u00a3{base * 1.20:.2f} (auto-calculated)")
        self.preview_vip.setText(f"\u00a3{base * 1.44:.2f} (auto-calculated)")

    def get_data(self) -> dict:
        return {
            "city_id": self.city_combo.currentData(),
            "show_period": self.period_combo.currentText(),
            "lower_hall_price": self.price_spin.value(),
        }
