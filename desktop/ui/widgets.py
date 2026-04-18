"""
desktop/ui/widgets.py
Reusable UI components: buttons, cards, form rows, badges, toast messages.
Dark cinema theme.
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

# Buttons


def primary_button(text: str, icon_text: str = "") -> QPushButton:
    btn = QPushButton(f"  {icon_text}  {text}  " if icon_text else text)
    btn.setProperty("primary", True)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet(btn.styleSheet())  # force property re-eval
    return btn


def secondary_button(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setProperty("secondary", True)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


def danger_button(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setProperty("danger", True)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


# Labels


def heading_label(text: str, size: int = 18) -> QLabel:
    lbl = QLabel(text)
    lbl.setProperty("heading", True)
    lbl.setFont(heading_font(size))
    lbl.setStyleSheet(f"color: {WHITE}; background: transparent;")
    return lbl


def subheading_label(text: str, size: int = 13) -> QLabel:
    lbl = QLabel(text)
    lbl.setProperty("subheading", True)
    lbl.setFont(heading_font(size, bold=True))
    lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent;")
    return lbl


def muted_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setProperty("muted", True)
    lbl.setFont(body_font(10))
    lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
    return lbl


def badge_label(text: str, colour: str = ACCENT) -> QLabel:
    """Small coloured tag/badge."""
    lbl = QLabel(f"  {text}  ")
    lbl.setFont(body_font(9))
    lbl.setStyleSheet(
        f"background-color: {colour}; color: {WHITE}; "
        f"border-radius: 4px; padding: 2px 8px; font-weight: 600;"
    )
    lbl.setFixedHeight(22)
    return lbl


def status_badge(status: str) -> QLabel:
    """Booking status badge — confirmed (teal) or cancelled (coral)."""
    colour = SUCCESS if status == "confirmed" else DANGER
    return badge_label(status.capitalize(), colour)


# Cards


class Card(QFrame):
    """A dark bordered card container with rounded corners."""

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
        self._layout.addWidget(widget)
        return widget

    def add_layout(self, layout):
        self._layout.addLayout(layout)
        return layout


# Form helpers


def form_row(label_text: str, widget: QWidget, stretch: bool = True) -> QHBoxLayout:
    """Standard form row: label on left, widget on right."""
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
    """Read-only label: value pair (for receipts, details, etc.)."""
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


# Separator


def separator() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet(f"background-color: {BORDER}; max-height: 1px;")
    return line


# Toast notification


class Toast(QLabel):
    """Temporary notification that fades out automatically."""

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

        # Position at bottom centre of parent
        px = (parent.width() - self.width()) // 2
        py = parent.height() - 80
        self.move(px, py)
        self.show()

        # Fade out
        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        self._effect.setOpacity(1.0)

        QTimer.singleShot(duration, self._fade_out)

    def _fade_out(self):
        self._anim = QPropertyAnimation(self._effect, b"opacity")
        self._anim.setDuration(400)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.finished.connect(self.deleteLater)
        self._anim.start()


def show_toast(parent, message: str, success: bool = True, duration: int = 3000):
    colour = SUCCESS if success else DANGER
    Toast(parent, message, colour, duration)


# Message boxes


def confirm_dialog(parent, title: str, message: str) -> bool:
    reply = QMessageBox.question(
        parent,
        title,
        message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return reply == QMessageBox.StandardButton.Yes


def error_dialog(parent, message: str, title: str = "Error"):
    QMessageBox.critical(parent, title, message)


def info_dialog(parent, message: str, title: str = "Information"):
    QMessageBox.information(parent, title, message)
