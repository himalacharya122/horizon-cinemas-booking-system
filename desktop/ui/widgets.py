# ============================================
# Author: Himal Acharya
# Student ID: 22085619
# Last Edited: 2026-04-25
# ============================================

"""
desktop/ui/widgets.py
reusable UI components including buttons, cards, form rows, badges, and toast messages for the Horizon Cinemas theme.
"""

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from desktop.ui.theme import (
    ACCENT,
    ACCENT_HOVER,
    BG_CARD,
    BORDER,
    DANGER,
    RADIUS,
    SPACING_MD,
    SPACING_SM,
    SUCCESS,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WHITE,
    body_font,
    heading_font,
)

# button components


def primary_button(text: str, icon_text: str = "") -> QPushButton:
    """creates a primary action button with Horizon Red styling."""
    btn = QPushButton(f"  {icon_text}  {text}  " if icon_text else text)
    btn.setProperty("primary", True)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet(btn.styleSheet())  # force property re-evaluation
    return btn


def secondary_button(text: str) -> QPushButton:
    """creates a subtle secondary action button."""
    btn = QPushButton(text)
    btn.setProperty("secondary", True)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


def danger_button(text: str) -> QPushButton:
    """creates a high-visibility button for destructive actions."""
    btn = QPushButton(text)
    btn.setProperty("danger", True)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


# label components


def heading_label(text: str, size: int = 18) -> QLabel:
    """returns a large QLabel styled as a main heading."""
    lbl = QLabel(text)
    lbl.setProperty("heading", True)
    lbl.setFont(heading_font(size))
    lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent;")
    return lbl


def subheading_label(text: str, size: int = 13) -> QLabel:
    """returns a bold QLabel styled as a section subheading."""
    lbl = QLabel(text)
    lbl.setProperty("subheading", True)
    lbl.setFont(heading_font(size, bold=True))
    lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent;")
    return lbl


def muted_label(text: str) -> QLabel:
    """returns a smaller QLabel with secondary text colouring."""
    lbl = QLabel(text)
    lbl.setProperty("muted", True)
    lbl.setFont(body_font(10))
    lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
    return lbl


def badge_label(text: str, colour: str = ACCENT) -> QLabel:
    """creates a small coloured tag or badge for status indicators."""
    lbl = QLabel(f"  {text}  ")
    lbl.setFont(body_font(9))
    lbl.setStyleSheet(
        f"background-color: {colour}; color: {WHITE}; "
        f"border-radius: 4px; padding: 4px 8px; font-weight: 600;"
    )
    lbl.setFixedHeight(26)
    return lbl


def status_badge(status: str) -> QLabel:
    """specialised badge for booking status: confirmed (SUCCESS) or cancelled (DANGER)."""
    colour = SUCCESS if status == "confirmed" else DANGER
    return badge_label(status.capitalize(), colour)


# card containers


