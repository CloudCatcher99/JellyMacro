"""
Settings dialog for JellyMacro - configures application-wide settings
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout,
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox,
    QPushButton, QGroupBox, QLabel, QDialogButtonBox, QColorDialog
)
from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import QFont

from src.config import CONFIG, AppConfig
from src.theme import THEME_MANAGER


class SettingsDialog(QDialog):
    settings_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("JellyMacro Settings")
        self.resize(600, 500)
        
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Canvas settings
        canvas_group = QGroupBox("Canvas Settings")
        canvas_layout = QFormLayout(canvas_group)
        
        self.canvas_width = QSpinBox()
        self.canvas_width.setRange(100, 4000)
        self.canvas_width.setValue(800)
        canvas_layout.addRow("Canvas Width:", self.canvas_width)
        
        self.canvas_height = QSpinBox()
        self.canvas_height.setRange(100, 4000)
        self.canvas_height.setValue(800)
        canvas_layout.addRow("Canvas Height:", self.canvas_height)
        
        self.auto_fit_check = QCheckBox("Auto-fit Roblox on startup")
        canvas_layout.addRow(self.auto_fit_check)
        
        layout.addWidget(canvas_group)
        
        # Hotkeys
        hotkeys_group = QGroupBox("Hotkeys")
        hotkeys_layout = QFormLayout(hotkeys_group)
        
        self.start_stop_hotkey = QLineEdit()
        self.start_stop_hotkey.setMaxLength(20)
        self.start_stop_hotkey.setToolTip("Hotkey to start/pause playback")
        hotkeys_layout.addRow("Start/Stop:", self.start_stop_hotkey)
        
        self.record_hotkey = QLineEdit()
        self.record_hotkey.setMaxLength(20)
        self.record_hotkey.setToolTip("Hotkey to start/stop recording")
        hotkeys_layout.addRow("Record:", self.record_hotkey)
        
        self.pause_hotkey = QLineEdit()
        self.pause_hotkey.setMaxLength(20)
        hotkeys_layout.addRow("Pause:", self.pause_hotkey)
        
        self.screenshot_hotkey = QLineEdit()
        self.screenshot_hotkey.setMaxLength(20)
        hotkeys_layout.addRow("Screenshot:", self.screenshot_hotkey)
        
        layout.addWidget(hotkeys_group)
        
        # Counter settings
        counter_group = QGroupBox("Counter Settings")
        counter_layout = QFormLayout(counter_group)
        
        self.counter_enabled = QCheckBox("Enable counters")
        counter_layout.addRow(self.counter_enabled)
        
        self.update_interval = QDoubleSpinBox()
        self.update_interval.setRange(0.1, 60)
        self.update_interval.setSingleValue(0.1)
        self.update_interval.setSuffix("s")
        counter_layout.addRow("Update Interval:", self.update_interval)
        
        self.ocr_check = QCheckBox("Enable OCR for counter values")
        counter_layout.addRow(self.ocr_check)
        
        layout.addWidget(counter_group)
        
        # Action settings
        action_group = QGroupBox("Action Settings")
        action_layout = QFormLayout(action_group)
        
        self.default_delay = QDoubleSpinBox()
        self.default_delay.setRange(0, 10)
        self.default_delay.setSingleValue(0.01)
        self.default_delay.setSuffix("s")
        action_layout.addRow("Default Delay:", self.default_delay)
        
        self.click_duration = QDoubleSpinBox()
        self.click_duration.setRange(0, 5)
        self.click_duration.setSingleValue(0.01)
        self.click_duration.setSuffix("s")
        action_layout.addRow("Click Duration:", self.click_duration)
        
        self.key_press_duration = QDoubleSpinBox()
        self.key_press_duration.setRange(0, 5)
        self.key_press_duration.setSingleValue(0.01)
        self.key_press_duration.setSuffix("s")
        action_layout.addRow("Key Press Duration:", self.key_press_duration)
        
        layout.addWidget(action_group)
        
        # Theme settings
        theme_group = QGroupBox("Theme")
        theme_layout = QFormLayout(theme_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        theme_layout.addRow("Default Theme:", self.theme_combo)
        
        self.custom_colors_btn = QPushButton("Custom Colors")
        theme_layout.addRow(self.custom_colors_btn)
        
        layout.addWidget(theme_group)
        
        # Paths
        paths_group = QGroupBox("Paths")
        paths_layout = QFormLayout(paths_group)
        
        self.image_folder = QLineEdit()
        self.image_folder.setReadOnly(True)
        paths_layout.addRow("Image Folder:", self.image_folder)
        
        self.macro_folder = QLineEdit()
        self.macro_folder.setReadOnly(True)
        paths_layout.addRow("Macro Folder:", self.macro_folder)
        
        layout.addWidget(paths_group)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self.apply_settings)
        layout.addWidget(button_box)
        
        self.custom_colors_btn.clicked.connect(self._open_color_dialog)
    
    def _load_settings(self):
        config = CONFIG.get()
        
        self.canvas_width.setValue(config.canvas.width)
        self.canvas_height.setValue(config.canvas.height)
        self.auto_fit_check.setChecked(config.canvas.auto_fit_roblox)
        
        self.start_stop_hotkey.setText(config.hotkeys.get("start_stop", "f8"))
        self.record_hotkey.setText(config.hotkeys.get("record", "f9"))
        self.pause_hotkey.setText(config.hotkeys.get("pause", "f10"))
        self.screenshot_hotkey.setText(config.hotkeys.get("screenshot", "f11"))
        
        self.counter_enabled.setChecked(config.counters.enabled)
        self.update_interval.setValue(config.counters.update_interval)
        self.ocr_check.setChecked(config.counters.ocr_enabled)
        
        self.default_delay.setValue(config.actions.default_delay)
        self.click_duration.setValue(config.actions.click_duration)
        self.key_press_duration.setValue(config.actions.key_press_duration)
        
        self.theme_combo.setCurrentIndex(0 if config.theme.dark_mode else 1)
        
        self.image_folder.setText(config.image_folder)
        self.macro_folder.setText(config.macro_folder)
    
    def apply_settings(self):
        config = CONFIG.get()
        
        config.canvas.width = self.canvas_width.value()
        config.canvas.height = self.canvas_height.value()
        config.canvas.auto_fit_roblox = self.auto_fit_check.isChecked()
        
        config.hotkeys = {
            "start_stop": self.start_stop_hotkey.text(),
            "record": self.record_hotkey.text(),
            "pause": self.pause_hotkey.text(),
            "screenshot": self.screenshot_hotkey.text()
        }
        
        config.counters.enabled = self.counter_enabled.isChecked()
        config.counters.update_interval = self.update_interval.value()
        config.counters.ocr_enabled = self.ocr_check.isChecked()
        
        config.actions.default_delay = self.default_delay.value()
        config.actions.click_duration = self.click_duration.value()
        config.actions.key_press_duration = self.key_press_duration.value()
        
        config.theme.dark_mode = (self.theme_combo.currentText() == "Dark")
        
        CONFIG.save()
        
        THEME_MANAGER.set_theme("dark" if config.theme.dark_mode else "light")
        
        self.settings_changed.emit()
    
    def accept(self):
        self.apply_settings()
        super().accept()
    
    def _open_color_dialog(self):
        color = QColorDialog.getColor()
        if color.isValid():
            pass