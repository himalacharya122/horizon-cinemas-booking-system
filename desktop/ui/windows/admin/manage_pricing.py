# ============================================
# Author: Ridesha khadka
# Student ID: 23002960
# Last Edited: 2026-04-25
# ============================================

"""
desktop/ui/windows/admin/manage_pricing.py
implements the ticket pricing management interface for Administrators to adjust cinema-specific rates.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (  # type: ignore
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
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
    BG_CARD,
    BG_INPUT,
    BORDER,
    GOLD,
    HERO_BG,
    SPACING_LG,
    SPACING_MD,
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
    secondary_button,
    show_toast,
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


class ManagePricingView(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        header_content = QVBoxLayout()
        header_content.setSpacing(4)
        header_content.addWidget(heading_label("Ticket Pricing"))
        desc = muted_label(
            "Global ticket fee management, base price controls, and automated tax calculations"
        )
        header_content.addWidget(desc)

        header = QHBoxLayout()
        header.addLayout(header_content)
        header.addStretch()

        set_btn = primary_button("Set / Update Price")
        set_btn.setStyleSheet(
            f"QPushButton {{ background-color: {ACCENT}; color: {WHITE}; border: none; "
            f"min-height: 34px; max-height: 34px; min-width: 150px; font-weight: 700; "
            f"border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}"
        )
        set_btn.clicked.connect(self._set_price)
        header.addWidget(set_btn)

        refresh_btn = secondary_button("Refresh")
        refresh_btn.setStyleSheet(
            f"QPushButton {{ background-color: {HERO_BG}; color: {WHITE}; border: none; "
            f"min-height: 34px; max-height: 34px; min-width: 100px; font-weight: 700; "
            f"border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: #2E2C28; }}"
        )
        refresh_btn.clicked.connect(self._load_data)
        header.addWidget(refresh_btn)

        layout.addLayout(header)

        # Info card
        info_card = Card()
        info_card.setStyleSheet(f"Card {{ border: 1.5px solid {BORDER}; border-radius: 8px; }}")
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
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["City", "Period", "Lower Hall", "Upper Gallery", "VIP"]
        )

        hh = self.table.horizontalHeader()
        for i in range(5):
            hh.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        self.table.setStyleSheet(
            f"QTableWidget {{ border: 1.5px solid {BORDER}; border-radius: 8px; }}"
            f"QHeaderView::section {{ border-right: 1px solid {BORDER}; border-bottom: 2.5px solid {BORDER}; }}"
            "QTableWidget::item:selected { background-color: #FEF2F2; color: #0A0908; }"
        )
        self.table.setItemDelegate(_LeftPaddingDelegate(14, self.table))
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
                self.table.setItem(
                    row, 3, QTableWidgetItem(f"\u00a3{p['upper_gallery_price']:.2f}")
                )
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
        self.setMinimumSize(480, 500)
        self.setStyleSheet(f"QDialog {{ background: {BG_CARD}; }}")
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QWidget()
        header.setObjectName("modalHeader")
        header.setStyleSheet(f"QWidget#modalHeader {{ background: {WHITE}; }}")
        hl = QVBoxLayout(header)
        hl.setContentsMargins(24, 20, 24, 16)
        hl.setSpacing(4)
        title_lbl = QLabel("Update Base Pricing")
        title_lbl.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 15pt; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        hl.addWidget(title_lbl)
        sub_lbl = QLabel("Adjust cinema-specific ticket rates for different periods")
        sub_lbl.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 10pt; background: transparent; border: none;"
        )
        hl.addWidget(sub_lbl)
        root.addWidget(header)

        # Divider
        div = QWidget()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background: {BORDER};")
        root.addWidget(div)

        # Body
        body = QWidget()
        body.setObjectName("modalBody")
        body.setStyleSheet(f"QWidget#modalBody {{ background: {WHITE}; }}")
        form = QFormLayout(body)
        form.setContentsMargins(24, 24, 24, 24)
        form.setSpacing(14)

        _combo_style = (
            f"QComboBox {{ border: 1.5px solid {BORDER}; border-radius: 8px; background-color: #F2F1EE; "
            f"padding: 4px 10px; color: {TEXT_PRIMARY}; outline: none; min-height: 36px; }}"
            f"QComboBox:focus {{ border-color: {ACCENT}; background-color: {WHITE}; }}"
            f"QComboBox::drop-down {{ border: none; width: 24px; }}"
            f"QComboBox QAbstractItemView {{ background-color: {WHITE}; selection-background-color: {ACCENT}; "
            f"selection-color: {WHITE}; border: 1px solid {BORDER}; outline: none; }}"
        )

        self.city_combo = QComboBox()
        self.city_combo.setStyleSheet(_combo_style)
        try:
            for c in api.get_cities():
                self.city_combo.addItem(c["city_name"], c["city_id"])
        except Exception:
            pass
        form.addRow(self._lbl("City"), self.city_combo)

        self.period_combo = QComboBox()
        self.period_combo.addItems(["morning", "afternoon", "evening"])
        self.period_combo.setStyleSheet(_combo_style)
        form.addRow(self._lbl("Period"), self.period_combo)

        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(1, 100)
        self.price_spin.setDecimals(2)
        self.price_spin.setPrefix("\u00a3")
        self.price_spin.setValue(5.00)
        self.price_spin.setFixedHeight(36)
        self.price_spin.setStyleSheet(
            f"QDoubleSpinBox {{ border: 1.5px solid {BORDER}; border-radius: 8px; "
            f"background-color: {BG_INPUT}; padding: 4px 10px; color: {TEXT_PRIMARY}; }}"
            f"QDoubleSpinBox:focus {{ border-color: {ACCENT}; background-color: {WHITE}; }}"
        )
        form.addRow(self._lbl("Lower Hall Price"), self.price_spin)

        # Preview
        self.preview_upper = QLabel("")
        self.preview_vip = QLabel("")
        self.preview_upper.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 10pt; font-weight: 500; "
            "background: transparent; border: none;"
        )
        self.preview_vip.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 10pt; font-weight: 500; "
            "background: transparent; border: none;"
        )
        form.addRow(self._lbl("Upper Gallery"), self.preview_upper)
        form.addRow(self._lbl("VIP"), self.preview_vip)

        self.price_spin.valueChanged.connect(self._update_preview)
        self._update_preview()

        root.addWidget(body, 1)

        # Footer
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

        save_btn = primary_button("Save Price")
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
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 10pt; font-weight: 600; "
            f"background: transparent; border: none;"
        )
        return lbl

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
