"""
desktop/ui/theme.py
Dark cinema theme — immersive, modern design inspired by premium
cinema booking platforms.

Palette:
  Backgrounds  — deep navy-blacks (#0D0D1A → #2A2A48)
  Text         — off-white / muted grey (#EAEAF0 → #5C5C78)
  Accent       — cinema red (#E53E3E)
  Gold         — IMDb-style ratings (#F6C744)
  Success      — teal (#2DD4BF)
  Danger       — coral-red (#FC5C65)

Fonts:
  Manrope → headings, navigation
  Inter   → body text, labels, inputs
"""

from pathlib import Path
from PyQt6.QtGui import QFontDatabase, QFont  # type: ignore
from PyQt6.QtWidgets import QApplication  # type: ignore

# Dark Cinema Backgrounds
BG_DARKEST   = "#222831"   # Main app / content area background
BG_DARK      = "#393E46"   # Sidebar, panels
BG_CARD      = "#2E3440"   # Slightly lifted surface (blend of dark tones)
BG_INPUT     = "#3F454F"   # Input fields, combo boxes (lighter than panel)
BG_HOVER     = "#4A505A"   # Hover state

# Borders
BORDER       = "#393E46"   # Default borders
BORDER_LIGHT = "#4A505A"   # Focus / lighter borders

# ─── Text ───
TEXT_PRIMARY   = "#EEEEEE"  # Primary readable text
TEXT_SECONDARY = "#C9D1D9"  # Softer light gray
TEXT_MUTED     = "#9AA4AF"  # Muted text

# ─── Accent — Teal Accent ───
ACCENT       = "#00ADB5"
ACCENT_HOVER = "#0199A1"   # Slightly darker teal for hover
ACCENT_LIGHT = "#0F2E30"   # Subtle teal-tinted background

# ─── Supporting Colours ───
GOLD         = "#F6C744"      # IMDb ratings, stars
SUCCESS      = "#2DD4BF"      # Confirmed, positive
DANGER       = "#FC5C65"      # Cancel, errors
DANGER_HOVER = "#EB3B5A"

# ─── Legacy aliases (backward compatibility with admin/manager pages) ───
WHITE    = "#FFFFFF"
SNOW     = BG_CARD
SILVER   = BORDER
SMOKE    = TEXT_SECONDARY
SLATE    = "#6B7280"
CHARCOAL = TEXT_PRIMARY
BLACK    = "#F5F5F7"

ACCENT_LIGHT_LEGACY = ACCENT_LIGHT   # some old code may reference

# ─── Font Loading ───
FONTS_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
_fonts_loaded = False


def load_fonts():
    """Load Manrope and Inter from the local fonts directory."""
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
    """Manrope font for headings."""
    f = QFont("Manrope", size)
    if bold:
        f.setBold(True)
    return f


def body_font(size: int = 11) -> QFont:
    """Inter font for body text."""
    return QFont("Inter", size)


# ─── Spacing / Sizing ───
RADIUS      = "6px"
RADIUS_LG   = "10px"
SPACING_XS  = 4
SPACING_SM  = 8
SPACING_MD  = 16
SPACING_LG  = 24
SPACING_XL  = 32

INPUT_HEIGHT = "38px"
BTN_HEIGHT   = "40px"