class Card(QFrame):
    """a rounded container with a subtle border for grouping UI elements."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            f"Card {{ background: {BG_CARD}; border: 1px solid {BORDER}; "
            f"border-radius: {RADIUS}; }}"
        )
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        self._layout.setSpacing(SPACING_SM)

    def add(self, widget):
        """adds a widget to the card layout."""
        self._layout.addWidget(widget)
        return widget

    def add_layout(self, layout):
        """adds a nested layout to the card."""
        self._layout.addLayout(layout)
        return layout


# form layout helpers


def form_row(label_text: str, widget: QWidget, stretch: bool = True) -> QHBoxLayout:
    """creates a standard row with a fixed-width QLabel on the left and a widget on the right."""
    row = QHBoxLayout()
    lbl = QLabel(label_text)
    lbl.setFont(body_font(11))
    lbl.setFixedWidth(140)
    lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent; font-weight: 500;")
    row.addWidget(lbl)
    if stretch:
        row.addWidget(widget, 1)
    else:
        row.addWidget(widget)
    return row


def labelled_value(label: str, value: str) -> QHBoxLayout:
    """displays a read-only label and value pair, often used for details or receipts."""
    row = QHBoxLayout()
    lbl = QLabel(label)
    lbl.setFont(body_font(10))
    lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent; font-weight: 500;")
    lbl.setFixedWidth(130)
    val = QLabel(value)
    val.setFont(body_font(11))
    val.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent;")
    val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    row.addWidget(lbl)
    row.addWidget(val, 1)
    return row


# visual separator


def separator() -> QFrame:
    """returns a clean horizontal line to divide sections."""
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Plain)
    line.setStyleSheet(f"background-color: {BORDER}; max-height: 1px; border: none;")
    return line


# toast notifications


class Toast(QLabel):
    """temporary notification that slides and fades out after a duration."""

    def __init__(self, parent, message: str, colour: str = TEXT_PRIMARY, duration: int = 3000):
        super().__init__(message, parent)
        self.setFont(body_font(10))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            f"background-color: {colour}; color: {WHITE}; "
            f"border-radius: {RADIUS}; padding: 10px 24px; font-weight: 500;"
        )
        self.setFixedHeight(44)
        self.adjustSize()
        self.setMinimumWidth(300)

        # position at bottom centre of parent window
        px = (parent.width() - self.width()) // 2
        py = parent.height() - 80
        self.move(px, py)
        self.show()

        # setup opacity effect for fading
        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        self._effect.setOpacity(1.0)

        QTimer.singleShot(duration, self._fade_out)

    def _fade_out(self):
        """starts the fade-out animation and deletes the widget upon completion."""
        self._anim = QPropertyAnimation(self._effect, b"opacity")
        self._anim.setDuration(400)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.finished.connect(self.deleteLater)
        self._anim.start()


def show_toast(parent, message: str, success: bool = True, duration: int = 3000):
    """helper function to instantiate a Toast notification."""
    colour = SUCCESS if success else DANGER
    Toast(parent, message, colour, duration)


# modal dialogs


def _style_dialog(msg_box: QMessageBox):
    """applies custom styling to QMessageBox to match the application theme."""
    from PyQt6.QtWidgets import QDialogButtonBox  # type: ignore

    # sizing is driven by stylesheets to prevent layout clipping
    msg_box.setStyleSheet(
        f"QMessageBox {{"
        f"  background-color: {WHITE};"
        f"}}"
        f"QMessageBox QDialogButtonBox {{"
        f"  padding: 8px 0px 16px 0px;"
        f"}}"
        f"QMessageBox QPushButton {{"
        f"  min-height: 34px;"
        f"  min-width: 110px;"
        f"  padding: 6px 16px;"
        f"  border-radius: 6px;"
        f"  font-weight: 700;"
        f"  font-family: 'Manrope';"
        f"  font-size: 10pt;"
        f"  border: none;"
        f"}}"
    )

    bbox = msg_box.findChild(QDialogButtonBox)
    if bbox:
        bbox.setCenterButtons(True)

    # button-specific styling based on action type
    for btn in msg_box.findChildren(QPushButton):
        text = btn.text().lower()
        btn.setCursor(Qt.CursorShape.PointingHandCursor)

        if any(keyword in text for keyword in ["yes", "ok", "save", "confirm"]):
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {ACCENT}; color: {WHITE}; }}"
                f"QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}"
            )
        else:
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {TEXT_SECONDARY}; color: {WHITE}; }}"
                f"QPushButton:hover {{ background-color: #4A4A48; }}"
            )


def confirm_dialog(parent, title: str, message: str) -> bool:
    """shows a confirmation dialog with Yes/No options."""
    msg = QMessageBox(parent)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setIcon(QMessageBox.Icon.Question)
    msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    msg.setDefaultButton(QMessageBox.StandardButton.No)
    _style_dialog(msg)
    return msg.exec() == QMessageBox.StandardButton.Yes


def error_dialog(parent, message: str, title: str = "Error"):
    """displays an error message in a styled modal."""
    msg = QMessageBox(parent)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    _style_dialog(msg)
    msg.exec()


def info_dialog(parent, message: str, title: str = "Information"):
    """displays informational text in a styled modal."""
    msg = QMessageBox(parent)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setIcon(QMessageBox.Icon.Information)
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    _style_dialog(msg)
    msg.exec()
