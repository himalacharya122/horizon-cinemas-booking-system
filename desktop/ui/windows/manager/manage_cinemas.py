"""
desktop/ui/windows/manager/manage_cinemas.py
implements the Manager view for registering new cinemas, adding screens, and configuring base ticket pricing.
supports city-based organisation and show period pricing tiers.
"""

from PyQt6.QtCore import Qt  # type: ignore
from PyQt6.QtGui import QShowEvent  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from desktop.api_client import api
from desktop.ui.theme import (
    ACCENT,
    ACCENT_HOVER,
    BG_CARD,
    BG_DARK,
    BG_INPUT,
    BORDER,
    HERO_BG,
    SPACING_LG,
    SPACING_MD,
    SPACING_SM,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WHITE,
)
from desktop.ui.widgets import (
    error_dialog,
    heading_label,
    muted_label,
    primary_button,
    secondary_button,
    separator,
    show_toast,
)

# visual style definitions for shared UI components
_TABLE_QSS = (
    f"QTableWidget {{ border: 1.5px solid {BORDER}; border-radius: 8px; background: {WHITE}; }}"
    f"QHeaderView::section {{ background-color: {BG_DARK}; color: {TEXT_SECONDARY}; "
    f"font-weight: 600; padding: 8px 5px; border: none; border-bottom: 2.5px solid {BORDER}; "
    f"border-right: 1px solid {BORDER}; border-left: 10px solid transparent; }}"
    f"QTableWidget::item {{ border-left: 10px solid transparent; padding-right: 10px; }}"
    "QTableWidget::item:selected { background-color: #FEF2F2; color: #0A0908; }"
)

_PRIMARY_BTN_QSS = (
    f"QPushButton {{ background-color: {ACCENT}; color: {WHITE}; border: none; "
    f"min-height: 34px; max-height: 34px; font-weight: 700; border-radius: 6px; }}"
    f"QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}"
)

_DARK_BTN_QSS = (
    f"QPushButton {{ background-color: {HERO_BG}; color: {WHITE}; border: none; "
    f"min-height: 34px; max-height: 34px; min-width: 100px; font-weight: 700; border-radius: 6px; }}"
    f"QPushButton:hover {{ background-color: #2E2C28; }}"
)


