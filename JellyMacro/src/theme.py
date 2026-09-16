"""
Theme management for JellyMacro - Dark and Light modes
"""

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QPalette, QColor, QFont
from PySide6.QtWidgets import QApplication


class ThemeManager(QObject):
    theme_changed = Signal(str)
    
    DARK_THEME = {
        "name": "dark",
        "background": "#0d1117",
        "surface": "#161b22",
        "surface_variant": "#21262d",
        "border": "#30363d",
        "primary": "#00b4d8",
        "primary_hover": "#0096c7",
        "secondary": "#00d4aa",
        "secondary_hover": "#00b896",
        "accent_top": "#0077b6",
        "accent_bottom": "#00b4d8",
        "text_primary": "#f0f6fc",
        "text_secondary": "#8b949e",
        "text_muted": "#6e7681",
        "success": "#3fb950",
        "warning": "#d29922",
        "error": "#f85149",
        "canvas_bg": "#0d1117",
        "canvas_border": "#30363d",
        "button_bg": "#238636",
        "button_hover": "#2ea043",
        "button_danger": "#da3633",
        "button_danger_hover": "#f85149",
        "input_bg": "#0d1117",
        "input_border": "#30363d",
        "input_focus": "#00b4d8",
        "scrollbar_bg": "#161b22",
        "scrollbar_handle": "#30363d",
        "scrollbar_hover": "#484f58",
        "selection": "#00b4d8",
        "selection_text": "#ffffff",
        "tooltip_bg": "#161b22",
        "tooltip_text": "#f0f6fc",
        "menu_bg": "#161b22",
        "menu_border": "#30363d",
        "menu_hover": "#21262d",
        "header_top": "#0077b6",
        "header_bottom": "#00b4d8",
        "footer_top": "#00b4d8",
        "footer_bottom": "#00d4aa",
    }
    
    LIGHT_THEME = {
        "name": "light",
        "background": "#ffffff",
        "surface": "#f6f8fa",
        "surface_variant": "#eaeef2",
        "border": "#d0d7de",
        "primary": "#0077b6",
        "primary_hover": "#005f8d",
        "secondary": "#00a878",
        "secondary_hover": "#008f65",
        "accent_top": "#ff69b4",
        "accent_bottom": "#87ceeb",
        "text_primary": "#1f2328",
        "text_secondary": "#656d76",
        "text_muted": "#8b949e",
        "success": "#2da44e",
        "warning": "#bf8700",
        "error": "#cf222e",
        "canvas_bg": "#ffffff",
        "canvas_border": "#d0d7de",
        "button_bg": "#2da44e",
        "button_hover": "#3fb950",
        "button_danger": "#cf222e",
        "button_danger_hover": "#f85149",
        "input_bg": "#ffffff",
        "input_border": "#d0d7de",
        "input_focus": "#0077b6",
        "scrollbar_bg": "#f6f8fa",
        "scrollbar_handle": "#d0d7de",
        "scrollbar_hover": "#8b949e",
        "selection": "#0077b6",
        "selection_text": "#ffffff",
        "tooltip_bg": "#1f2328",
        "tooltip_text": "#f0f6fc",
        "menu_bg": "#ffffff",
        "menu_border": "#d0d7de",
        "menu_hover": "#f6f8fa",
        "header_top": "#ffb6c1",
        "header_bottom": "#87ceeb",
        "footer_top": "#87ceeb",
        "footer_bottom": "#98fb98",
    }
    
    def __init__(self):
        super().__init__()
        self._current_theme = "dark"
        self._themes = {
            "dark": self.DARK_THEME,
            "light": self.LIGHT_THEME
        }
    
    @property
    def current_theme(self) -> str:
        return self._current_theme
    
    @property
    def colors(self) -> dict:
        return self._themes[self._current_theme]
    
    def set_theme(self, theme_name: str):
        if theme_name in self._themes:
            self._current_theme = theme_name
            self.theme_changed.emit(theme_name)
    
    def toggle_theme(self):
        new_theme = "light" if self._current_theme == "dark" else "dark"
        self.set_theme(new_theme)
    
    def get_stylesheet(self) -> str:
        c = self.colors
        return f"""
        QMainWindow {{
            background-color: {c['background']};
            color: {c['text_primary']};
        }}
        
        QWidget {{
            background-color: {c['background']};
            color: {c['text_primary']};
            font-family: 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
            font-size: 13px;
        }}
        
        QTabWidget::pane {{
            border: 1px solid {c['border']};
            background-color: {c['surface']};
            border-radius: 8px;
            margin-top: -1px;
        }}
        
        QTabBar::tab {{
            background-color: {c['surface_variant']};
            color: {c['text_secondary']};
            padding: 10px 20px;
            margin-right: 2px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            border: 1px solid {c['border']};
            border-bottom: none;
            min-width: 100px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {c['surface']};
            color: {c['text_primary']};
            border-bottom: 1px solid {c['surface']};
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {c['menu_hover']};
            color: {c['text_primary']};
        }}
        
        QPushButton {{
            background-color: {c['primary']};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: 600;
            min-height: 20px;
        }}
        
        QPushButton:hover {{
            background-color: {c['primary_hover']};
        }}
        
        QPushButton:pressed {{
            background-color: {c['primary']};
        }}
        
        QPushButton:disabled {{
            background-color: {c['border']};
            color: {c['text_muted']};
        }}
        
        QPushButton#dangerButton {{
            background-color: {c['button_danger']};
        }}
        
        QPushButton#dangerButton:hover {{
            background-color: {c['button_danger_hover']};
        }}
        
        QPushButton#secondaryButton {{
            background-color: {c['surface_variant']};
            color: {c['text_primary']};
            border: 1px solid {c['border']};
        }}
        
        QPushButton#secondaryButton:hover {{
            background-color: {c['menu_hover']};
            border-color: {c['primary']};
        }}
        
        QPushButton#successButton {{
            background-color: {c['button_bg']};
        }}
        
        QPushButton#successButton:hover {{
            background-color: {c['button_hover']};
        }}
        
        QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
            background-color: {c['input_bg']};
            color: {c['text_primary']};
            border: 1px solid {c['input_border']};
            border-radius: 6px;
            padding: 8px 12px;
            selection-background-color: {c['selection']};
            selection-color: {c['selection_text']};
        }}
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color: {c['input_focus']};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {c['menu_bg']};
            border: 1px solid {c['menu_border']};
            selection-background-color: {c['selection']};
            selection-color: {c['selection_text']};
            outline: none;
        }}
        
        QListWidget, QTreeWidget, QTableWidget {{
            background-color: {c['surface']};
            color: {c['text_primary']};
            border: 1px solid {c['border']};
            border-radius: 6px;
            outline: none;
            selection-background-color: {c['selection']};
            selection-color: {c['selection_text']};
            alternate-background-color: {c['surface_variant']};
        }}
        
        QListWidget::item, QTreeWidget::item {{
            padding: 8px 12px;
            border: none;
        }}
        
        QListWidget::item:hover, QTreeWidget::item:hover {{
            background-color: {c['menu_hover']};
        }}
        
        QListWidget::item:selected, QTreeWidget::item:selected {{
            background-color: {c['selection']};
            color: {c['selection_text']};
        }}
        
        QHeaderView::section {{
            background-color: {c['surface_variant']};
            color: {c['text_primary']};
            padding: 8px 12px;
            border: 1px solid {c['border']};
            border-left: none;
            border-top: none;
            font-weight: 600;
        }}
        
        QHeaderView::section:first {{
            border-left: none;
        }}
        
        QScrollBar:vertical {{
            background-color: {c['scrollbar_bg']};
            width: 10px;
            border: none;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {c['scrollbar_handle']};
            border-radius: 5px;
            min-height: 30px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {c['scrollbar_hover']};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        
        QScrollBar:horizontal {{
            background-color: {c['scrollbar_bg']};
            height: 10px;
            border: none;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {c['scrollbar_handle']};
            border-radius: 5px;
            min-width: 30px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {c['scrollbar_hover']};
        }}
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
        }}
        
        QGroupBox {{
            border: 1px solid {c['border']};
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 12px;
            font-weight: 600;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 8px;
            color: {c['text_primary']};
            background-color: {c['background']};
        }}
        
        QCheckBox {{
            spacing: 8px;
        }}
        
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {c['border']};
            border-radius: 4px;
            background-color: {c['input_bg']};
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {c['primary']};
            border-color: {c['primary']};
            image: url(:/icons/check.svg);
        }}
        
        QCheckBox::indicator:hover {{
            border-color: {c['primary']};
        }}
        
        QRadioButton::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {c['border']};
            border-radius: 9px;
            background-color: {c['input_bg']};
        }}
        
        QRadioButton::indicator:checked {{
            background-color: {c['primary']};
            border-color: {c['primary']};
        }}
        
        QSlider::groove:horizontal {{
            border: 1px solid {c['border']};
            height: 6px;
            background: {c['surface_variant']};
            border-radius: 3px;
        }}
        
        QSlider::handle:horizontal {{
            background: {c['primary']};
            border: 1px solid {c['primary']};
            width: 18px;
            height: 18px;
            margin: -7px 0;
            border-radius: 9px;
        }}
        
        QSlider::handle:horizontal:hover {{
            background: {c['primary_hover']};
        }}
        
        QProgressBar {{
            border: 1px solid {c['border']};
            border-radius: 6px;
            background-color: {c['surface_variant']};
            text-align: center;
            color: {c['text_primary']};
        }}
        
        QProgressBar::chunk {{
            background-color: {c['primary']};
            border-radius: 5px;
        }}
        
        QToolTip {{
            background-color: {c['tooltip_bg']};
            color: {c['tooltip_text']};
            border: 1px solid {c['border']};
            border-radius: 6px;
            padding: 6px 10px;
        }}
        
        QMenu {{
            background-color: {c['menu_bg']};
            border: 1px solid {c['menu_border']};
            border-radius: 8px;
            padding: 4px;
        }}
        
        QMenu::item {{
            padding: 8px 24px;
            border-radius: 4px;
        }}
        
        QMenu::item:selected {{
            background-color: {c['menu_hover']};
        }}
        
        QMenu::separator {{
            height: 1px;
            background-color: {c['border']};
            margin: 4px 8px;
        }}
        
        QDockWidget {{
            titlebar-close-icon: url(:/icons/close.svg);
            titlebar-normal-icon: url(:/icons/undock.svg);
        }}
        
        QDockWidget::title {{
            background-color: {c['surface_variant']};
            padding: 8px 12px;
            border-bottom: 1px solid {c['border']};
        }}
        
        QStatusBar {{
            background-color: {c['surface']};
            border-top: 1px solid {c['border']};
            color: {c['text_secondary']};
        }}
        
        QSplitter::handle {{
            background-color: {c['border']};
        }}
        
        QSplitter::handle:horizontal {{
            width: 2px;
        }}
        
        QSplitter::handle:vertical {{
            height: 2px;
        }}
        """


THEME_MANAGER = ThemeManager()