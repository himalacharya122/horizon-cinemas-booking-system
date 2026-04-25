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
  Manrope → headings, brand, all body text
"""

from pathlib import Path

from PyQt6.QtGui import QFont, QFontDatabase  # type: ignore

# Backgrounds
BG_DARKEST = "#FAFAF9"   # page / window background   (ink-50)
BG_DARK    = "#F1F1EF"   # sidebar, panels            (ink-100)
BG_CARD    = "#FFFFFF"   # card surfaces              (white)
BG_INPUT   = "#FAFAF9"   # input fields               (ink-50)
BG_HOVER   = "#F1F1EF"   # hover state                (ink-100)

# Borders
BORDER       = "#E4E3E0"  # default borders            (ink-200)
BORDER_LIGHT = "#F1F1EF"  # subtle / inner borders     (ink-100)

# Text
TEXT_PRIMARY   = "#0A0908"  # headings, body            (ink-900)
TEXT_SECONDARY = "#2E2C28"  # labels, secondary copy    (ink-700)
TEXT_MUTED     = "#6E6C68"  # placeholders, captions    (ink-500)

# Accent (Horizon red)
ACCENT       = "#B91C1C"   # primary red
ACCENT_HOVER = "#991B1B"   # hover / pressed
ACCENT_LIGHT = "#FEF2F2"   # tinted background for red accents

# Hero (dark brand panel — login left side, nav bar)
HERO_BG = "#0A0908"   # ink-900
HERO_FG = "#FFFFFF"   # text on hero

# Supporting
GOLD          = "#C8A04A"   # highlights, gold badges
SUCCESS       = "#10B981"   # confirmed / positive
DANGER        = "#EF4444"   # errors / destructive
DANGER_HOVER  = "#DC2626"

# Legacy aliases kept for backward compatibility
WHITE         = "#FFFFFF"
SNOW          = BG_CARD
SILVER        = BORDER
SMOKE         = TEXT_SECONDARY
SLATE         = TEXT_MUTED
CHARCOAL      = TEXT_PRIMARY
BLACK         = "#0A0908"
ACCENT_LIGHT_LEGACY = ACCENT_LIGHT

# Font Loading
FONTS_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
_fonts_loaded = False


def load_fonts():
    """Load Manrope from the local fonts directory."""
    global _fonts_loaded
    if _fonts_loaded:
        return
    _fonts_loaded = True
    if not FONTS_DIR.exists():
        return
    for font_file in FONTS_DIR.rglob("*"):
        if font_file.suffix.lower() in (".ttf", ".otf"):
            QFontDatabase.addApplicationFont(str(font_file))


def heading_font(size: int = 16, bold: bool = True) -> QFont:
    """Manrope — headings, brand, navigation."""
    f = QFont("Manrope", size)
    if bold:
        f.setBold(True)
    return f


def body_font(size: int = 11, bold: bool = False) -> QFont:
    """Manrope — body text, labels, inputs."""
    f = QFont("Manrope", size)
    if bold:
        f.setBold(True)
    return f


# Spacing / Sizing
RADIUS    = "8px"
RADIUS_LG = "12px"
SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 16
SPACING_LG = 24
SPACING_XL = 32

INPUT_HEIGHT = "38px"
BTN_HEIGHT   = "40px"

# Global QSS — Light Cinema Theme
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
    background-color: {BG_INPUT};
    border: 1.5px solid {BORDER};
    border-radius: {RADIUS};
    padding: 6px 12px;
    min-height: {INPUT_HEIGHT};
    color: {TEXT_PRIMARY};
    font-size: 11pt;
    selection-background-color: {ACCENT};
    selection-color: {WHITE};
}}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QDateEdit:focus, QTimeEdit:focus {{
    border: 1.5px solid {ACCENT};
    background-color: {WHITE};
    outline: none;
}}

QLineEdit:disabled, QSpinBox:disabled {{
    background-color: {BG_DARK};
    color: {TEXT_MUTED};
}}

QLineEdit[echoMode="2"] {{
    lineedit-password-character: 9679;
}}

/* ComboBox */
QComboBox {{
    background-color: {BG_INPUT};
    border: 1.5px solid {BORDER};
    border-radius: {RADIUS};
    padding: 6px 12px;
    min-height: {INPUT_HEIGHT};
    color: {TEXT_PRIMARY};
    font-size: 11pt;
}}

QComboBox:focus {{
    border-color: {ACCENT};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border-left: 1px solid {BORDER};
    border-top-right-radius: {RADIUS};
    border-bottom-right-radius: {RADIUS};
}}

QComboBox QAbstractItemView {{
    background-color: {WHITE};
    border: 1px solid {BORDER};
    selection-background-color: {ACCENT_LIGHT};
    selection-color: {TEXT_PRIMARY};
    color: {TEXT_PRIMARY};
    outline: 0;
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

QPushButton[primary="true"]:pressed {{
    background-color: #7F1D1D;
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

/* Calendar */
QCalendarWidget {{
    background-color: {WHITE};
    color: {TEXT_PRIMARY};
}}

QCalendarWidget QAbstractItemView {{
    background-color: {WHITE};
    color: {TEXT_PRIMARY};
    selection-background-color: {ACCENT};
    selection-color: {WHITE};
}}

QCalendarWidget QWidget#qt_calendar_navigationbar {{
    background-color: {BG_DARK};
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
