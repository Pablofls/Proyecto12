"""Identidad visual compartida con la plataforma web."""

VERDE = "#1f6f4a"
VERDE_OSCURO = "#17583b"
VERDE_CLARO = "#e8f3ed"
GRIS = "#5b6670"
GRIS_CLARO = "#f4f6f7"
BORDE = "#dde3e6"
ROJO = "#b3261e"
AMBAR = "#8a6100"
TEXTO = "#1c2226"


ESTILO = f"""
QWidget {{
    color: {TEXTO};
    font-family: "Segoe UI";
    font-size: 14px;
}}
QMainWindow, QWidget#raiz, QStackedWidget {{ background: {GRIS_CLARO}; }}
QWidget#encabezado {{ background: {VERDE}; }}
QLabel#marca {{ color: white; font-size: 16px; font-weight: 700; letter-spacing: 1px; }}
QLabel#sesion {{ color: white; }}
QLabel#insignia {{
    color: white; background: rgba(255,255,255,35); border-radius: 12px;
    padding: 4px 10px; font-weight: 600;
}}
QLabel#titulo {{ font-size: 22px; font-weight: 700; color: {TEXTO}; }}
QLabel#subtitulo, QLabel#ayuda {{ color: {GRIS}; }}
QLabel#estadoOk {{
    color: {VERDE}; background: #e3f2e9; border: 1px solid #b9dcc8;
    border-radius: 5px; padding: 8px 10px;
}}
QLabel#estadoError {{
    color: {ROJO}; background: #fdeceb; border: 1px solid #f2c4c1;
    border-radius: 5px; padding: 8px 10px;
}}
QFrame#tarjeta {{
    background: white; border: 1px solid {BORDE}; border-radius: 8px;
}}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {{
    background: white; border: 1px solid {BORDE}; border-radius: 5px;
    padding: 8px 9px; min-height: 20px;
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QComboBox:focus, QTextEdit:focus {{ border: 2px solid {VERDE}; }}
QPushButton {{
    background: {VERDE}; color: white; border: 0; border-radius: 5px;
    padding: 9px 16px; font-weight: 600;
}}
QPushButton:hover {{ background: {VERDE_OSCURO}; }}
QPushButton:disabled {{ background: #aeb8b2; color: #edf0ee; }}
QPushButton#secundario {{
    background: white; color: {VERDE}; border: 1px solid {VERDE};
}}
QPushButton#secundario:hover {{ background: {VERDE_CLARO}; }}
QPushButton#salir {{ background: rgba(255,255,255,35); }}
QPushButton#salir:hover {{ background: rgba(255,255,255,55); }}
QTabWidget::pane {{ border: 0; background: {GRIS_CLARO}; }}
QTabBar::tab {{
    background: white; color: {GRIS}; padding: 12px 16px;
    border-bottom: 3px solid transparent;
}}
QTabBar::tab:selected {{ color: {VERDE}; border-bottom: 3px solid {VERDE}; }}
QTabBar::tab:hover {{ color: {VERDE}; background: {VERDE_CLARO}; }}
QHeaderView::section {{
    background: {VERDE_CLARO}; color: {GRIS}; border: 0;
    border-bottom: 1px solid {BORDE}; padding: 9px 10px;
    font-size: 12px; font-weight: 700;
}}
QTableWidget {{
    background: white; alternate-background-color: #fafbfb;
    border: 1px solid {BORDE}; border-radius: 7px; gridline-color: {BORDE};
    selection-background-color: {VERDE_CLARO}; selection-color: {TEXTO};
}}
QTableWidget::item {{ padding: 7px; border-bottom: 1px solid {BORDE}; }}
QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{ width: 18px; height: 18px; }}
QScrollArea {{ border: 0; background: {GRIS_CLARO}; }}
QStatusBar {{ background: white; color: {GRIS}; border-top: 1px solid {BORDE}; }}
QToolTip {{ background: {TEXTO}; color: white; border: 0; padding: 5px; }}
"""
