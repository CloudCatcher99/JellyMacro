"""
Counter widget for JellyMacro - tracks gems, tokens, etc. via image recognition
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QFormLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QToolButton, QMenu, QLineEdit, QSpinBox,
    QDoubleSpinBox, QComboBox, QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor
from typing import List, Optional, Dict
import time

from src.vision import IMAGE_MANAGER, IMAGE_RECOGNIZER, SCREEN_CAPTURE
from src.actions import Rect, Point
from src.engine import ENGINE
from src.config import CONFIG


class CounterWidget(QWidget):
    counter_changed = Signal(str, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._counters: Dict[str, dict] = {}
        self._update_timer: QTimer = QTimer(self)
        self._update_timer.timeout.connect(self._update_counters)
        
        self._setup_ui()
        self.load_counters()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("Gem & Token Counters")
        title_font = QFont("Segoe UI", 14, QFont.Bold)
        title.setFont(title_font)
        
        add_btn = QToolButton()
        add_btn.setText("Add Counter")
        add_btn.setToolTip("Add a new counter")
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(add_btn)
        layout.addLayout(header)
        
        # Counter list
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["Counter Name", "Current Value", "Indicator Image", "Actions"])
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setSelectionMode(QTableWidget.SingleSelection)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        header_view = self._table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.Stretch)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(3, QHeaderView.Fixed)
        header_view.resizeSection(3, 100)
        
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)
        
        layout.addWidget(self._table)
        
        # Manual refresh button
        refresh_btn = QToolButton()
        refresh_btn.setText("Refresh Counters")
        refresh_btn.setToolTip("Refresh all counter values now")
        
        layout.addWidget(refresh_btn, alignment=Qt.AlignRight)
        
        add_btn.clicked.connect(self._add_counter)
        refresh_btn.clicked.connect(self._update_counters)
        
        # Start auto-update timer
        interval = int(CONFIG.get().counters.update_interval * 1000)
        self._update_timer.start(interval)
    
    def _refresh_table(self):
        self._table.setRowCount(0)
        
        for name, info in self._counters.items():
            row = self._table.rowCount()
            self._table.insertRow(row)
            
            name_item = QTableWidgetItem(name)
            self._table.setItem(row, 0, name_item)
            
            value_item = QTableWidgetItem(str(info.get('value', 0)))
            value_item.setTextAlignment(Qt.AlignCenter)
            value_item.setForeground(QColor("#00ff00") if info.get('value', 0) > info.get('last_value', 0) else QColor("#ff6b6b"))
            self._table.setItem(row, 1, value_item)
            
            image_item = QTableWidgetItem(info.get('image_name', ''))
            image_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 2, image_item)
            
            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_layout.setSpacing(4)
            
            edit_btn = QToolButton()
            edit_btn.setText("Edit")
            edit_btn.setToolTip("Edit counter settings")
            
            del_btn = QToolButton()
            del_btn.setText("Delete")
            del_btn.setToolTip("Delete counter")
            
            action_layout.addWidget(edit_btn)
            action_layout.addWidget(del_btn)
            
            self._table.setCellWidget(row, 3, action_widget)
            
            # Connect button signals with closure
            counter_name = name
            edit_btn.clicked.connect(lambda _, n=counter_name: self._edit_counter(n))
            del_btn.clicked.connect(lambda _, n=counter_name: self._delete_counter(n))
    
    def _add_counter(self):
        name, ok = QInputDialog.getText(self, "Add Counter", "Counter Name:")
        if ok and name:
            images = IMAGE_MANAGER.get_all_images()
            if not images:
                QMessageBox.information(self, "No Images", "Please collect images first")
                return
            
            image_names = [img.name for img in images]
            image_name, ok = QInputDialog.getItem(self, "Select Image", 
                                                   "Select indicator image:", 
                                                   image_names)
            if ok and image_name:
                self._counters[name] = {
                    'value': 0,
                    'last_value': 0,
                    'image_name': image_name,
                    'image_path': IMAGE_MANAGER.get_image(image_name).path if IMAGE_MANAGER.get_image(image_name) else '',
                    'region': None
                }
                self._save_counters()
                self._refresh_table()
                self.counter_changed.emit(name, 0)
    
    def _edit_counter(self, name: str):
        if name not in self._counters:
            return
        
        info = self._counters[name]
        new_name, ok = QInputDialog.getText(self, "Edit Counter", 
                                             "Counter Name:", text=name)
        if ok and new_name and new_name != name:
            self._counters[new_name] = info
            del self._counters[name]
            self._save_counters()
            self._refresh_table()
    
    def _delete_counter(self, name: str):
        if name in self._counters:
            del self._counters[name]
            self._save_counters()
            self._refresh_table()
    
    def _on_context_menu(self, position):
        item = self._table.itemAt(position)
        if item:
            row = item.row()
            menu = QMenu()
            menu.addAction("Edit Counter", lambda: self._edit_counter(row))
            menu.addAction("Delete Counter", lambda: self._delete_counter(row))
            menu.exec(self._table.mapToGlobal(position))
    
    def _update_counters(self):
        for name, info in self._counters.items():
            image_path = info.get('image_path', '')
            if image_path:
                from src.vision import IMAGE_RECOGNIZER
                result = IMAGE_RECOGNIZER.find_image(image_path, 0.8, info.get('region'))
                if result:
                    # In a more complete implementation, we'd do OCR here
                    # For now, just increment
                    info['last_value'] = info.get('value', 0)
                    self.counter_changed.emit(name, info['value'])
        
        self._refresh_table()
    
    def load_counters(self):
        # In a full implementation, we'd load from a config file
        pass
    
    def _save_counters(self):
        # In a full implementation, we'd save to a config file
        pass
    
    def set_counter_value(self, name: str, value: int):
        if name in self._counters:
            self._counters[name]['last_value'] = self._counters[name].get('value', 0)
            self._counters[name]['value'] = value
            self._refresh_table()
            self.counter_changed.emit(name, value)
    
    def reset(self):
        for name in self._counters:
            self._counters[name]['value'] = 0
            self._counters[name]['last_value'] = 0
        self._refresh_table()