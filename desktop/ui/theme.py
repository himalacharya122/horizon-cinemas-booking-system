# ============================================
# Author: Himal Acharya
# Student ID: 22085619
# Last Edited: 2026-04-25
# ============================================

"""
desktop/ui/theme.py
Horizon Cinemas — light theme with red accent.

Palette (from design system):
  Backgrounds  — off-white / light grey  (#FAFAF9 → #FFFFFF)
  Text         — near-black / dark grey  (#0A0908 → #6E6C68)
  Accent       — Horizon red (#B91C1C)
  Hero         — ink-900 (#0A0908) for dark brand panels
  Gold         — #C8A04A (highlights)
  Success      — #10B981
  Danger       — #EF4444

Fonts:
  Manrope -> headings, brand, all body text
"""

from pathlib import Path

from PyQt6.QtGui import QFont, QFontDatabase  # type: ignore

# background colours
BG_DARKEST = "#FAFAF9"  # primary window background
BG_DARK = "#F1F1EF"  # sidebar and panel backgrounds
BG_CARD = "#FFFFFF"  # card surface background
BG_INPUT = "#FAFAF9"  # input field background
BG_HOVER = "#F1F1EF"  # state for hovered elements

# border colours
BORDER = "#E4E3E0"  # standard border colour
BORDER_LIGHT = "#F1F1EF"  # subtle or inner borders

# text colours
TEXT_PRIMARY = "#0A0908"  # main text and headings
TEXT_SECONDARY = "#2E2C28"  # labels and secondary copy
TEXT_MUTED = "#6E6C68"  # placeholders and caption text

# branding accent (Horizon Red)
ACCENT = "#B91C1C"  # main brand red
ACCENT_HOVER = "#991B1B"  # hover state for accent buttons
ACCENT_LIGHT = "#FEF2F2"  # subtle background tint

# hero panels (dark branding sections)
HERO_BG = "#0A0908"  # dark background for login and navigation
HERO_FG = "#FFFFFF"  # contrasting text for hero sections

# functional status colours
GOLD = "#C8A04A"  # premium highlights or gold badges
SUCCESS = "#10B981"  # indicators for confirmed or positive actions
DANGER = "#EF4444"  # error messages or destructive actions
DANGER_HOVER = "#DC2626"  # hover state for danger buttons

# legacy aliases for backward compatibility
WHITE = "#FFFFFF"
SNOW = BG_CARD
SILVER = BORDER
SMOKE = TEXT_SECONDARY
SLATE = TEXT_MUTED
CHARCOAL = TEXT_PRIMARY
BLACK = "#0A0908"
ACCENT_LIGHT_LEGACY = ACCENT_LIGHT

# resource loading
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
ARROW_SVG = (ASSETS_DIR / "dropdown_arrow.svg").as_posix()
UP_ARROW_SVG = (ASSETS_DIR / "up_arrow.svg").as_posix()

_fonts_loaded = False


def load_fonts():
    """loads the Manrope font family from the local assets directory."""
    global _fonts_loaded
    if _fonts_loaded:
        return
    _fonts_loaded = True
    fonts_dir = ASSETS_DIR / "fonts"
    if not fonts_dir.exists():
        return
    for font_file in fonts_dir.rglob("*"):
        if font_file.suffix.lower() in (".ttf", ".otf"):
            QFontDatabase.addApplicationFont(str(font_file))


def heading_font(size: int = 16, bold: bool = True) -> QFont:
    """returns a QFont using the Manrope family, suitable for headings."""
    f = QFont("Manrope", size)
    if bold:
        f.setBold(True)
    return f


def body_font(size: int = 11, bold: bool = False) -> QFont:
    """returns a QFont using the Manrope family, suitable for body text and labels."""
    f = QFont("Manrope", size)
    if bold:
        f.setBold(True)
    return f


# layout spacing and element sizing
RADIUS = "8px"
RADIUS_LG = "12px"
SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 16
SPACING_LG = 24
SPACING_XL = 32

INPUT_HEIGHT = "38px"
BTN_HEIGHT = "40px"