class ManageCinemasView(QWidget):
    """a view for Manager users to configure cinema locations and regional pricing."""

    def __init__(self):
        """initialises the view and fetches the initial dataset."""
        super().__init__()
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        """constructs the primary layout including a QTabWidget for cinemas and pricing."""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        # header section with view title and refresh action
        header_content = QVBoxLayout()
        header_content.setSpacing(4)
        header_content.addWidget(heading_label("Manage Cinemas"))
        header_content.addWidget(
            muted_label("Add and configure cinemas, screens, and base ticket pricing")
        )

        header = QHBoxLayout()
        header.addLayout(header_content)
        header.addStretch()

        refresh_btn = secondary_button("Refresh")
        refresh_btn.setStyleSheet(_DARK_BTN_QSS)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self._load_data)
        header.addWidget(refresh_btn)

        layout.addLayout(header)
        layout.addWidget(separator())

        self.tabs = QTabWidget()

        # cinemas tab
        cinemas_page = QWidget()
        cl = QVBoxLayout(cinemas_page)
        cl.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        cl.setSpacing(SPACING_SM)

        cinema_btn_row = QHBoxLayout()
        cinema_btn_row.setSpacing(SPACING_SM)

        add_cinema_btn = primary_button("+ Add Cinema")
        add_cinema_btn.setStyleSheet(_PRIMARY_BTN_QSS)
        add_cinema_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_cinema_btn.clicked.connect(self._add_cinema)
        cinema_btn_row.addWidget(add_cinema_btn)

        add_screen_btn = secondary_button("+ Add Screen to Selected")
        add_screen_btn.setStyleSheet(
            f"QPushButton {{ background-color: {WHITE}; color: {TEXT_PRIMARY}; "
            f"border: 1.5px solid {BORDER}; min-height: 34px; max-height: 34px; "
            f"font-weight: 600; border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: #F1F1EF; border-color: #CDCBC6; }}"
        )
        add_screen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_screen_btn.clicked.connect(self._add_screen)
        cinema_btn_row.addWidget(add_screen_btn)

        cinema_btn_row.addStretch()
        cl.addLayout(cinema_btn_row)

        self.cinema_table = QTableWidget()
        self.cinema_table.setAlternatingRowColors(True)
        self.cinema_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.cinema_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.cinema_table.setShowGrid(False)
        self.cinema_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.cinema_table.verticalHeader().setVisible(False)
        self.cinema_table.verticalHeader().setDefaultSectionSize(44)
        self.cinema_table.setStyleSheet(_TABLE_QSS)
        self.cinema_table.setColumnCount(6)
        self.cinema_table.setHorizontalHeaderLabels(
            ["ID", "Cinema", "City", "Address", "Screens", "Status"]
        )
        hh = self.cinema_table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        cl.addWidget(self.cinema_table, 1)

        self.tabs.addTab(cinemas_page, "Cinemas")

        # prices tab
        prices_page = QWidget()
        pl = QVBoxLayout(prices_page)
        pl.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        pl.setSpacing(SPACING_SM)

        price_btn_row = QHBoxLayout()
        price_btn_row.setSpacing(SPACING_SM)

        set_price_btn = primary_button("Set / Update Price")
        set_price_btn.setStyleSheet(_PRIMARY_BTN_QSS)
        set_price_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        set_price_btn.clicked.connect(self._set_price)
        price_btn_row.addWidget(set_price_btn)
        price_btn_row.addStretch()
        pl.addLayout(price_btn_row)

        self.price_table = QTableWidget()
        self.price_table.setAlternatingRowColors(True)
        self.price_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.price_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.price_table.setShowGrid(False)
        self.price_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.price_table.verticalHeader().setVisible(False)
        self.price_table.verticalHeader().setDefaultSectionSize(44)
        self.price_table.setStyleSheet(_TABLE_QSS)
        self.price_table.setColumnCount(5)
        self.price_table.setHorizontalHeaderLabels(
            ["City", "Period", "Lower Hall", "Upper Gallery", "VIP"]
        )
        ph = self.price_table.horizontalHeader()
        ph.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        ph.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        ph.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        ph.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        ph.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        pl.addWidget(self.price_table, 1)

        self.tabs.addTab(prices_page, "Base Prices")

        layout.addWidget(self.tabs, 1)

        scroll.setWidget(content)
        outer.addWidget(scroll)

    # data loading logic
    def showEvent(self, event: QShowEvent):
        """refreshes the view data whenever the widget is shown."""
        super().showEvent(event)
        self._load_data()

    def _load_data(self):
        """fetches cinemas and pricing data from the api and populates the tables."""
        try:
            cinemas = api.get_cinemas()
            self.cinema_table.setRowCount(len(cinemas))
            for row, c in enumerate(cinemas):
                self.cinema_table.setItem(row, 0, QTableWidgetItem(str(c["cinema_id"])))
                self.cinema_table.setItem(row, 1, QTableWidgetItem(c["cinema_name"]))
                self.cinema_table.setItem(row, 2, QTableWidgetItem(c.get("city_name", "")))
                self.cinema_table.setItem(row, 3, QTableWidgetItem(c["address"]))
                self.cinema_table.setItem(row, 4, QTableWidgetItem(str(len(c.get("screens", [])))))
                status_item = QTableWidgetItem("Active" if c["is_active"] else "Inactive")
                status_item.setForeground(
                    __import__("PyQt6.QtGui", fromlist=["QColor"]).QColor(
                        "#10B981" if c["is_active"] else "#EF4444"
                    )
                )
                self.cinema_table.setItem(row, 5, status_item)
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

    # action handlers

    def _add_cinema(self):
        """opens the cinemadialog to register a new cinema location."""
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
        """opens the ScreenDialog to add a new screen to the currently selected cinema."""
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
        """opens the PriceDialog to configure regional base pricing."""
        dlg = PriceDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                api.set_price(dlg.get_data())
                show_toast(self, "Price updated.")
                self._load_data()
            except Exception as e:
                error_dialog(self, str(e))


# shared modal components


def _modal_lbl(text: str) -> QLabel:
    """creates a standard QLabel for modal field descriptions."""
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color: {TEXT_SECONDARY}; font-size: 10pt; font-weight: 600; "
        f"background: transparent; border: none;"
    )
    return lbl


