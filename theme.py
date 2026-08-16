"""
Theme and styling for Martin GUI.
"""
from dataclasses import dataclass


@dataclass
class Theme:
    """Application theme colors."""
    background: str = "#050505"
    panel: str = "#0a0a0a"
    border: str = "#1a1a1a"
    text_primary: str = "#f5f5f5"
    text_secondary: str = "#888888"
    accent: str = "#ffffff"
    accent_hover: str = "#d4d4d4"
    accent_pressed: str = "#a3a3a3"
    success: str = "#e5e5e5"
    warning: str = "#cccccc"
    error: str = "#737373"
    input_bg: str = "#000000"
    input_border: str = "#262626"
    sidebar_bg: str = "#000000"
    sidebar_hover: str = "#0a0a0a"
    sidebar_active: str = "#171717"

    font_family: str = "Segoe UI"
    font_size: int = 10
    font_size_large: int = 14
    font_size_small: int = 9


DARK_THEME = Theme()

LIGHT_THEME = Theme(
    background="#ffffff",
    panel="#f5f5f5",
    border="#e5e5e5",
    text_primary="#171717",
    text_secondary="#737373",
    accent="#171717",
    accent_hover="#404040",
    accent_pressed="#525252",
    success="#171717",
    warning="#525252",
    error="#a3a3a3",
    input_bg="#ffffff",
    input_border="#d4d4d4",
    sidebar_bg="#f5f5f5",
    sidebar_hover="#e5e5e5",
    sidebar_active="#d4d4d4",
)


def get_stylesheet(theme: Theme) -> str:
    """Generate QSS stylesheet from theme."""
    return f"""
QMainWindow {{
    background-color: {theme.background};
    color: {theme.text_primary};
    font-family: {theme.font_family};
    font-size: {theme.font_size}pt;
}}

QWidget {{
    background-color: {theme.background};
    color: {theme.text_primary};
}}

QWidget#centralWidget {{
    background-color: {theme.background};
}}

QWidget#sidebar {{
    background-color: {theme.sidebar_bg};
    border-right: 1px solid {theme.border};
}}

QWidget#sidebar QPushButton {{
    background-color: transparent;
    border: none;
    border-radius: 0px;
    padding: 12px 20px;
    color: {theme.text_primary};
    text-align: left;
    font-size: {theme.font_size}pt;
}}

QWidget#sidebar QPushButton:hover {{
    background-color: {theme.sidebar_hover};
}}

QWidget#sidebar QPushButton:pressed {{
    background-color: {theme.sidebar_active};
}}

QWidget#sidebar QPushButton[active="true"] {{
    background-color: {theme.sidebar_active};
    border-left: 2px solid {theme.accent};
    font-weight: bold;
}}

QLabel#logo {{
    color: {theme.text_primary};
    font-size: {theme.font_size_large + 4}pt;
    font-weight: bold;
    padding: 24px 20px;
    letter-spacing: 2px;
}}

QWidget#contentArea {{
    background-color: {theme.background};
}}

QFrame#panel {{
    background-color: {theme.panel};
    border: 1px solid {theme.border};
    border-radius: 0px;
}}

QFrame#panel QLabel#panelTitle {{
    color: {theme.text_primary};
    font-size: {theme.font_size_large}pt;
    font-weight: bold;
    padding: 20px;
    border-bottom: 1px solid {theme.border};
    background-color: transparent;
}}

QFrame#panel QLabel#panelContent {{
    color: {theme.text_primary};
    padding: 20px;
    background-color: transparent;
}}

QPushButton {{
    background-color: {theme.accent};
    color: {theme.background};
    border: none;
    border-radius: 0px;
    padding: 10px 18px;
    font-size: {theme.font_size}pt;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: {theme.accent_hover};
}}

QPushButton:pressed {{
    background-color: {theme.accent_pressed};
}}

QPushButton:disabled {{
    background-color: {theme.border};
    color: {theme.text_secondary};
}}

QPushButton#secondaryButton {{
    background-color: transparent;
    color: {theme.text_primary};
    border: 1px solid {theme.border};
    border-radius: 0px;
}}

QPushButton#secondaryButton:hover {{
    background-color: {theme.sidebar_hover};
    border-color: {theme.accent};
}}

QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {theme.input_bg};
    color: {theme.text_primary};
    border: 1px solid {theme.input_border};
    border-radius: 0px;
    padding: 10px 14px;
    font-size: {theme.font_size}pt;
    selection-background-color: {theme.accent};
    selection-color: {theme.background};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {theme.accent};
}}

QLabel {{
    color: {theme.text_primary};
    font-size: {theme.font_size}pt;
    background-color: transparent;
}}

QLabel#secondaryLabel {{
    color: {theme.text_secondary};
    font-size: {theme.font_size_small}pt;
}}

QLabel#valueLabel {{
    color: {theme.text_primary};
    font-size: {theme.font_size_large}pt;
    font-weight: bold;
}}

QFrame#userMessage {{
    background-color: {theme.accent};
    border-radius: 0px;
    padding: 12px 16px;
    margin: 6px 24px 6px 56px;
}}

QFrame#assistantMessage {{
    background-color: {theme.panel};
    border: 1px solid {theme.border};
    border-radius: 0px;
    padding: 12px 16px;
    margin: 6px 56px 6px 24px;
}}

QLabel#messageText {{
    color: {theme.text_primary};
    font-size: {theme.font_size}pt;
    background-color: transparent;
}}

QLabel#messageTime {{
    color: {theme.text_secondary};
    font-size: {theme.font_size_small}pt;
    background-color: transparent;
}}

QScrollBar:vertical {{
    background-color: transparent;
    width: 6px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background-color: {theme.border};
    border-radius: 0px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {theme.accent};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QComboBox {{
    background-color: {theme.input_bg};
    color: {theme.text_primary};
    border: 1px solid {theme.input_border};
    border-radius: 0px;
    padding: 8px 12px;
    min-width: 120px;
}}

QComboBox:hover {{
    border-color: {theme.accent};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid {theme.text_primary};
    margin-right: 8px;
}}

QListWidget {{
    background-color: {theme.panel};
    border: 1px solid {theme.border};
    border-radius: 0px;
    color: {theme.text_primary};
}}

QListWidget::item {{
    padding: 10px 14px;
    border-bottom: 1px solid {theme.border};
}}

QListWidget::item:selected {{
    background-color: {theme.accent};
    color: {theme.background};
}}

QListWidget::item:hover {{
    background-color: {theme.sidebar_hover};
}}

QProgressBar {{
    background-color: {theme.input_bg};
    border: 1px solid {theme.input_border};
    border-radius: 0px;
    text-align: center;
    color: {theme.text_primary};
}}

QProgressBar::chunk {{
    background-color: {theme.accent};
    border-radius: 0px;
}}

QFrame#separator {{
    background-color: {theme.border};
    max-height: 1px;
    min-height: 1px;
}}

QToolTip {{
    background-color: {theme.panel};
    border: 1px solid {theme.border};
    color: {theme.text_primary};
    padding: 8px 12px;
    border-radius: 0px;
}}"""
print("theme.py written")
