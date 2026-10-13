"""Единый стиль для всего приложения"""

# Цветовая палитра
COLORS = {
    'primary': '#2196F3',      # Синий
    'primary_dark': '#1976D2',
    'success': '#4CAF50',      # Зелёный
    'danger': '#f44336',       # Красный
    'warning': '#FF9800',      # Оранжевый
    'bg_main': '#f5f5f5',      # Фон
    'bg_card': '#ffffff',      # Карточки
    'bg_header': '#2196F3',    # Шапка
    'text_main': '#212121',
    'text_secondary': '#757575',
    'border': '#e0e0e0',
}

# Общие стили
APP_STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS['bg_main']};
}}

QWidget {{
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 13px;
    color: {COLORS['text_main']};
}}

QGroupBox {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 15px;
    font-weight: bold;
    font-size: 13px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    color: {COLORS['primary_dark']};
}}

QPushButton {{
    background-color: {COLORS['primary']};
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: bold;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: {COLORS['primary_dark']};
}}

QPushButton:pressed {{
    background-color: #1565C0;
}}

QPushButton#calcButton {{
    background-color: {COLORS['success']};
    font-size: 16px;
    padding: 12px 24px;
    border-radius: 6px;
}}

QPushButton#calcButton:hover {{
    background-color: #388E3C;
}}

QPushButton#resetButton {{
    background-color: {COLORS['warning']};
}}

QPushButton#resetButton:hover {{
    background-color: #F57C00;
}}

QPushButton#removeButton {{
    background-color: {COLORS['danger']};
    padding: 4px 8px;
    font-size: 11px;
}}

QPushButton#removeButton:hover {{
    background-color: #d32f2f;
}}

QPushButton#addButton {{
    background-color: {COLORS['success']};
    padding: 6px 12px;
    font-size: 12px;
}}

QPushButton#addButton:hover {{
    background-color: #388E3C;
}}

QLineEdit {{
    background-color: white;
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 6px 8px;
    min-height: 20px;
}}

QLineEdit:focus {{
    border: 2px solid {COLORS['primary']};
}}

QComboBox {{
    background-color: white;
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 6px 8px;
    min-height: 20px;
}}

QComboBox:hover {{
    border: 1px solid {COLORS['primary']};
}}

QComboBox::drop-down {{
    border: none;
}}

QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    background-color: {COLORS['bg_card']};
}}

QTabBar::tab {{
    background-color: {COLORS['bg_main']};
    border: 1px solid {COLORS['border']};
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 10px 20px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background-color: {COLORS['bg_card']};
    border-bottom: 2px solid {COLORS['primary']};
    font-weight: bold;
}}

QTabBar::tab:hover {{
    background-color: #e3f2fd;
}}

QMenuBar {{
    background-color: {COLORS['bg_header']};
    color: white;
    padding: 2px;
}}

QMenuBar::item:selected {{
    background-color: {COLORS['primary_dark']};
}}

QMenu {{
    background-color: white;
    border: 1px solid {COLORS['border']};
}}

QMenu::item:selected {{
    background-color: {COLORS['primary']};
    color: white;
}}

QLabel {{
    background-color: transparent;
}}

QLabel#headerLabel {{
    font-size: 18px;
    font-weight: bold;
    color: {COLORS['primary_dark']};
    padding: 10px;
}}

QCheckBox {{
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
}}

QRadioButton {{
    spacing: 8px;
}}

QRadioButton::indicator {{
    width: 18px;
    height: 18px;
}}

QTableWidget {{
    background-color: white;
    border: 1px solid {COLORS['border']};
    gridline-color: {COLORS['border']};
}}

QTableWidget::item:selected {{
    background-color: #bbdefb;
}}

QHeaderView::section {{
    background-color: {COLORS['primary']};
    color: white;
    padding: 8px;
    border: 1px solid {COLORS['border']};
    font-weight: bold;
}}

QScrollArea {{
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    background-color: {COLORS['bg_card']};
}}
"""