def _modal_line(placeholder: str = "") -> QLineEdit:
    """creates a styled QLineEdit for use within modal dialogs."""
    inp = QLineEdit()
    inp.setPlaceholderText(placeholder)
    inp.setFixedHeight(36)
    inp.setStyleSheet(
        f"QLineEdit {{ background: {BG_INPUT}; border: 1.5px solid {BORDER}; "
        f"border-radius: 8px; padding: 4px 10px; font-size: 10pt; color: {TEXT_PRIMARY}; }}"
        f"QLineEdit:focus {{ border-color: {ACCENT}; background: {WHITE}; }}"
    )
    return inp


def _modal_combo(items: list = None) -> QComboBox:
    """creates a styled QComboBox for selection inputs in modals."""
    cb = QComboBox()
    cb.setFixedHeight(36)
    cb.setStyleSheet(
        f"QComboBox {{ background: {BG_INPUT}; border: 1.5px solid {BORDER}; "
        f"border-radius: 8px; padding: 4px 10px; font-size: 10pt; color: {TEXT_PRIMARY}; }}"
        f"QComboBox:focus {{ border-color: {ACCENT}; background: {WHITE}; }}"
        f"QComboBox::drop-down {{ border: none; width: 24px; }}"
    )
    if items:
        cb.addItems(items)
    return cb


def _modal_spin(min_val: int, max_val: int, value: int = None) -> QSpinBox:
    """creates a styled QSpinBox for numerical inputs in modals."""
    sp = QSpinBox()
    sp.setRange(min_val, max_val)
    if value is not None:
        sp.setValue(value)
    sp.setFixedHeight(36)
    sp.setStyleSheet(
        f"QSpinBox {{ background: {BG_INPUT}; border: 1.5px solid {BORDER}; "
        f"border-radius: 8px; padding: 4px 10px; font-size: 10pt; color: {TEXT_PRIMARY}; }}"
        f"QSpinBox:focus {{ border-color: {ACCENT}; background: {WHITE}; }}"
    )
    return sp


def _modal_divider() -> QFrame:
    """creates a thin horizontal separator for modal layouts."""
    div = QFrame()
    div.setFrameShape(QFrame.Shape.HLine)
    div.setStyleSheet(f"background: {BORDER}; max-height: 1px; border: none;")
    return div


def _modal_footer(dialog: QDialog, save_label: str) -> QWidget:
    """constructs the standard footer section for modal dialogs with Cancel and Save actions."""
    footer = QWidget()
    footer.setObjectName("modalFooter")
    footer.setStyleSheet(
        f"QWidget#modalFooter {{ background: {BG_CARD}; border-top: 1.5px solid {BORDER}; }}"
    )
    fl = QHBoxLayout(footer)
    fl.setContentsMargins(24, 14, 24, 14)
    fl.setSpacing(10)
    fl.addStretch()

    from desktop.ui.widgets import primary_button, secondary_button

    cancel_btn = secondary_button("Cancel")
    cancel_btn.setStyleSheet(
        f"QPushButton {{ background-color: {HERO_BG}; color: {WHITE}; border: none; "
        f"min-height: 34px; max-height: 34px; min-width: 100px; font-weight: 700; "
        f"border-radius: 6px; }}"
        f"QPushButton:hover {{ background-color: #2E2C28; }}"
    )
    cancel_btn.clicked.connect(dialog.reject)
    fl.addWidget(cancel_btn)

    save_btn = primary_button(save_label)
    save_btn.setStyleSheet(
        f"QPushButton {{ background-color: {ACCENT}; color: {WHITE}; border: none; "
        f"min-height: 34px; max-height: 34px; min-width: 130px; font-weight: 700; "
        f"border-radius: 6px; }}"
        f"QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}"
    )
    save_btn.clicked.connect(dialog.accept)
    fl.addWidget(save_btn)
    return footer