# global QSS style sheet for the light cinema theme
GLOBAL_QSS = f"""
/* Base */
QMainWindow, QDialog {{
    background-color: {BG_DARKEST};
    color: {TEXT_PRIMARY};
    font-family: "Manrope", "Segoe UI", "Helvetica Neue", sans-serif;
    font-size: 11pt;
}}

QWidget {{
    color: {TEXT_PRIMARY};
    font-family: "Manrope", "Segoe UI", "Helvetica Neue", sans-serif;
    font-size: 11pt;
}}

/* Labels */
QLabel {{
    color: {TEXT_PRIMARY};
    background: transparent;
}}

QLabel[heading="true"] {{
    font-family: "Manrope", "Segoe UI", sans-serif;
    font-size: 18pt;
    font-weight: 700;
    color: {TEXT_PRIMARY};
    background: transparent;
}}

QLabel[subheading="true"] {{
    font-family: "Manrope", "Segoe UI", sans-serif;
    font-size: 13pt;
    font-weight: 600;
    color: {TEXT_PRIMARY};
    background: transparent;
}}

QLabel[muted="true"] {{
    color: {TEXT_MUTED};
    font-size: 10pt;
    background: transparent;
}}

/* Inputs */
QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit {{
    background-color: {WHITE};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 0 10px;
    min-height: 34px;
    max-height: 34px;
    color: {TEXT_PRIMARY};
    font-size: 10pt;
    selection-background-color: {ACCENT};
    selection-color: {WHITE};
}}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QDateEdit:focus, QTimeEdit:focus {{
    border: 1px solid {ACCENT};
    background-color: {WHITE};
}}

QLineEdit:disabled, QSpinBox:disabled {{
    background-color: {BG_DARK};
    color: {TEXT_MUTED};
}}

QLineEdit[echoMode="2"] {{
    lineedit-password-character: 9679;
}}

/* SpinBox — properly sized up/down buttons */
QSpinBox, QDoubleSpinBox {{
    padding-right: 22px;   /* reserve room for the button column */
}}

QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 22px;
    height: 17px;
    border-left: 1px solid {BORDER};
    border-bottom: 1px solid {BORDER};
    border-top-right-radius: 6px;
    background-color: {WHITE};
}}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {{
    background-color: {BG_DARK};
}}

QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    image: url("{UP_ARROW_SVG}");
    width: 10px;
    height: 10px;
}}

QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 22px;
    height: 17px;
    border-left: 1px solid {BORDER};
    border-bottom-right-radius: 6px;
    background-color: {WHITE};
}}

QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background-color: {BG_DARK};
}}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    image: url("{ARROW_SVG}");
    width: 10px;
    height: 10px;
}}


/* ComboBox */
QComboBox {{
    background-color: {WHITE};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 0 10px;
    min-height: 34px;
    max-height: 34px;
    color: {TEXT_PRIMARY};
    font-size: 10pt;
}}

QComboBox:focus {{
    border-color: {ACCENT};
    background-color: {WHITE};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 30px;
    border: none;
}}

QComboBox::down-arrow {{
    image: url("{ARROW_SVG}");
    width: 12px;
    height: 12px;
}}

QComboBox::down-arrow:on {{
    image: url("{ARROW_SVG}");
}}

QComboBox QAbstractItemView {{
    background-color: {WHITE};
    border: 1px solid {BORDER};
    selection-background-color: {ACCENT_LIGHT};
    selection-color: {TEXT_PRIMARY};
    color: {TEXT_PRIMARY};
    outline: none;
    padding: 4px;
}}

QComboBox QAbstractItemView::item {{
    padding: 8px 12px;
    border-radius: 4px;
    margin: 1px 0;
    border-bottom: 1px solid {BORDER_LIGHT};
}}

QComboBox QAbstractItemView::item:selected {{
    background-color: {ACCENT_LIGHT};
    color: {ACCENT};
    border-bottom: 1px solid transparent;
}}

/* ── Calendar Widget ─────────────────────────────────────── */

/* Navigation bar — flex-like row, vertically centred */
QCalendarWidget QWidget#qt_calendar_navigationbar {{
    background-color: {BG_DARK};
    border-bottom: 1px solid {BORDER};
    min-height: 44px;
    max-height: 44px;
}}

/* Prev / Next arrow buttons — vertically centred inside the nav bar */
QCalendarWidget QToolButton#qt_calendar_prevmonth,
QCalendarWidget QToolButton#qt_calendar_nextmonth {{
    color: {TEXT_PRIMARY};
    font-size: 14pt;
    font-weight: 700;
    border: none;
    border-radius: 4px;
    padding: 0px;
    margin: 8px 4px;          /* top+bottom margin centres them in the 44px bar */
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
    background: transparent;
    qproperty-iconSize: 0px;  /* hide the default icon so only text/arrow shows  */
}}

QCalendarWidget QToolButton#qt_calendar_prevmonth:hover,
QCalendarWidget QToolButton#qt_calendar_nextmonth:hover {{
    background-color: {BORDER};
}}

/* Month / year button in the centre of the nav bar */
QCalendarWidget QToolButton#qt_calendar_monthbutton,
QCalendarWidget QToolButton#qt_calendar_yearbutton {{
    color: {TEXT_PRIMARY};
    font-family: "Manrope";
    font-size: 11pt;
    font-weight: 700;
    border: none;
    border-radius: 4px;
    padding: 0px 26px 0px 6px;  /* right padding creates gap between text and arrow */
    margin: 8px 2px;
    min-height: 28px;
    max-height: 28px;
    background: transparent;
}}

QCalendarWidget QToolButton#qt_calendar_monthbutton:hover,
QCalendarWidget QToolButton#qt_calendar_yearbutton:hover {{
    background-color: {BG_HOVER};
}}

/* Drop-down arrow on the month button — padding-right on button makes room for gap */
QCalendarWidget QToolButton::menu-indicator {{
    image: url("{ARROW_SVG}");
    width: 10px;
    height: 10px;
    subcontrol-position: right center;
    subcontrol-origin: padding;
    right: 4px;
}}

QCalendarWidget QMenu {{
    background-color: {WHITE};
    border: 1px solid {BORDER};
    font-family: "Manrope";
    font-size: 10pt;
}}

QCalendarWidget QSpinBox {{
    width: 70px;
    font-family: "Manrope";
    font-size: 10pt;
    color: {TEXT_PRIMARY};
    background-color: {WHITE};
    selection-background-color: {ACCENT};
    selection-color: {WHITE};
    border: 1px solid {BORDER};
    border-radius: 4px;
    min-height: 28px;
    max-height: 28px;
    margin: 8px 2px;
}}

/* Day-of-week header row */
QCalendarWidget QAbstractItemView {{
    font-family: "Manrope";
    font-size: 10pt;
    background-color: {WHITE};
    outline: none;
}}

/* The actual date grid table */
QCalendarWidget QTableView {{
    background-color: {WHITE};
    alternate-background-color: {WHITE};
    selection-background-color: {ACCENT};
    selection-color: {WHITE};
    border: none;
}}

/* Selectable dates — dark, bold, clearly clickable */
QCalendarWidget QTableView::item:enabled {{
    color: {TEXT_PRIMARY};
    font-weight: 600;
    background-color: transparent;
    border-radius: 4px;
}}

QCalendarWidget QTableView::item:enabled:hover {{
    background-color: {ACCENT_LIGHT};
    color: {ACCENT};
}}

QCalendarWidget QTableView::item:enabled:selected {{
    background-color: {ACCENT};
    color: {WHITE};
    border-radius: 4px;
}}

/* Out-of-range / past dates — visually muted, no hover effect */
QCalendarWidget QTableView::item:disabled {{
    color: #C8C6C2;
    font-weight: 400;
    font-style: italic;
    background-color: transparent;
}}

/* Buttons */
QPushButton {{
    font-family: "Manrope", "Segoe UI", sans-serif;
    font-size: 11pt;
    font-weight: 600;
    border-radius: {RADIUS};
    padding: 8px 20px;
    min-height: {BTN_HEIGHT};
    border: 1.5px solid {BORDER};
    background-color: {WHITE};
    color: {TEXT_PRIMARY};
}}

QPushButton:hover {{
    background-color: {BG_HOVER};
    border-color: {BORDER};
}}

QPushButton:pressed {{
    background-color: {BG_DARK};
}}

QPushButton[primary="true"] {{
    background-color: {ACCENT};
    color: {WHITE};
    border: none;
}}

QPushButton[primary="true"]:hover {{
    background-color: {ACCENT_HOVER};
}}

QPushButton[secondary="true"] {{
    background-color: {WHITE};
    color: {TEXT_PRIMARY};
    border: 1.5px solid {BORDER};
}}

QPushButton[secondary="true"]:hover {{
    background-color: {BG_HOVER};
    border-color: #CDCBC6;
}}

QPushButton[danger="true"] {{
    background-color: {DANGER};
    color: {WHITE};
    border: none;
}}

QPushButton[danger="true"]:hover {{
    background-color: {DANGER_HOVER};
}}

QPushButton:disabled {{
    background-color: {BG_DARK};
    color: {TEXT_MUTED};
    border: 1px solid {BORDER};
}}

/* Radio / Checkbox */
QRadioButton, QCheckBox {{
    spacing: 8px;
    font-size: 11pt;
    color: {TEXT_PRIMARY};
    background: transparent;
}}

QRadioButton::indicator, QCheckBox::indicator {{
    width: 18px;
    height: 18px;
}}

/* Tables */
QTableWidget, QTableView {{
    background-color: {WHITE};
    alternate-background-color: {BG_DARK};
    gridline-color: {BORDER};
    border: 1px solid {BORDER};
    border-radius: {RADIUS};
    selection-background-color: {ACCENT_LIGHT};
    selection-color: {TEXT_PRIMARY};
    color: {TEXT_PRIMARY};
    font-size: 10pt;
}}

QHeaderView::section {{
    background-color: {BG_DARK};
    color: {TEXT_SECONDARY};
    font-family: "Manrope", "Segoe UI", sans-serif;
    font-weight: 600;
    font-size: 10pt;
    padding: 8px 12px;
    border: none;
    border-bottom: 2px solid {BORDER};
    border-right: 1px solid {BORDER};
}}

QTableWidget::item {{
    padding: 6px 12px;
}}

/* Scroll Bars */
QScrollBar:vertical {{
    background: {BG_DARK};
    width: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: #CDCBC6;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: {BG_DARK};
    height: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal {{
    background: {BORDER};
    border-radius: 4px;
    min-width: 30px;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* Tab Widget */
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: {RADIUS};
    background: {WHITE};
    margin-top: -1px;
}}

QTabBar::tab {{
    font-family: "Manrope", "Segoe UI", sans-serif;
    font-weight: 600;
    font-size: 10pt;
    padding: 10px 24px;
    background: {BG_DARK};
    color: {TEXT_MUTED};
    border: 1px solid {BORDER};
    border-bottom: none;
    border-top-left-radius: {RADIUS};
    border-top-right-radius: {RADIUS};
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background: {WHITE};
    color: {ACCENT};
    border-bottom: 2px solid {ACCENT};
}}

QTabBar::tab:hover:!selected {{
    background: {BG_HOVER};
    color: {TEXT_PRIMARY};
}}

/* Group Boxes */
QGroupBox {{
    font-family: "Manrope", "Segoe UI", sans-serif;
    font-weight: 600;
    font-size: 11pt;
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: {RADIUS};
    margin-top: 12px;
    padding-top: 20px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 16px;
    padding: 0 8px;
    background-color: {BG_DARKEST};
}}

/* Status Bar */
QStatusBar {{
    background-color: {BG_DARK};
    color: {TEXT_MUTED};
    font-size: 9pt;
    border-top: 1px solid {BORDER};
}}

/* Message Boxes */
QMessageBox {{
    background-color: {WHITE};
}}

QMessageBox QLabel {{
    color: {TEXT_PRIMARY};
    font-size: 11pt;
    background: transparent;
}}

QMessageBox QPushButton {{
    min-width: 80px;
}}

/* Text Edit */
QTextEdit, QPlainTextEdit {{
    background-color: {BG_INPUT};
    border: 1px solid {BORDER};
    border-radius: {RADIUS};
    padding: 8px;
    color: {TEXT_PRIMARY};
    font-size: 10pt;
}}

/* Tooltips */
QToolTip {{
    background-color: {TEXT_PRIMARY};
    color: {WHITE};
    border: none;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 10pt;
}}

/* Menu */
QMenu {{
    background-color: {WHITE};
    border: 1px solid {BORDER};
    border-radius: {RADIUS};
    color: {TEXT_PRIMARY};
    padding: 4px;
}}

QMenu::item {{
    padding: 6px 20px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {ACCENT_LIGHT};
    color: {ACCENT};
}}

/* Splitter */
QSplitter::handle {{
    background-color: {BORDER};
}}
"""
