"""
Screenshot collection tool for JellyMacro - captures screenshots for image recognition
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFormLayout,
    QGroupBox, QToolButton, QLineEdit, QComboBox, QSpinBox,
    QPushButton, QSizePolicy, QFrame, QDialog, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, Signal, QRect, QPoint
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QFont
from typing import Optional, List
import cv2
import numpy as np
import pyautogui

from src.vision import IMAGE_MANAGER, SCREENSHOT_TOOL
from src.actions import Rect, Point
from src.theme import THEME_MANAGER


class ScreenSelectorDialog(QDialog):
    """Dialog for selecting a screen region"""
    
    selected = Signal(QRect)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)
        
        screen = QApplication.primaryScreen()
        self._screen_geom = screen.availableGeometry()
        self._select_start: Optional[QPoint] = None
        self._select_end: Optional[QPoint] = None
        self._selecting = False
        
        self.showFullScreen()
        self.activateWindow()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._select_start = event.globalPosition().toQPoint()
            self._select_end = self._select_start
            self._selecting = True
            self.update()
    
    def mouseMoveEvent(self, event):
        if self._selecting:
            self._select_end = event.globalPosition().toQPoint()
            self.update()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._selecting:
            self._select_end = event.globalPosition().toQPoint()
            self._selecting = False
            self.update()
            
            if self._select_start and self._select_end:
                rect = QRect(
                    min(self._select_start.x(), self._select_end.x()),
                    min(self._select_start.y(), self._select_end.y()),
                    abs(self._select_end.x() - self._select_start.x()),
                    abs(self._select_end.y() - self._select_start.y())
                )
                if rect.width() > 10 and rect.height() > 10:
                    self.selected.emit(rect)
                    self.accept()
                else:
                    self._selecting = True
                    self.update()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        
        if not self._selecting:
            # Dim the screen to indicate selection mode
            painter.fillRect(self._screen_geom, QColor(0, 0, 0, 100))
            
            # Instructions
            painter.setPen(QPen(QColor(255, 255, 255)))
            font = painter.font()
            font.setPointSize(16)
            painter.setFont(font)
            painter.drawText(self._screen_geom, Qt.AlignTop | Qt.AlignHCenter | Qt.TextWordWrap, 
                            "Select a region to capture\nDrag to select, press ESC to cancel")
            return
        
        # Create dimming overlay
        painter.fillRect(self._screen_geom, QColor(0, 0, 0, 150))
        
        sel_rect = QRect(
            min(self._select_start.x(), self._select_end.x()),
            min(self._select_start.y(), self._select_end.y()),
            abs(self._select_end.x() - self._select_start.x()),
            abs(self._select_end.y() - self._select_start.y())
        )
        
        # Clear the selection area
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.fillRect(sel_rect, QColor(0, 0, 0, 0))
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        
        # Draw selection border
        pen = QPen(QColor(0, 255, 0, 200))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(sel_rect)


class ScreenshotToolWidget(QWidget):
    image_collected = Signal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._selector: Optional[ScreenSelectorDialog] = None
        self._capture_preview: Optional[QPixmap] = None
        self._current_mode = "canvas"
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("Screenshot Collection Tool")
        title_font = QFont("Segoe UI", 14, QFont.Bold)
        title.setFont(title_font)
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        # Capture options group
        capture_group = QGroupBox("Capture Mode")
        capture_layout = QFormLayout(capture_group)
        
        self.full_radio = QPushButton("Full Canvas (800x800)")
        self.region_radio = QPushButton("Select Region Manually")
        self.window_radio = QPushButton("Capture Roblox Window")
        
        self.full_radio.setCheckable(True)
        self.full_radio.setChecked(True)
        
        for btn in [self.full_radio, self.region_radio, self.window_radio]:
            btn.clicked.connect(lambda _, b=btn: self._set_mode(b))
        
        capture_layout.addRow(self.full_radio)
        capture_layout.addRow(self.region_radio)
        capture_layout.addRow(self.window_radio)
        
        layout.addWidget(capture_group)
        
        # Image naming
        naming_group = QGroupBox("Image Details")
        naming_layout = QFormLayout(naming_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter image name (e.g. 'gem_icon')")
        naming_layout.addRow("Image Name:", self.name_edit)
        
        self.category_combo = QComboBox()
        self.category_combo.addItems(["general", "ui_elements", "game_objects", "buttons", "icons"])
        naming_layout.addRow("Category:", self.category_combo)
        
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Optional description")
        naming_layout.addRow("Description:", self.desc_edit)
        
        layout.addWidget(naming_group)
        
        # Preview
        self._preview_label = QLabel()
        self._preview_label.setFixedSize(200, 200)
        self._preview_label.setAlignment(Qt.AlignCenter)
        c = THEME_MANAGER.colors
        self._preview_label.setStyleSheet(f"""
            QLabel {{
                background-color: {c['surface']};
                border: 2px dashed {c['border']};
                border-radius: 8px;
                color: {c['text_secondary']};
            }}
        """)
        self._preview_label.setText("No preview available")
        
        preview_layout = QHBoxLayout()
        preview_layout.addWidget(QLabel("Preview:"))
        preview_layout.addStretch()
        layout.addLayout(preview_layout)
        layout.addWidget(self._preview_label, alignment=Qt.AlignCenter)
        
        # Capture button
        self.capture_btn = QPushButton("Capture Image")
        self.capture_btn.setToolTip("Capture the selected area and save")
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.capture_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.capture_btn.clicked.connect(self._capture_image)
        
        # Collected images list
        images_group = QGroupBox("Collected Images")
        images_layout = QVBoxLayout(images_group)
        
        list_layout = QHBoxLayout()
        list_layout.addWidget(QLabel("Image:"))
        self._images_list = QComboBox()
        list_layout.addWidget(self._images_list, 1)
        
        self._view_btn = QPushButton("View")
        self._delete_img_btn = QPushButton("Delete")
        list_layout.addWidget(self._view_btn)
        list_layout.addWidget(self._delete_img_btn)
        
        images_layout.addLayout(list_layout)
        layout.addWidget(images_group)
        
        self._view_btn.clicked.connect(self._view_selected_image)
        self._delete_img_btn.clicked.connect(self._delete_selected_image)
        
        layout.addStretch()
        
        THEME_MANAGER.theme_changed.connect(self._on_theme_changed)
    
    def _on_theme_changed(self, theme_name: str):
        c = THEME_MANAGER.colors
        self._preview_label.setStyleSheet(f"""
            QLabel {{
                background-color: {c['surface']};
                border: 2px dashed {c['border']};
                border-radius: 8px;
                color: {c['text_secondary']};
            }}
        """)
    
    def _set_mode(self, button):
        if button == self.full_radio:
            self._current_mode = "canvas"
        elif button == self.region_radio:
            self._current_mode = "region"
        elif button == self.window_radio:
            self._current_mode = "window"
        
        for btn in [self.full_radio, self.region_radio, self.window_radio]:
            btn.setChecked(btn == button)
    
    def start_capture_mode(self):
        self.setEnabled(True)
    
    def _capture_image(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "No Name", "Please enter an image name")
            return
        
        category = self.category_combo.currentText()
        description = self.desc_edit.text().strip()
        
        if self._current_mode == "canvas":
            try:
                screenshot = pyautogui.screenshot(
                    region=(0, 0, 800, 800)
                )
                image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                stored = IMAGE_MANAGER.add_image(name, image, category, description)
                self.image_collected.emit(name, stored.path if stored else "")
                self._refresh_images_list()
                self._update_preview(image)
            except Exception as e:
                print(f"Capture error: {e}")
                QMessageBox.critical(self, "Error", f"Capture failed: {e}")
        
        elif self._current_mode == "region":
            self._open_region_selector()
        
        elif self._current_mode == "window":
            self._capture_window()
    
    def _open_region_selector(self):
        if self._selector is None:
            self._selector = ScreenSelectorDialog(self)
            self._selector.selected.connect(self._on_region_selected)
            self._selector.finished.connect(self._on_selector_closed)
        self._selector.show()
    
    def _on_region_selected(self, rect: QRect):
        try:
            screenshot = pyautogui.screenshot(
                region=(rect.x(), rect.y(), rect.width(), rect.height())
            )
            image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            name = self.name_edit.text().strip()
            if name:
                stored = IMAGE_MANAGER.add_image(name, image, self.category_combo.currentText(),
                                                 self.desc_edit.text().strip())
                self.image_collected.emit(name, stored.path if stored else "")
                self._refresh_images_list()
                self._update_preview(image)
        except Exception as e:
            print(f"Region capture error: {e}")
    
    def _on_selector_closed(self):
        if self._selector:
            self._selector.deleteLater()
            self._selector = None
    
    def _capture_window(self):
        try:
            import win32gui
            import win32ui
            import win32con
            
            hwnd = win32gui.FindWindow(None, "Roblox")
            if not hwnd:
                QMessageBox.warning(self, "Window Not Found", "Roblox window not found")
                return
            
            left, top, right, bot = win32gui.GetWindowRect(hwnd)
            w = right - left
            h = bot - top
            
            hwnd_dc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()
            
            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mfc_dc, w, h)
            save_dc.SelectObject(save_bitmap)
            
            win32gui.PrintWindow(hwnd, save_dc.GetSafeHdc(), 3)
            
            bmpinfo = save_bitmap.GetInfo()
            bmpstr = save_bitmap.GetBitmapBits(True)
            
            image = np.frombuffer(bmpstr, dtype=np.uint8).reshape((h, w, 4))
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
            
            win32gui.DeleteObject(save_bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)
            
            name = self.name_edit.text().strip()
            if name:
                stored = IMAGE_MANAGER.add_image(name, image, self.category_combo.currentText(),
                                                 self.desc_edit.text().strip())
                self.image_collected.emit(name, stored.path if stored else "")
                self._refresh_images_list()
                self._update_preview(image)
        except ImportError:
            QMessageBox.warning(self, "Feature Unavailable", 
                              "Window capture requires pywin32 (Windows only)")
    
    def _refresh_images_list(self):
        self._images_list.blockSignals(True)
        self._images_list.clear()
        images = IMAGE_MANAGER.get_all_images()
        for img in images:
            self._images_list.addItem(img.name, img.name)
        self._images_list.blockSignals(False)
    
    def _update_preview(self, image: np.ndarray):
        if image is None:
            self._preview_label.setText("No preview available")
            return
        
        h, w = image.shape[:2]
        bytes_per_line = w * 3
        qimage = QImage(image.data, w, h, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(qimage).scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._preview_label.setPixmap(pixmap)
        self._preview_label.setText("")
    
    def _view_selected_image(self):
        name = self._images_list.currentData()
        if name:
            image = IMAGE_MANAGER.load_image(name)
            if image is not None:
                dialog = QDialog(self, Qt.Window)
                dialog.setWindowTitle(f"Image: {name}")
                layout = QVBoxLayout(dialog)
                
                h, w = image.shape[:2]
                bytes_per_line = w * 3
                qimage = QImage(image.data, w, h, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
                pixmap = QPixmap.fromImage(qimage)
                
                label = QLabel()
                label.setPixmap(pixmap)
                layout.addWidget(label)
                
                close_btn = QPushButton("Close")
                close_btn.clicked.connect(dialog.close)
                layout.addWidget(close_btn)
                
                dialog.resize(min(w, 800), min(h, 600))
                dialog.exec()
    
    def _delete_selected_image(self):
        name = self._images_list.currentData()
        if name:
            IMAGE_MANAGER.remove_image(name)
            self._refresh_images_list()