class CinemaDialog(QDialog):
    """a modal dialog for adding a new cinema and optionally creating a new city."""

    def __init__(self, parent):
        """initialises the CinemaDialog and sets its visual properties."""
        super().__init__(parent)
        self.setWindowTitle("Add Cinema")
        self.setMinimumWidth(480)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background: {BG_CARD}; }}")
        self._build()

    def _build(self):
        """constructs the form fields for cinema details including a conditional city input."""
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # header with title and instructional subtitle
        header = QWidget()
        header.setObjectName("modalHeader")
        header.setStyleSheet(f"QWidget#modalHeader {{ background: {BG_CARD}; }}")
        hl = QVBoxLayout(header)
        hl.setContentsMargins(24, 20, 24, 16)
        hl.setSpacing(4)
        title_lbl = QLabel("Add Cinema")
        title_lbl.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 15pt; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        hl.addWidget(title_lbl)
        sub_lbl = QLabel("Register a new Horizon cinema in an existing or new city")
        sub_lbl.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 10pt; background: transparent; border: none;"
        )
        hl.addWidget(sub_lbl)
        root.addWidget(header)
        root.addWidget(_modal_divider())

        # Body
        body = QWidget()
        body.setObjectName("modalBody")
        body.setStyleSheet(f"QWidget#modalBody {{ background: {BG_CARD}; }}")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(24, 20, 24, 20)
        bl.setSpacing(14)

        # City picker
        bl.addWidget(_modal_lbl("City"))
        self.city_combo = _modal_combo()
        self.city_combo.addItem("— Create new city —", None)
        try:
            for c in api.get_cities():
                self.city_combo.addItem(c["city_name"], c["city_id"])
        except Exception:
            pass
        self.city_combo.currentIndexChanged.connect(self._toggle_new_city)
        bl.addWidget(self.city_combo)

        # New city name (conditionally visible)
        self._new_city_lbl = _modal_lbl("New City Name")
        bl.addWidget(self._new_city_lbl)
        self.new_city_input = _modal_line("e.g. Birmingham")
        bl.addWidget(self.new_city_input)

        bl.addWidget(_modal_lbl("Cinema Name  *"))
        self.name_input = _modal_line("e.g. Horizon Manchester Central")
        bl.addWidget(self.name_input)

        bl.addWidget(_modal_lbl("Address  *"))
        self.address_input = _modal_line("Full street address")
        bl.addWidget(self.address_input)

        bl.addWidget(_modal_lbl("Phone"))
        self.phone_input = _modal_line("e.g. 0161 000 0000")
        bl.addWidget(self.phone_input)

        root.addWidget(body)
        root.addWidget(_modal_footer(self, "Add Cinema"))

        self._toggle_new_city()

    def _toggle_new_city(self):
        """toggles the visibility of the new city input field based on the picker selection."""
        is_new = self.city_combo.currentData() is None
        self._new_city_lbl.setVisible(is_new)
        self.new_city_input.setVisible(is_new)

    def get_data(self) -> dict:
        """collects and returns the form data as a dictionary for API submission."""
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
    """a modal dialog for adding a new screen to a cinema and defining its seat distribution."""

    def __init__(self, parent):
        """initialises the ScreenDialog and sets up its layout."""
        super().__init__(parent)
        self.setWindowTitle("Add Screen")
        self.setMinimumWidth(440)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background: {BG_CARD}; }}")
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QWidget()
        header.setObjectName("modalHeader")
        header.setStyleSheet(f"QWidget#modalHeader {{ background: {BG_CARD}; }}")
        hl = QVBoxLayout(header)
        hl.setContentsMargins(24, 20, 24, 16)
        hl.setSpacing(4)
        title_lbl = QLabel("Add Screen")
        title_lbl.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 15pt; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        hl.addWidget(title_lbl)
        sub_lbl = QLabel("Configure the screen layout and seat distribution")
        sub_lbl.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 10pt; background: transparent; border: none;"
        )
        hl.addWidget(sub_lbl)
        root.addWidget(header)
        root.addWidget(_modal_divider())

        # Body
        body = QWidget()
        body.setObjectName("modalBody")
        body.setStyleSheet(f"QWidget#modalBody {{ background: {BG_CARD}; }}")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(24, 20, 24, 20)
        bl.setSpacing(14)

        bl.addWidget(_modal_lbl("Screen Number"))
        self.number_spin = _modal_spin(1, 6, 1)
        bl.addWidget(self.number_spin)

        bl.addWidget(_modal_divider())

        bl.addWidget(_modal_lbl("Total Seats"))
        self.total_spin = _modal_spin(50, 120, 80)
        self.total_spin.valueChanged.connect(self._auto_calc)
        bl.addWidget(self.total_spin)

        # Two-column row for seat breakdown
        seat_row = QHBoxLayout()
        seat_row.setSpacing(SPACING_MD)

        lower_col = QVBoxLayout()
        lower_col.setSpacing(6)
        lower_col.addWidget(_modal_lbl("Lower Hall"))
        self.lower_spin = _modal_spin(1, 120)
        lower_col.addWidget(self.lower_spin)
        seat_row.addLayout(lower_col)

        upper_col = QVBoxLayout()
        upper_col.setSpacing(6)
        upper_col.addWidget(_modal_lbl("Upper Gallery"))
        self.upper_spin = _modal_spin(1, 120)
        upper_col.addWidget(self.upper_spin)
        seat_row.addLayout(upper_col)

        vip_col = QVBoxLayout()
        vip_col.setSpacing(6)
        vip_col.addWidget(_modal_lbl("VIP Seats"))
        self.vip_spin = _modal_spin(0, 10, 0)
        vip_col.addWidget(self.vip_spin)
        seat_row.addLayout(vip_col)

        bl.addLayout(seat_row)

        root.addWidget(body)
        root.addWidget(_modal_footer(self, "Add Screen"))

        self._auto_calc()

    def _auto_calc(self):
        """automatically calculates the seat breakdown based on the total number of seats."""
        total = self.total_spin.value()
        lower = round(total * 0.3)
        upper = total - lower
        self.lower_spin.setValue(lower)
        self.upper_spin.setValue(upper)

    def get_data(self) -> dict:
        """returns the configured screen and seat data."""
        return {
            "screen_number": self.number_spin.value(),
            "total_seats": self.total_spin.value(),
            "lower_hall_seats": self.lower_spin.value(),
            "upper_gallery_seats": self.upper_spin.value(),
            "vip_seats": self.vip_spin.value(),
        }


