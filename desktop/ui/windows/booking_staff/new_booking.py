"""
desktop/ui/windows/booking_staff/new_booking.py
implements the New Booking interface for Booking Staff.
features an interactive Seat Map, AI-driven seat recommendations, upsell suggestions, and receipt generation.
"""

from typing import Dict, List, Optional

from PyQt6.QtCore import QDate, Qt, pyqtSignal  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QApplication,
    QButtonGroup,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from desktop.api_client import api
from desktop.ui.theme import (
    ACCENT,
    ACCENT_HOVER,
    ACCENT_LIGHT,
    BG_CARD,
    BG_DARKEST,
    BG_HOVER,
    BORDER,
    GOLD,
    HERO_BG,
    RADIUS,
    SPACING_LG,
    SPACING_MD,
    SPACING_SM,
    SUCCESS,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WHITE,
    body_font,
    heading_font,
)
from desktop.ui.widgets import (
    Card,
    error_dialog,
    form_row,
    heading_label,
    labelled_value,
    muted_label,
    primary_button,
    secondary_button,
    separator,
    show_toast,
    status_badge,
    subheading_label,
)

# ai seat recommendation logic


def _recommend_seats(seats: List[dict], num_tickets: int) -> List[dict]:
    """
    score all available seats and return the best n consecutive seats.
    scoring: centre row × centre column weighting.
    prefers consecutive seats within a single row.
    """
    available = [s for s in seats if s["is_available"]]
    if len(available) < num_tickets:
        return []

    # Group available seats by row
    rows: Dict[str, List[dict]] = {}
    for seat in available:
        rows.setdefault(seat["row_label"], []).append(seat)

    sorted_row_keys = sorted(rows.keys())
    num_rows = len(sorted_row_keys)
    best_row_idx = num_rows // 2  # centre of the available rows

    def col_num(seat_number: str, row_label: str) -> int:
        """Extract the column number from a seat_number string."""
        suffix = seat_number[len(row_label) :] if seat_number.startswith(row_label) else seat_number
        digits = "".join(c for c in suffix if c.isdigit())
        return int(digits) if digits else 0

    def seat_score(seat: dict, row_idx: int, row_size: int) -> float:
        row_dist = abs(row_idx - best_row_idx)
        col = col_num(seat["seat_number"], seat["row_label"])
        col_dist = abs(col - row_size // 2)
        return row_dist * 3.0 + col_dist

    best_group: Optional[List[dict]] = None
    best_score = float("inf")

    for row_idx, row_key in enumerate(sorted_row_keys):
        row_seats = sorted(
            rows[row_key],
            key=lambda s: col_num(s["seat_number"], s["row_label"]),
        )
        row_size = len(row_seats)
        # Try all consecutive windows of num_tickets seats in this row
        if row_size >= num_tickets:
            for i in range(row_size - num_tickets + 1):
                group = row_seats[i : i + num_tickets]
                score = sum(seat_score(s, row_idx, row_size) for s in group)
                if score < best_score:
                    best_score = score
                    best_group = group

    if best_group:
        return best_group

    # Fallback: best individual seats across rows (when no single row has enough)
    all_scored = []
    for row_idx, row_key in enumerate(sorted_row_keys):
        row_size = len(rows[row_key])
        for seat in rows[row_key]:
            all_scored.append((seat_score(seat, row_idx, row_size), seat))
    all_scored.sort(key=lambda x: x[0])
    return [s[1] for s in all_scored[:num_tickets]]


# rule-based upsell suggestion logic


def _build_upsell_tips(avail: dict) -> List[str]:
    """
    Return a list of upsell tip strings based on availability data.
    Rule-based — no API call required.
    """
    tips = []
    seats_available = avail.get("seats_available", 0)
    seats_total = avail.get("seats_total", 1)
    seat_type = avail.get("seat_type", "")
    unit_price = avail.get("unit_price", 0.0)
    show_type = avail.get("show_type", "")

    occupancy = 1 - (seats_available / max(seats_total, 1))

    if occupancy >= 0.80:
        tips.append(
            f"Only {seats_available} seat(s) remaining — this showing is nearly sold out. "
            "Secure the booking now."
        )
    elif occupancy >= 0.60:
        tips.append(f"{seats_available} of {seats_total} seats still available — filling up fast.")

    if seat_type == "lower_hall":
        vip_price = round(unit_price * 1.44, 2)
        ug_price = round(unit_price * 1.20, 2)
        tips.append(
            f"Upper Gallery available from £{ug_price:.2f}/ticket — better viewing angle, "
            f"only £{ug_price - unit_price:.2f} more."
        )
        tips.append(
            f"VIP seats available from £{vip_price:.2f}/ticket — worth mentioning for special occasions."
        )
    elif seat_type == "upper_gallery":
        vip_price = round((unit_price / 1.20) * 1.44, 2)
        diff = round(vip_price - unit_price, 2)
        tips.append(
            f"VIP seats available from £{vip_price:.2f}/ticket — only £{diff:.2f} more per person."
        )

    if show_type == "evening":
        tips.append("Evening shows tend to sell out — recommend booking the full group now.")

    return tips[:3]  # cap at 3 tips


# custom seat map button widget


class SeatButton(QPushButton):
    """a specialized button representing a single seat in the cinema auditorium."""

    toggled_seat = pyqtSignal(dict, bool)  # seat_data, is_selected

    STATE_AVAILABLE = "available"
    STATE_BOOKED = "booked"
    STATE_SELECTED = "selected"
    STATE_RECOMMENDED = "recommended"

    # Seat button size — large enough to comfortably show 2–3 character labels
    SEAT_SIZE = 52

    def __init__(self, seat: dict):
        super().__init__()
        self.seat = seat
        self._state = self.STATE_BOOKED if not seat["is_available"] else self.STATE_AVAILABLE
        self._selected = False

        # Label: strip row prefix to show just column number
        row = seat["row_label"]
        label = seat["seat_number"]
        if label.startswith(row):
            label = label[len(row) :]
        if not label:
            label = seat["seat_number"]

        self.setText(label)
        # Fixed square size — generous enough that padding + border don't clip text
        self.setFixedSize(self.SEAT_SIZE, self.SEAT_SIZE)
        self.setFont(body_font(10, bold=True))
        self.setToolTip(seat["seat_number"])
        self.setCursor(
            Qt.CursorShape.PointingHandCursor
            if seat["is_available"]
            else Qt.CursorShape.ForbiddenCursor
        )
        self._apply_style()

        if seat["is_available"]:
            self.clicked.connect(self._on_click)

    def _on_click(self):
        self._selected = not self._selected
        self._state = self.STATE_SELECTED if self._selected else self.STATE_AVAILABLE
        self._apply_style()
        self.toggled_seat.emit(self.seat, self._selected)

    def set_recommended(self, yes: bool):
        if not self.seat["is_available"]:
            return
        if yes and not self._selected:
            self._state = self.STATE_RECOMMENDED
        elif not yes and self._state == self.STATE_RECOMMENDED:
            self._state = self.STATE_AVAILABLE
        self._apply_style()

    def force_select(self, yes: bool):
        if not self.seat["is_available"]:
            return
        self._selected = yes
        self._state = self.STATE_SELECTED if yes else self.STATE_AVAILABLE
        self._apply_style()

    def is_selected(self) -> bool:
        return self._selected

    def _apply_style(self):
        styles = {
            self.STATE_AVAILABLE: (BG_CARD, TEXT_SECONDARY, BORDER),
            self.STATE_SELECTED: (ACCENT, WHITE, ACCENT_HOVER),
            self.STATE_RECOMMENDED: (ACCENT_LIGHT, GOLD, ACCENT),
            self.STATE_BOOKED: ("#D9D9D9", "#888888", "#CCCCCC"),
        }
        bg, fg, border = styles[self._state]
        hover_bg = BG_HOVER if self._state == self.STATE_AVAILABLE else bg
        # No padding in the stylesheet — geometry is fully controlled by setFixedSize.
        # Padding inside a fixed-size button steals from the content area and clips text.
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
            }}
        """)
        self.setEnabled(self.seat["is_available"])


# interactive seat map grid widget


class SeatMapWidget(QWidget):
    """a grid-based widget for visualizing and selecting cinema seats."""

    selection_changed = pyqtSignal(int)  # emits current selected count

    def __init__(self):
        super().__init__()
        self._seat_buttons: List[SeatButton] = []
        self._num_required = 1
        self._recommended_ids: List[int] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING_SM)

        # Header row: count label + recommend button
        header = QHBoxLayout()
        self.count_label = QLabel("Select seats")
        self.count_label.setFont(body_font(10, bold=True))
        self.count_label.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent;")
        header.addWidget(self.count_label)
        header.addStretch()

        self.recommend_btn = secondary_button("Use AI Recommendation")
        self.recommend_btn.setStyleSheet(
            f"QPushButton {{ background-color: {HERO_BG}; color: {WHITE}; border: none; "
            f"min-height: 34px; max-height: 34px; min-width: 180px; font-weight: 700; "
            f"border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: #2E2C28; }}"
        )
        self.recommend_btn.clicked.connect(self._apply_recommendation)
        header.addWidget(self.recommend_btn)
        layout.addLayout(header)

        # AI recommendation feedback banner
        self.ai_banner = QLabel("")
        self.ai_banner.setFont(body_font(9))
        self.ai_banner.setWordWrap(True)
        self.ai_banner.setStyleSheet(f"""
            color: {GOLD};
            background-color: {ACCENT_LIGHT};
            border: 1px solid {ACCENT};
            border-radius: 4px;
            padding: 6px 10px;
        """)
        self.ai_banner.hide()
        layout.addWidget(self.ai_banner)

        # Grid container
        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet("background: transparent;")
        self.grid_layout = QVBoxLayout(self.grid_widget)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(4)
        layout.addWidget(self.grid_widget)

        # map legend for seat states
        legend = QHBoxLayout()
        for color, label in [
            (BG_CARD, "Available"),
            (ACCENT, "Selected"),
            (ACCENT_LIGHT, "AI Pick"),
            (BG_DARKEST, "Booked"),
        ]:
            dot = QLabel("■")
            dot.setFont(body_font(10))
            dot.setStyleSheet(
                f"color: {color if color != BG_DARKEST else '#3A3A3A'}; background: transparent;"
            )
            txt = QLabel(label)
            txt.setFont(body_font(8))
            txt.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
            legend.addWidget(dot)
            legend.addWidget(txt)
            legend.addSpacing(8)
        legend.addStretch()
        layout.addLayout(legend)

    def load(self, seats: List[dict], num_required: int, recommended_ids: List[int]):
        self._num_required = num_required
        self._recommended_ids = recommended_ids
        self._seat_buttons.clear()

        # Clear grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Group by row_label
        rows: Dict[str, List[dict]] = {}
        for seat in seats:
            rows.setdefault(seat["row_label"], []).append(seat)

        # add SCREEN indicator at the top of the map
        screen_wrapper = QWidget()
        screen_wrapper.setStyleSheet("background: transparent;")
        screen_wrapper_layout = QHBoxLayout(screen_wrapper)
        screen_wrapper_layout.setContentsMargins(48, 0, 48, 0)
        screen_wrapper_layout.setSpacing(0)

        screen_frame = QFrame()
        screen_frame.setFixedHeight(28)
        screen_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_DARKEST};
                border: 1.5px solid {BORDER};
                border-radius: 6px;
            }}
        """)
        screen_inner = QHBoxLayout(screen_frame)
        screen_inner.setContentsMargins(0, 0, 0, 0)

        screen_lbl = QLabel("SCREEN")
        screen_lbl.setFont(body_font(8, bold=True))
        screen_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        screen_lbl.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        screen_inner.addWidget(screen_lbl)

        screen_wrapper_layout.addWidget(screen_frame)
        self.grid_layout.addWidget(screen_wrapper)

        # Spacer below screen
        spacer = QWidget()
        spacer.setFixedHeight(16)
        spacer.setStyleSheet("background: transparent;")
        self.grid_layout.addWidget(spacer)

        # Render rows
        sorted_keys = sorted(rows.keys())
        for row_key in sorted_keys:
            row_seats = sorted(
                rows[row_key],
                key=lambda s: int(
                    "".join(c for c in s["seat_number"][len(s["row_label"]) :] if c.isdigit())
                    or "0"
                ),
            )
            row_widget = QWidget()
            row_widget.setStyleSheet("background: transparent;")
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(6)

            # Row label
            lbl = QLabel(row_key)
            lbl.setFixedWidth(34)
            lbl.setFont(body_font(8))
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lbl.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
            row_layout.addWidget(lbl)

            for seat in row_seats:
                btn = SeatButton(seat)
                if seat["seat_id"] in recommended_ids:
                    btn.set_recommended(True)
                btn.toggled_seat.connect(self._on_seat_toggled)
                row_layout.addWidget(btn)
                self._seat_buttons.append(btn)

            row_layout.addStretch()
            self.grid_layout.addWidget(row_widget)

        self._update_count_label()

    def set_ai_banner(self, text: str):
        if text:
            self.ai_banner.setText(text)
            self.ai_banner.show()
        else:
            self.ai_banner.hide()

    def get_selected_seat_ids(self) -> List[int]:
        return [btn.seat["seat_id"] for btn in self._seat_buttons if btn.is_selected()]

    def selected_count(self) -> int:
        return sum(1 for btn in self._seat_buttons if btn.is_selected())

    def _on_seat_toggled(self, seat: dict, selected: bool):
        self._update_count_label()
        self.selection_changed.emit(self.selected_count())

    def _apply_recommendation(self):
        """Deselect all then select the recommended seats."""
        for btn in self._seat_buttons:
            btn.force_select(False)
        rec_set = set(self._recommended_ids)
        for btn in self._seat_buttons:
            if btn.seat["seat_id"] in rec_set:
                btn.force_select(True)
        self._update_count_label()
        self.selection_changed.emit(self.selected_count())

    def _update_count_label(self):
        n = self.selected_count()
        color = (
            SUCCESS
            if n == self._num_required
            else (ACCENT if n > self._num_required else TEXT_SECONDARY)
        )
        self.count_label.setStyleSheet(
            f"color: {color}; background: transparent; font-weight: bold;"
        )
        self.count_label.setText(f"{n} of {self._num_required} seat(s) selected")


