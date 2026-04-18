"""
desktop/ui/windows/manager/manage_cinemas.py
Manager view: add new cinemas (in existing or new cities),
add screens to existing cinemas, set base prices.
"""

from PyQt6.QtWidgets import (  # type: ignore
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from desktop.api_client import api
from desktop.ui.theme import SPACING_LG, SPACING_MD
from desktop.ui.widgets import (
    error_dialog,
    heading_label,
    primary_button,
    secondary_button,
    separator,
    show_toast,
)


class ManageCinemasView(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        layout.addWidget(heading_label("Manage Cinemas"))
        layout.addWidget(separator())

        self.tabs = QTabWidget()

        # Cinemas tab
        cinemas_page = QWidget()
        cl = QVBoxLayout(cinemas_page)

        header = QHBoxLayout()
        add_btn = primary_button("+ Add Cinema")
        add_btn.clicked.connect(self._add_cinema)
        header.addWidget(add_btn)
        refresh_btn = secondary_button("Refresh")
        refresh_btn.clicked.connect(self._load_data)
        header.addWidget(refresh_btn)
        header.addStretch()
        cl.addLayout(header)

        self.cinema_table = QTableWidget()
        self.cinema_table.setAlternatingRowColors(True)
        self.cinema_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.cinema_table.verticalHeader().setVisible(False)
        self.cinema_table.setColumnCount(6)
        self.cinema_table.setHorizontalHeaderLabels(
            ["ID", "Cinema", "City", "Address", "Screens", "Status"]
        )
        self.cinema_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.cinema_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        cl.addWidget(self.cinema_table, 1)

        screen_btn = primary_button("+ Add Screen to Selected")
        screen_btn.clicked.connect(self._add_screen)
        cl.addWidget(screen_btn)

        self.tabs.addTab(cinemas_page, "Cinemas")

        # Prices tab
        prices_page = QWidget()
        pl = QVBoxLayout(prices_page)

        price_header = QHBoxLayout()
        set_price_btn = primary_button("Set / Update Price")
        set_price_btn.clicked.connect(self._set_price)
        price_header.addWidget(set_price_btn)
        price_header.addStretch()
        pl.addLayout(price_header)

        self.price_table = QTableWidget()
        self.price_table.setAlternatingRowColors(True)
        self.price_table.verticalHeader().setVisible(False)
        self.price_table.setColumnCount(5)
        self.price_table.setHorizontalHeaderLabels(
            ["City", "Period", "Lower Hall", "Upper Gallery", "VIP"]
        )
        self.price_table.horizontalHeader().setStretchLastSection(True)
        pl.addWidget(self.price_table, 1)

        self.tabs.addTab(prices_page, "Base Prices")
        layout.addWidget(self.tabs, 1)

    # Data loading
    def _load_data(self):
        try:
            cinemas = api.get_cinemas()
            self.cinema_table.setRowCount(len(cinemas))
            for row, c in enumerate(cinemas):
                self.cinema_table.setItem(row, 0, QTableWidgetItem(str(c["cinema_id"])))
                self.cinema_table.setItem(row, 1, QTableWidgetItem(c["cinema_name"]))
                self.cinema_table.setItem(row, 2, QTableWidgetItem(c.get("city_name", "")))
                self.cinema_table.setItem(row, 3, QTableWidgetItem(c["address"]))
                self.cinema_table.setItem(row, 4, QTableWidgetItem(str(len(c.get("screens", [])))))
                self.cinema_table.setItem(
                    row, 5, QTableWidgetItem("Active" if c["is_active"] else "Inactive")
                )
        except Exception as e:
            error_dialog(self, str(e))

        try:
            prices = api.get_prices()
            cities = {c["city_id"]: c["city_name"] for c in api.get_cities()}
            self.price_table.setRowCount(len(prices))
            for row, p in enumerate(prices):
                self.price_table.setItem(row, 0, QTableWidgetItem(cities.get(p["city_id"], "?")))
                self.price_table.setItem(row, 1, QTableWidgetItem(p["show_period"].capitalize()))
                self.price_table.setItem(row, 2, QTableWidgetItem(f"£{p['lower_hall_price']:.2f}"))
                self.price_table.setItem(
                    row, 3, QTableWidgetItem(f"£{p['upper_gallery_price']:.2f}")
                )
                self.price_table.setItem(row, 4, QTableWidgetItem(f"£{p['vip_price']:.2f}"))
        except Exception as e:
            error_dialog(self, str(e))

    # Actions
    def _add_cinema(self):
        dlg = CinemaDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                api.create_cinema(dlg.get_data())
                show_toast(self, "Cinema added.")
                self._load_data()
            except Exception as e:
                detail = str(e)
                if hasattr(e, "response"):
                    try:
                        detail = e.response.json().get("detail", detail)
                    except Exception:
                        pass
                error_dialog(self, detail)

    def _add_screen(self):
        row = self.cinema_table.currentRow()
        if row < 0:
            error_dialog(self, "Select a cinema first.")
            return
        cinema_id = int(self.cinema_table.item(row, 0).text())
        dlg = ScreenDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                api.add_screen(cinema_id, dlg.get_data())
                show_toast(self, "Screen added.")
                self._load_data()
            except Exception as e:
                detail = str(e)
                if hasattr(e, "response"):
                    try:
                        detail = e.response.json().get("detail", detail)
                    except Exception:
                        pass
                error_dialog(self, detail)

    def _set_price(self):
        dlg = PriceDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                api.set_price(dlg.get_data())
                show_toast(self, "Price updated.")
                self._load_data()
            except Exception as e:
                error_dialog(self, str(e))


# Dialogs
class CinemaDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Add Cinema")
        self.setMinimumWidth(460)
        self._build()

    def _build(self):
        form = QFormLayout(self)

        # City: existing or new
        self.city_combo = QComboBox()
        self.city_combo.addItem("— Create new city —", None)
        try:
            for c in api.get_cities():
                self.city_combo.addItem(c["city_name"], c["city_id"])
        except Exception:
            pass
        self.city_combo.currentIndexChanged.connect(self._toggle_new_city)
        form.addRow("City:", self.city_combo)

        self.new_city_input = QLineEdit()
        self.new_city_input.setPlaceholderText("New city name")
        form.addRow("New City:", self.new_city_input)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Horizon Manchester Central")
        form.addRow("Cinema Name:", self.name_input)

        self.address_input = QLineEdit()
        form.addRow("Address:", self.address_input)

        self.phone_input = QLineEdit()
        form.addRow("Phone:", self.phone_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

        self._toggle_new_city()

    def _toggle_new_city(self):
        is_new = self.city_combo.currentData() is None
        self.new_city_input.setVisible(is_new)

    def get_data(self) -> dict:
        d = {
            "cinema_name": self.name_input.text().strip(),
            "address": self.address_input.text().strip(),
            "phone": self.phone_input.text().strip() or None,
            "screens": [],
        }
        city_id = self.city_combo.currentData()
        if city_id:
            d["city_id"] = city_id
        else:
            d["new_city_name"] = self.new_city_input.text().strip()
        return d


class ScreenDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Add Screen")
        self.setMinimumWidth(400)
        self._build()

    def _build(self):
        form = QFormLayout(self)

        self.number_spin = QSpinBox()
        self.number_spin.setRange(1, 6)
        form.addRow("Screen Number:", self.number_spin)

        self.total_spin = QSpinBox()
        self.total_spin.setRange(50, 120)
        self.total_spin.setValue(80)
        self.total_spin.valueChanged.connect(self._auto_calc)
        form.addRow("Total Seats:", self.total_spin)

        self.lower_spin = QSpinBox()
        self.lower_spin.setRange(1, 120)
        form.addRow("Lower Hall:", self.lower_spin)

        self.upper_spin = QSpinBox()
        self.upper_spin.setRange(1, 120)
        form.addRow("Upper Gallery:", self.upper_spin)

        self.vip_spin = QSpinBox()
        self.vip_spin.setRange(0, 10)
        form.addRow("VIP Seats:", self.vip_spin)

        self._auto_calc()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _auto_calc(self):
        total = self.total_spin.value()
        lower = round(total * 0.3)
        upper = total - lower
        self.lower_spin.setValue(lower)
        self.upper_spin.setValue(upper)

    def get_data(self) -> dict:
        return {
            "screen_number": self.number_spin.value(),
            "total_seats": self.total_spin.value(),
            "lower_hall_seats": self.lower_spin.value(),
            "upper_gallery_seats": self.upper_spin.value(),
            "vip_seats": self.vip_spin.value(),
        }


class PriceDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Set Base Price")
        self.setMinimumWidth(380)
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
        self.price_spin.setPrefix("£")
        self.price_spin.setValue(5.00)
        form.addRow("Lower Hall Price:", self.price_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def get_data(self) -> dict:
        return {
            "city_id": self.city_combo.currentData(),
            "show_period": self.period_combo.currentText(),
            "lower_hall_price": self.price_spin.value(),
        }