class PriceDialog(QDialog):
    """a modal dialog for setting or updating regional base ticket prices for specific show periods."""

    def __init__(self, parent):
        """initialises the PriceDialog and configures its properties."""
        super().__init__(parent)
        self.setWindowTitle("Set Base Price")
        self.setMinimumWidth(420)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background: {BG_CARD}; }}")
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QWidget()
        header.setObjectName("modalHeader")
        header.setStyleSheet(f"QWidget#modalHeader {{ background: {BG_CARD}; }}")
        hl = QVBoxLayout(header)
        hl.setContentsMargins(24, 20, 24, 16)
        hl.setSpacing(4)
        title_lbl = QLabel("Set Base Price")
        title_lbl.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 15pt; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        hl.addWidget(title_lbl)
        sub_lbl = QLabel("Configure ticket pricing by city and show period")
        sub_lbl.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 10pt; background: transparent; border: none;"
        )
        hl.addWidget(sub_lbl)
        root.addWidget(header)
        root.addWidget(_modal_divider())

        # Body
        body = QWidget()
        body.setObjectName("modalBody")
        body.setStyleSheet(f"QWidget#modalBody {{ background: {BG_CARD}; }}")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(24, 20, 24, 20)
        bl.setSpacing(14)

        bl.addWidget(_modal_lbl("City"))
        self.city_combo = _modal_combo()
        try:
            for c in api.get_cities():
                self.city_combo.addItem(c["city_name"], c["city_id"])
        except Exception:
            pass
        bl.addWidget(self.city_combo)

        bl.addWidget(_modal_lbl("Show Period"))
        self.period_combo = _modal_combo(["morning", "afternoon", "evening"])
        bl.addWidget(self.period_combo)

        bl.addWidget(_modal_lbl("Lower Hall Price  *"))
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(1, 100)
        self.price_spin.setDecimals(2)
        self.price_spin.setPrefix("£")
        self.price_spin.setValue(5.00)
        self.price_spin.setFixedHeight(36)
        self.price_spin.setStyleSheet(
            f"QDoubleSpinBox {{ background: {BG_INPUT}; border: 1.5px solid {BORDER}; "
            f"border-radius: 8px; padding: 4px 10px; font-size: 10pt; color: {TEXT_PRIMARY}; }}"
            f"QDoubleSpinBox:focus {{ border-color: {ACCENT}; background: {WHITE}; }}"
        )
        bl.addWidget(self.price_spin)

        root.addWidget(body)
        root.addWidget(_modal_footer(self, "Save Price"))

    def get_data(self) -> dict:
        """returns the selected city, period, and price data."""
        return {
            "city_id": self.city_combo.currentData(),
            "show_period": self.period_combo.currentText(),
            "lower_hall_price": self.price_spin.value(),
        }