# ─── Global QSS — Dark Cinema Theme ───
GLOBAL_QSS = f"""
/* ═══ Base ═══ */
QMainWindow, QDialog {{
    background-color: {BG_DARKEST};
    color: {TEXT_PRIMARY};
    font-family: "Inter", "Segoe UI", "Helvetica Neue", sans-serif;
    font-size: 11pt;
}}

QWidget {{
    color: {TEXT_PRIMARY};
    font-family: "Inter", "Segoe UI", "Helvetica Neue", sans-serif;
    font-size: 11pt;
}}

/* ═══ Labels ═══ */
QLabel {{
    color: {TEXT_PRIMARY};
    background: transparent;
}}

QLabel[heading="true"] {{
    font-family: "Manrope", "Segoe UI", sans-serif;
    font-size: 18pt;
    font-weight: 700;
    color: {WHITE};
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
    color: {TEXT_SECONDARY};
    font-size: 10pt;
    background: transparent;
}}

/* ═══ Inputs ═══ */
QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit {{
    background-color: {BG_INPUT};
    border: 1px solid {BORDER};
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
    outline: none;
}}

QLineEdit:disabled, QSpinBox:disabled {{
    background-color: {BG_DARK};
    color: {TEXT_MUTED};
}}

QLineEdit[echoMode="2"] {{
    lineedit-password-character: 9679;
}}

/* ═══ Combo Box ═══ */
QComboBox {{
    background-color: {BG_INPUT};
    border: 1px solid {BORDER};
    border-radius: {RADIUS};
    padding: 6px 12px;
    min-height: {INPUT_HEIGHT};
    color: {TEXT_PRIMARY};
    font-size: 11pt;
}}

QComboBox:focus {{
    border: 1.5px solid {ACCENT};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 30px;
    border-left: 1px solid {BORDER};
    border-top-right-radius: {RADIUS};
    border-bottom-right-radius: {RADIUS};
}}

QComboBox QAbstractItemView {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER};
    selection-background-color: {ACCENT};
    selection-color: {WHITE};
    color: {TEXT_PRIMARY};
    outline: 0;
}}

/* ═══ Buttons ═══ */
QPushButton {{
    font-family: "Inter", "Segoe UI", sans-serif;
    font-size: 11pt;
    font-weight: 600;
    border-radius: {RADIUS};
    padding: 8px 20px;
    min-height: {BTN_HEIGHT};
    border: none;
    background-color: {BG_HOVER};
    color: {TEXT_PRIMARY};
}}

QPushButton:hover {{
    background-color: {BORDER_LIGHT};
}}

QPushButton[primary="true"] {{
    background-color: {ACCENT};
    color: {WHITE};
}}

QPushButton[primary="true"]:hover {{
    background-color: {ACCENT_HOVER};
}}

QPushButton[primary="true"]:pressed {{
    background-color: #9B2C2C;
}}

QPushButton[secondary="true"] {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
}}

QPushButton[secondary="true"]:hover {{
    background-color: {BG_HOVER};
    border-color: {BORDER_LIGHT};
}}

QPushButton[danger="true"] {{
    background-color: {DANGER};
    color: {WHITE};
}}

QPushButton[danger="true"]:hover {{
    background-color: {DANGER_HOVER};
}}

QPushButton:disabled {{
    background-color: {BG_DARK};
    color: {TEXT_MUTED};
    border: 1px solid {BORDER};
}}

/* Radio / Check */
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

/* ═══ Tables ═══ */
QTableWidget, QTableView {{
    background-color: {BG_CARD};
    alternate-background-color: {BG_DARK};
    gridline-color: {BORDER};
    border: 1px solid {BORDER};
    border-radius: {RADIUS};
    selection-background-color: {ACCENT_LIGHT};
    selection-color: {WHITE};
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

/* ═══ Scroll Bars ═══ */
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
    background: {BORDER_LIGHT};
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

/* ═══ Tab Widget ═══ */
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: {RADIUS};
    background: {BG_CARD};
    margin-top: -1px;
}}

QTabBar::tab {{
    font-family: "Manrope", "Segoe UI", sans-serif;
    font-weight: 600;
    font-size: 10pt;
    padding: 10px 24px;
    background: {BG_DARK};
    color: {TEXT_SECONDARY};
    border: 1px solid {BORDER};
    border-bottom: none;
    border-top-left-radius: {RADIUS};
    border-top-right-radius: {RADIUS};
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background: {BG_CARD};
    color: {ACCENT};
    border-bottom: 2px solid {ACCENT};
}}

QTabBar::tab:hover:!selected {{
    background: {BG_HOVER};
    color: {TEXT_PRIMARY};
}}

/* ═══ Group Boxes ═══ */
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

/* ═══ Status Bar ═══ */
QStatusBar {{
    background-color: {BG_DARK};
    color: {TEXT_SECONDARY};
    font-size: 9pt;
    border-top: 1px solid {BORDER};
}}

/* ═══ Message Boxes ═══ */
QMessageBox {{
    background-color: {BG_CARD};
}}

QMessageBox QLabel {{
    color: {TEXT_PRIMARY};
    font-size: 11pt;
    background: transparent;
}}

QMessageBox QPushButton {{
    min-width: 80px;
}}

/* ═══ Text Edit ═══ */
QTextEdit, QPlainTextEdit {{
    background-color: {BG_INPUT};
    border: 1px solid {BORDER};
    border-radius: {RADIUS};
    padding: 8px;
    color: {TEXT_PRIMARY};
    font-size: 10pt;
}}

/* ═══ Calendar Popup ═══ */
QCalendarWidget {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
}}

QCalendarWidget QAbstractItemView {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    selection-background-color: {ACCENT};
    selection-color: {WHITE};
}}

QCalendarWidget QWidget#qt_calendar_navigationbar {{
    background-color: {BG_DARK};
}}

/* ═══ Tooltips ═══ */
QToolTip {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    padding: 4px 8px;
}}
"""