# automated staff tips and upselling panel


class UpsellPanel(QFrame):
    """a panel that displays context-aware sales tips to Booking Staff."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"""
            UpsellPanel {{
                background-color: {HERO_BG};
                border: 1px solid {BORDER};
                border-radius: {RADIUS};
            }}
        """)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(12, 10, 12, 10)
        self._layout.setSpacing(6)

        header = QLabel("STAFF TIPS")
        header.setFont(body_font(8, bold=True))
        header.setStyleSheet(f"color: {GOLD}; background: transparent;")
        self._layout.addWidget(header)
        self.hide()

    def set_tips(self, tips: List[str]):
        # Remove old tips (keep header)
        while self._layout.count() > 1:
            item = self._layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        for tip in tips:
            lbl = QLabel(f"\u2022 {tip}")
            lbl.setFont(body_font(9))
            lbl.setWordWrap(True)
            lbl.setStyleSheet(f"color: {WHITE}; background: transparent;")
            self._layout.addWidget(lbl)

        if tips:
            self.show()
        else:
            self.hide()


# booking confirmation modal


class ConfirmBookingDialog(QDialog):
    """a modal dialog for reviewing booking details before final commitment."""

    def __init__(self, parent, summary: dict):
        super().__init__(parent)
        self.setWindowTitle("Confirm Booking")
        self.setMinimumWidth(380)
        self.setStyleSheet(f"background-color: {BG_CARD}; color: {TEXT_PRIMARY};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("Confirm this booking?")
        title.setFont(heading_font(13))
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(title)

        layout.addWidget(separator())

        rows = [
            ("Film", summary.get("film", "")),
            ("Date", summary.get("date", "")),
            ("Time", summary.get("time", "")),
            ("Seat Type", summary.get("seat_type", "").replace("_", " ").title()),
            ("Seats Selected", summary.get("seats_label", "")),
            ("Customer", summary.get("customer", "")),
        ]
        for label, value in rows:
            layout.addLayout(labelled_value(label, value))

        layout.addWidget(separator())

        total_lbl = QLabel(f"Total: £{summary.get('total', 0):.2f}")
        total_lbl.setFont(heading_font(15))
        total_lbl.setStyleSheet(f"color: {ACCENT}; background: transparent;")
        layout.addWidget(total_lbl)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Confirm & Book")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


# primary New Booking view implementation


class NewBookingView(QWidget):
    """the central view for processing new customer bookings and payments."""

    def __init__(self):
        super().__init__()
        self._showings_data = []
        self._availability: Optional[dict] = None
        self._last_booking: Optional[dict] = None
        self._seat_map_data: Optional[List[dict]] = None
        self._build_ui()
        self._load_cinemas()

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        self.main_layout = QVBoxLayout(content)
        self.main_layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        self.main_layout.setSpacing(SPACING_MD)

        # view header with title and service description
        header_content = QVBoxLayout()
        header_content.setSpacing(4)
        header_content.addWidget(heading_label("New Booking"))
        desc = muted_label(
            "Create and process new customer reservations with real-time seat selection"
        )
        header_content.addWidget(desc)
        self.main_layout.addLayout(header_content)

        columns = QHBoxLayout()
        columns.setSpacing(SPACING_LG)

        # left column: booking parameters and seat selection
        left = QVBoxLayout()
        left.setSpacing(SPACING_MD)

        # cinema and film selection controls
        select_card = Card()
        self.cinema_combo = QComboBox()
        self.cinema_combo.currentIndexChanged.connect(self._on_cinema_changed)
        select_card.add_layout(form_row("Cinema", self.cinema_combo))

        self.film_combo = QComboBox()
        self.film_combo.currentIndexChanged.connect(self._on_film_changed)
        select_card.add_layout(form_row("Film", self.film_combo))

        self.showing_combo = QComboBox()
        self.showing_combo.currentIndexChanged.connect(self._reset_seat_map)
        select_card.add_layout(form_row("Showing", self.showing_combo))

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setMinimumDate(QDate.currentDate())
        self.date_edit.setMaximumDate(QDate.currentDate().addDays(7))
        self.date_edit.dateChanged.connect(self._reset_seat_map)
        select_card.add_layout(form_row("Date", self.date_edit))
        left.addWidget(select_card)

        # seat type selection and availability checks
        ticket_card = Card()
        type_group_layout = QHBoxLayout()
        self.seat_type_group = QButtonGroup(self)
        self.rb_lower = QRadioButton("Lower Hall")
        self.rb_upper = QRadioButton("Upper Gallery")
        self.rb_vip = QRadioButton("VIP")
        self.rb_lower.setChecked(True)
        for rb in (self.rb_lower, self.rb_upper, self.rb_vip):
            rb.toggled.connect(self._reset_seat_map)
        self.seat_type_group.addButton(self.rb_lower, 0)
        self.seat_type_group.addButton(self.rb_upper, 1)
        self.seat_type_group.addButton(self.rb_vip, 2)
        st_lbl = QLabel("Seat Type:")
        st_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        type_group_layout.addWidget(st_lbl)
        type_group_layout.addWidget(self.rb_lower)
        type_group_layout.addWidget(self.rb_upper)
        type_group_layout.addWidget(self.rb_vip)
        type_group_layout.addStretch()
        ticket_card.add_layout(type_group_layout)

        self.num_tickets = QSpinBox()
        self.num_tickets.setMinimum(1)
        self.num_tickets.setMaximum(20)
        self.num_tickets.setValue(1)
        self.num_tickets.valueChanged.connect(self._reset_seat_map)
        ticket_card.add_layout(form_row("Tickets", self.num_tickets))

        self.check_btn = primary_button("Check Availability & Price")
        self.check_btn.setStyleSheet(
            f"QPushButton {{ background-color: {ACCENT}; color: {WHITE}; border: none; "
            f"min-height: 34px; max-height: 34px; min-width: 200px; font-weight: 700; "
            f"border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}"
        )
        self.check_btn.clicked.connect(self._check_availability)
        ticket_card.add(self.check_btn)

        self.avail_label = QLabel("")
        self.avail_label.setFont(body_font(11))
        self.avail_label.setWordWrap(True)
        self.avail_label.hide()
        ticket_card.add(self.avail_label)
        left.addWidget(ticket_card)

        # AI-driven upsell tips panel
        self.upsell_panel = UpsellPanel()
        left.addWidget(self.upsell_panel)

        # interactive seat map container
        self.seat_map_card = Card()
        seat_map_title = subheading_label("Seat Map", 11)
        self.seat_map_card.add(seat_map_title)
        self.seat_map_widget = SeatMapWidget()
        self.seat_map_widget.selection_changed.connect(self._on_selection_changed)
        self.seat_map_card.add(self.seat_map_widget)
        self.seat_map_card.hide()
        left.addWidget(self.seat_map_card)

        # customer contact and registration details
        customer_card = Card()
        customer_card.add(subheading_label("Customer Details", 12))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Full name")
        customer_card.add_layout(form_row("Name *", self.name_input))
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone number")
        customer_card.add_layout(form_row("Phone", self.phone_input))
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email address")
        customer_card.add_layout(form_row("Email", self.email_input))
        customer_card.add(separator())

        pay_lbl = QLabel("Simulate payment (card details not stored)")
        pay_lbl.setFont(body_font(9))
        pay_lbl.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        customer_card.add(pay_lbl)

        btn_row = QHBoxLayout()
        self.book_btn = primary_button("Confirm Booking")
        self.book_btn.setStyleSheet(
            f"QPushButton {{ background-color: {ACCENT}; color: {WHITE}; border: none; "
            f"min-height: 34px; max-height: 34px; min-width: 160px; font-weight: 700; "
            f"border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}"
            f"QPushButton:disabled {{ background-color: {BG_DARKEST}; color: {TEXT_MUTED}; }}"
        )
        self.book_btn.setEnabled(False)
        self.book_btn.clicked.connect(self._confirm_booking)
        btn_row.addWidget(self.book_btn)

        self.reset_btn = secondary_button("Reset")
        self.reset_btn.setStyleSheet(
            f"QPushButton {{ background-color: {HERO_BG}; color: {WHITE}; border: none; "
            f"min-height: 34px; max-height: 34px; min-width: 100px; font-weight: 700; "
            f"border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: #2E2C28; }}"
        )
        self.reset_btn.clicked.connect(self._reset_form)
        btn_row.addWidget(self.reset_btn)
        btn_row.addStretch()
        customer_card.add_layout(btn_row)
        left.addWidget(customer_card)
        left.addStretch()

        # right column: booking receipt and post-booking actions
        right = QVBoxLayout()
        right.setSpacing(SPACING_MD)

        receipt_title = subheading_label("Booking Receipt", 13)
        right.addWidget(receipt_title)

        self.receipt_card = Card()
        self.receipt_placeholder = muted_label("Receipt will appear here after booking.")
        self.receipt_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.receipt_placeholder.setMinimumHeight(200)
        self.receipt_card.add(self.receipt_placeholder)
        right.addWidget(self.receipt_card)

        # receipt management buttons (print and clipboard)
        receipt_btns = QHBoxLayout()
        self.print_btn = primary_button("Print Receipt")
        self.print_btn.setStyleSheet(
            f"QPushButton {{ background-color: {ACCENT}; color: {WHITE}; border: none; "
            f"min-height: 34px; max-height: 34px; min-width: 140px; font-weight: 700; "
            f"border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}"
        )
        self.print_btn.clicked.connect(self._print_receipt)
        self.print_btn.hide()
        receipt_btns.addWidget(self.print_btn)

        self.copy_btn = secondary_button("Copy to Clipboard")
        self.copy_btn.setStyleSheet(
            f"QPushButton {{ background-color: {HERO_BG}; color: {WHITE}; border: none; "
            f"min-height: 34px; max-height: 34px; min-width: 160px; font-weight: 700; "
            f"border-radius: 6px; }}"
            f"QPushButton:hover {{ background-color: #2E2C28; }}"
        )
        self.copy_btn.clicked.connect(self._copy_receipt)
        self.copy_btn.hide()
        receipt_btns.addWidget(self.copy_btn)
        receipt_btns.addStretch()
        right.addLayout(receipt_btns)
        right.addStretch()

        columns.addLayout(left, 3)
        columns.addLayout(right, 2)
        self.main_layout.addLayout(columns)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(content)
        outer.addWidget(scroll)

    # api data retrieval methods

    def _load_cinemas(self):
        try:
            cinemas = api.get_cinemas()
            self.cinema_combo.blockSignals(True)
            self.cinema_combo.clear()
            if api.role == "booking_staff":
                cinemas = [c for c in cinemas if c["cinema_id"] == api.cinema_id]
            for c in cinemas:
                label = c["cinema_name"]
                if c.get("city_name"):
                    label += f"  \u2014  {c['city_name']}"
                self.cinema_combo.addItem(label, c["cinema_id"])
            self.cinema_combo.blockSignals(False)
            self._on_cinema_changed()
        except Exception as e:
            error_dialog(self, f"Failed to load cinemas: {e}")

    def _on_cinema_changed(self):
        cinema_id = self.cinema_combo.currentData()
        if not cinema_id:
            return
        target = self.date_edit.date().toPyDate().isoformat()
        try:
            listings = api.get_film_listings(cinema_id, target)
            self.film_combo.blockSignals(True)
            self.film_combo.clear()
            self._showings_data = []
            for item in listings:
                self.film_combo.addItem(f"{item['title']}  (Screen {item['screen_number']})", item)
            self.film_combo.blockSignals(False)
            self._on_film_changed()
        except Exception as e:
            error_dialog(self, f"Failed to load films: {e}")

    def _on_film_changed(self):
        self.showing_combo.clear()
        idx = self.film_combo.currentIndex()
        if idx < 0:
            return
        film_data = self.film_combo.itemData(idx)
        if not film_data:
            return
        self._showings_data = film_data.get("showings", [])
        for s in self._showings_data:
            t = s["show_time"]
            if isinstance(t, str) and len(t) > 5:
                t = t[:5]
            label = (
                f"{t}  ({s['show_type'].capitalize()})  \u2014  "
                f"from \u00a3{s['lower_hall_price']:.2f}"
            )
            self.showing_combo.addItem(label, s)
        self._reset_seat_map()

    # Availability

    def _get_seat_type(self) -> str:
        return ["lower_hall", "upper_gallery", "vip"][self.seat_type_group.checkedId()]

    def _reset_seat_map(self):
        """Hide seat map and disable confirm whenever selection changes."""
        self._availability = None
        self._seat_map_data = None
        self.seat_map_card.hide()
        self.upsell_panel.hide()
        self.book_btn.setEnabled(False)
        self.avail_label.hide()

    def _check_availability(self):
        showing_idx = self.showing_combo.currentIndex()
        if showing_idx < 0 or not self._showings_data:
            error_dialog(self, "Please select a film and showing first.")
            return
        showing = self.showing_combo.itemData(showing_idx)
        if not showing:
            return

        data = {
            "showing_id": showing["showing_id"],
            "show_date": self.date_edit.date().toPyDate().isoformat(),
            "seat_type": self._get_seat_type(),
            "num_tickets": self.num_tickets.value(),
        }

        try:
            result = api.check_availability(data)
            self._availability = result
            available = result["available"]
            seats = result["seats_available"]
            total_seats = result["seats_total"]
            unit = result["unit_price"]
            total = result["total_price"]
            seat_type_label = result["seat_type"].replace("_", " ").title()

            if available:
                summary_text = (
                    f"{seats}/{total_seats} {seat_type_label} seats available\n"
                    f"Unit price: \u00a3{unit:.2f}  \u00d7  {self.num_tickets.value()} tickets"
                    f"  =  \u00a3{total:.2f}"
                )
                self.avail_label.setText(summary_text)
                self.avail_label.setStyleSheet(
                    f"color: {SUCCESS}; background: transparent; padding: 8px;"
                )
                # Load seat map and upsell
                self._load_seat_map(showing["showing_id"], data["show_date"], data["seat_type"])
                tips = _build_upsell_tips(result)
                self.upsell_panel.set_tips(tips)
            else:
                self.avail_label.setText(
                    f"\u2717  Only {seats} {seat_type_label} seat(s) available "
                    f"(requested {self.num_tickets.value()})"
                )
                self.avail_label.setStyleSheet(
                    f"color: {ACCENT}; background: transparent; padding: 8px;"
                )
                self.seat_map_card.hide()
                self.upsell_panel.hide()
                self.book_btn.setEnabled(False)

            self.avail_label.show()

        except Exception as e:
            detail = str(e)
            if hasattr(e, "response"):
                try:
                    detail = e.response.json().get("detail", detail)
                except Exception:
                    pass
            error_dialog(self, detail)

    def _load_seat_map(self, showing_id: int, show_date: str, seat_type: str):
        try:
            result = api.get_seat_map(showing_id, show_date, seat_type)
            seats = result["seats"]
            self._seat_map_data = seats
            num = self.num_tickets.value()

            recommended = _recommend_seats(seats, num)
            rec_ids = [s["seat_id"] for s in recommended]

            self.seat_map_widget.load(seats, num, rec_ids)

            if recommended:
                names = ", ".join(s["seat_number"] for s in recommended)
                row = recommended[0]["row_label"]
                self.seat_map_widget.set_ai_banner(
                    f"AI Recommendation: {names} - best centre-view seats for your group of {num}"
                )
            else:
                self.seat_map_widget.set_ai_banner("")

            self.seat_map_card.show()
            self.book_btn.setEnabled(False)  # must select seats first

        except Exception:
            # Seat map is optional — if it fails, fall back to auto-assign
            self.seat_map_card.hide()
            self.book_btn.setEnabled(True)

    def _on_selection_changed(self, count: int):
        required = self.num_tickets.value()
        self.book_btn.setEnabled(count == required and self._availability is not None)

    # Confirm booking

    def _confirm_booking(self):
        name = self.name_input.text().strip()
        if not name:
            error_dialog(self, "Customer name is required.")
            return

        showing_idx = self.showing_combo.currentIndex()
        showing = self.showing_combo.itemData(showing_idx)
        if not showing:
            return

        avail = self._availability or {}
        selected_ids = self.seat_map_widget.get_selected_seat_ids()
        num = self.num_tickets.value()
        seat_type = self._get_seat_type()
        total = avail.get("total_price", 0.0)

        # Build confirmation summary
        t = str(showing.get("show_time", ""))
        if len(t) > 5:
            t = t[:5]
        film_idx = self.film_combo.currentIndex()
        film_data = self.film_combo.itemData(film_idx) or {}
        film_title = film_data.get("title", "")

        seats_label = (
            ", ".join(
                next(
                    (s["seat_number"] for s in (self._seat_map_data or []) if s["seat_id"] == sid),
                    str(sid),
                )
                for sid in selected_ids
            )
            if selected_ids
            else f"{num} auto-assigned"
        )

        summary = {
            "film": film_title,
            "date": self.date_edit.date().toPyDate().isoformat(),
            "time": t,
            "seat_type": seat_type,
            "seats_label": seats_label,
            "customer": name,
            "total": total,
        }

        dlg = ConfirmBookingDialog(self, summary)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        self._create_booking(showing, name, seat_type, num, selected_ids)

    def _create_booking(
        self, showing: dict, name: str, seat_type: str, num: int, seat_ids: List[int]
    ):
        data = {
            "showing_id": showing["showing_id"],
            "show_date": self.date_edit.date().toPyDate().isoformat(),
            "customer_name": name,
            "customer_phone": self.phone_input.text().strip() or None,
            "customer_email": self.email_input.text().strip() or None,
            "seat_type": seat_type,
            "num_tickets": num,
            "payment_simulated": True,
        }
        if seat_ids:
            data["seat_ids"] = seat_ids

        self.book_btn.setEnabled(False)
        self.book_btn.setText("Processing\u2026")

        try:
            booking = api.create_booking(data)
            self._last_booking = booking
            self._show_receipt(booking)
            show_toast(self, f"Booking {booking['booking_reference']} confirmed!", success=True)
        except Exception as e:
            detail = str(e)
            if hasattr(e, "response"):
                try:
                    detail = e.response.json().get("detail", detail)
                except Exception:
                    pass
            error_dialog(self, detail)
        finally:
            self.book_btn.setEnabled(True)
            self.book_btn.setText("Confirm Booking")

    # Receipt

    def _show_receipt(self, booking: dict):
        while self.receipt_card._layout.count():
            item = self.receipt_card._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.receipt_card.add(subheading_label("Booking Confirmed", 13))
        self.receipt_card.add(status_badge(booking["booking_status"]))
        self.receipt_card.add(separator())

        fields = [
            ("Reference", booking["booking_reference"]),
            ("Film", booking.get("film_title", "")),
            ("Date", str(booking["show_date"])),
            ("Time", str(booking.get("show_time", ""))[:5]),
            ("Screen", str(booking.get("screen_number", ""))),
            ("Cinema", booking.get("cinema_name", "")),
            ("Customer", booking["customer_name"]),
            ("Tickets", str(booking["num_tickets"])),
        ]
        for label, value in fields:
            self.receipt_card.add_layout(labelled_value(label, value))

        seats = booking.get("booked_seats", [])
        if seats:
            seat_nums = ", ".join(s["seat_number"] for s in seats)
            seat_type = seats[0]["seat_type"].replace("_", " ").title()
            self.receipt_card.add_layout(labelled_value("Seats", seat_nums))
            self.receipt_card.add_layout(labelled_value("Seat Type", seat_type))

        self.receipt_card.add(separator())

        total_lbl = QLabel(f"Total: \u00a3{booking['total_cost']:.2f}")
        total_lbl.setFont(heading_font(16))
        total_lbl.setStyleSheet(f"color: {ACCENT}; background: transparent;")
        self.receipt_card.add(total_lbl)

        booking_date = booking.get("booking_date", "")
        if booking_date:
            self.receipt_card.add(muted_label(f"Booked: {str(booking_date)[:19]}"))

        self.print_btn.show()
        self.copy_btn.show()

    def _receipt_text(self) -> str:
        b = self._last_booking
        if not b:
            return ""
        seats = b.get("booked_seats", [])
        seat_str = ", ".join(s["seat_number"] for s in seats) if seats else "N/A"
        seat_type = seats[0]["seat_type"].replace("_", " ").title() if seats else "N/A"
        return (
            "═══════════════════════════════════════\n"
            "        HORIZON CINEMAS — RECEIPT      \n"
            "═══════════════════════════════════════\n"
            f"  Reference:  {b['booking_reference']}\n"
            f"  Status:     {b['booking_status'].capitalize()}\n"
            f"  Film:       {b.get('film_title', '')}\n"
            f"  Date:       {b['show_date']}\n"
            f"  Time:       {str(b.get('show_time', ''))[:5]}\n"
            f"  Screen:     {b.get('screen_number', '')}\n"
            f"  Cinema:     {b.get('cinema_name', '')}\n"
            f"  Customer:   {b['customer_name']}\n"
            f"  Tickets:    {b['num_tickets']}\n"
            f"  Seats:      {seat_str}\n"
            f"  Seat Type:  {seat_type}\n"
            "───────────────────────────────────────\n"
            f"  TOTAL:      \u00a3{b['total_cost']:.2f}\n"
            "═══════════════════════════════════════\n"
        )

    def _print_receipt(self):
        text = self._receipt_text()
        if not text:
            return
        try:
            from PyQt6.QtGui import QTextDocument  # type: ignore
            from PyQt6.QtPrintSupport import QPrintDialog, QPrinter  # type: ignore

            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            dialog = QPrintDialog(printer, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                doc = QTextDocument()
                doc.setPlainText(text)
                doc.print_(printer)
                show_toast(self, "Receipt sent to printer!", success=True)
        except Exception:
            # Fallback: copy to clipboard if printing unavailable
            QApplication.clipboard().setText(text)
            show_toast(self, "Print unavailable — receipt copied to clipboard.", success=False)

    def _copy_receipt(self):
        text = self._receipt_text()
        if not text:
            return
        QApplication.clipboard().setText(text)
        show_toast(self, "Receipt copied to clipboard!", success=True)

    # Reset

    def _reset_form(self):
        self.name_input.clear()
        self.phone_input.clear()
        self.email_input.clear()
        self.num_tickets.setValue(1)
        self.rb_lower.setChecked(True)
        self.avail_label.hide()
        self.book_btn.setEnabled(False)
        self._availability = None
        self._last_booking = None
        self._seat_map_data = None
        self.seat_map_card.hide()
        self.upsell_panel.hide()
        self.print_btn.hide()
        self.copy_btn.hide()

        while self.receipt_card._layout.count():
            item = self.receipt_card._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        self.receipt_placeholder = muted_label("Receipt will appear here after booking.")
        self.receipt_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.receipt_placeholder.setMinimumHeight(200)
        self.receipt_card.add(self.receipt_placeholder)
