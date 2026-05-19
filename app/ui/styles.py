from app.config import COLORS

C = COLORS

MAIN_STYLE = f"""
QMainWindow, QDialog, QWidget {{
    background-color: {C['bg']};
    color: {C['text']};
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}}

/* ── Sidebar ── */
#sidebar {{
    background-color: {C['navy']};
    min-width: 220px;
    max-width: 220px;
}}
#sidebar_header {{
    background-color: {C['navy']};
    padding: 16px 12px;
    border-bottom: 1px solid {C['navy_light']};
}}
#sidebar_title {{
    color: {C['gold']};
    font-size: 13px;
    font-weight: bold;
}}
#sidebar_subtitle {{
    color: #8899AA;
    font-size: 11px;
}}

QPushButton#nav_btn {{
    background: transparent;
    color: #BDC8D4;
    border: none;
    border-radius: 6px;
    padding: 10px 16px;
    text-align: left;
    font-size: 13px;
    margin: 1px 8px;
}}
QPushButton#nav_btn:hover {{
    background-color: {C['sidebar_hover']};
    color: white;
}}
QPushButton#nav_btn:checked {{
    background-color: {C['gold']};
    color: {C['navy']};
    font-weight: bold;
}}

/* ── Header ── */
#header {{
    background-color: white;
    border-bottom: 1px solid {C['border']};
    padding: 8px 20px;
    min-height: 52px;
    max-height: 52px;
}}
#page_title {{
    font-size: 18px;
    font-weight: bold;
    color: {C['text']};
}}
#user_info {{
    color: {C['text_light']};
    font-size: 12px;
}}

/* ── Cards / Panels ── */
QFrame#card {{
    background-color: white;
    border: 1px solid {C['border']};
    border-radius: 8px;
}}
QFrame#stat_card {{
    background-color: white;
    border: 1px solid {C['border']};
    border-radius: 8px;
    padding: 8px;
}}

/* ── Tables ── */
QTableWidget {{
    background-color: white;
    border: 1px solid {C['border']};
    border-radius: 6px;
    gridline-color: #EEF0F3;
    selection-background-color: #EBF3FB;
    selection-color: {C['text']};
    alternate-background-color: #FAFBFC;
}}
QTableWidget::item {{
    padding: 6px 10px;
    border-bottom: 1px solid #EEF0F3;
}}
QHeaderView::section {{
    background-color: #F0F2F5;
    color: {C['text']};
    padding: 8px 10px;
    border: none;
    border-right: 1px solid {C['border']};
    border-bottom: 2px solid {C['border']};
    font-weight: bold;
    font-size: 12px;
}}

/* ── Buttons ── */
QPushButton {{
    background-color: {C['gold']};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: bold;
    font-size: 13px;
    min-height: 32px;
}}
QPushButton:hover {{
    background-color: {C['gold_dark']};
}}
QPushButton:pressed {{
    background-color: #7A5F1E;
}}
QPushButton:disabled {{
    background-color: #CCCCCC;
    color: #999999;
}}
QPushButton#btn_secondary {{
    background-color: white;
    color: {C['text']};
    border: 1px solid {C['border']};
}}
QPushButton#btn_secondary:hover {{
    background-color: {C['bg']};
}}
QPushButton#btn_danger {{
    background-color: {C['danger']};
    color: white;
}}
QPushButton#btn_danger:hover {{
    background-color: #C0392B;
}}
QPushButton#btn_success {{
    background-color: {C['success']};
    color: white;
}}
QPushButton#btn_success:hover {{
    background-color: #1E8449;
}}
QPushButton#btn_info {{
    background-color: {C['info']};
    color: white;
}}
QPushButton#btn_info:hover {{
    background-color: #1A6FA0;
}}
QPushButton#btn_warning {{
    background-color: {C['warning']};
    color: white;
}}
QPushButton#btn_warning:hover {{
    background-color: #D68910;
}}

/* ── Inputs ── */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QComboBox {{
    background-color: white;
    border: 1px solid {C['border']};
    border-radius: 5px;
    padding: 6px 10px;
    color: {C['text']};
    font-size: 13px;
    min-height: 28px;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QComboBox:focus {{
    border: 2px solid {C['gold']};
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid {C['text_light']};
    width: 0;
    height: 0;
    margin-right: 6px;
}}
QComboBox QAbstractItemView {{
    border: 1px solid {C['border']};
    background: white;
    selection-background-color: #EBF3FB;
}}

/* ── Labels ── */
QLabel#field_label {{
    color: {C['text_light']};
    font-size: 12px;
    font-weight: bold;
}}
QLabel#section_label {{
    color: {C['navy']};
    font-size: 14px;
    font-weight: bold;
    padding-bottom: 4px;
    border-bottom: 2px solid {C['gold']};
}}
QLabel#stat_value {{
    font-size: 22px;
    font-weight: bold;
    color: {C['navy']};
}}
QLabel#stat_title {{
    font-size: 12px;
    color: {C['text_light']};
}}

/* ── Search bar ── */
QLineEdit#search_bar {{
    background-color: white;
    border: 1px solid {C['border']};
    border-radius: 18px;
    padding: 6px 14px;
    min-width: 240px;
}}

/* ── Tabs ── */
QTabWidget::pane {{
    border: 1px solid {C['border']};
    border-radius: 6px;
    background: white;
}}
QTabBar::tab {{
    background: {C['bg']};
    border: 1px solid {C['border']};
    padding: 8px 16px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
    color: {C['text_light']};
}}
QTabBar::tab:selected {{
    background: white;
    color: {C['gold']};
    font-weight: bold;
    border-bottom: 2px solid {C['gold']};
}}

/* ── Scrollbars ── */
QScrollBar:vertical {{
    background: {C['bg']};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: #CCCCCC;
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar:horizontal {{
    background: {C['bg']};
    height: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: #CCCCCC;
    border-radius: 4px;
}}

/* ── Status badges ── */
QLabel#badge_green {{
    background-color: #D5F5E3;
    color: #1E8449;
    border-radius: 10px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: bold;
}}
QLabel#badge_red {{
    background-color: #FADBD8;
    color: #C0392B;
    border-radius: 10px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: bold;
}}
QLabel#badge_yellow {{
    background-color: #FDEBD0;
    color: #D68910;
    border-radius: 10px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: bold;
}}
QLabel#badge_blue {{
    background-color: #D6EAF8;
    color: #1A6FA0;
    border-radius: 10px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: bold;
}}
QLabel#badge_gray {{
    background-color: #E8E8E8;
    color: #555555;
    border-radius: 10px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: bold;
}}

/* ── Separators ── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    color: {C['border']};
}}

/* ── Splitter ── */
QSplitter::handle {{
    background: {C['border']};
}}

/* ── Group Box ── */
QGroupBox {{
    border: 1px solid {C['border']};
    border-radius: 6px;
    margin-top: 14px;
    padding: 10px;
    font-weight: bold;
    color: {C['navy']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    background-color: {C['bg']};
    color: {C['navy']};
}}

/* ── Message boxes ── */
QMessageBox {{
    background-color: white;
}}

/* ── Progress bar ── */
QProgressBar {{
    border: 1px solid {C['border']};
    border-radius: 4px;
    background: {C['bg']};
    height: 8px;
}}
QProgressBar::chunk {{
    background-color: {C['gold']};
    border-radius: 4px;
}}
"""

LOGIN_STYLE = f"""
QWidget {{
    background-color: {C['navy']};
    color: white;
    font-family: 'Segoe UI', Arial, sans-serif;
}}
QFrame#login_card {{
    background-color: white;
    border-radius: 12px;
}}
QLabel#login_title {{
    color: {C['navy']};
    font-size: 22px;
    font-weight: bold;
}}
QLabel#login_sub {{
    color: {C['text_light']};
    font-size: 13px;
}}
QLabel#field_label {{
    color: {C['text']};
    font-size: 12px;
    font-weight: bold;
}}
QLineEdit {{
    background-color: {C['bg']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    padding: 8px 12px;
    color: {C['text']};
    font-size: 14px;
    min-height: 36px;
}}
QLineEdit:focus {{
    border: 2px solid {C['gold']};
    background: white;
}}
QPushButton#btn_login {{
    background-color: {C['gold']};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px;
    font-size: 15px;
    font-weight: bold;
    min-height: 42px;
}}
QPushButton#btn_login:hover {{
    background-color: {C['gold_dark']};
}}
QLabel#error_label {{
    color: {C['danger']};
    font-size: 12px;
}}
"""
