"""
Canvas widget for JellyMacro - displays the game screen with overlay capabilities
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRect, QTimer, Signal, QPoint
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPixmap,
    QMouseEvent, QPaintEvent, QResizeEvent
)
import numpy as np
import cv2
import pyautogui
from typing import Optional

from src.config import CONFIG
from src.actions import Rect
from src.theme import THEME_MANAGER


class CanvasWidget(QWidget):
    """Canvas widget that displays a 800x800 view of the screen with overlay"""
    
    click_pos = Signal(int, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap: Optional[QPixmap] = None
        self._pixmap_dirty = False
        self._overlay_points: list = []
        self._overlay_rects: list = []
        self._capture_timer: QTimer = QTimer(self)
        self._capture_timer.timeout.connect(self._update_capture)
        
        self._canvas_size = CONFIG.get().canvas
        self._theme_colors: dict = THEME_MANAGER.colors
        
        self.setMouseTracking(True)
        self.setFixedSize(self._canvas_size.width, self._canvas_size.height)
        self.update_theme()
    
    def update_theme(self):
        self._theme_colors = THEME_MANAGER.colors
    
    def resizeEvent(self, event: QResizeEvent):
        self.update()
        super().resizeEvent(event)
    
    def _update_capture(self):
        self.refresh_capture()
    
    def refresh_capture(self):
        try:
            screenshot = pyautogui.screenshot(
                region=(0, 0, self._canvas_size.width, self._canvas_size.height)
            )
            self.update_screenshot(cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR))
        except Exception as e:
            print(f"Capture error: {e}")
    
    def update_screenshot(self, image: np.ndarray):
        """Update the displayed screenshot from a numpy array"""
        if image is None:
            return
        
        h, w = image.shape[:2]
        bytes_per_line = w * 3
        from PySide6.QtGui import QImage
        qimage = QImage(image.data, w, h, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        self._pixmap = QPixmap.fromImage(qimage)
        self._pixmap_dirty = True
        self.update()
    
    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        rect = self.rect()
        c = self._theme_colors
        
        # Draw background border with gradient
        gradient = QPen()
        gradient_brush = QBrush(Qt.NoBrush)
        
        # Outer border with gradient
        border_pen = QPen(QColor(c['canvas_border']))
        border_pen.setWidth(2)
        painter.setPen(border_pen)
        painter.setBrush(QColor(c['canvas_bg']))
        painter.drawRect(rect.adjusted(1, 1, -1, -1))
        
        # Draw screenshot or placeholder
        if self._pixmap and not self._pixmap.isNull():
            # Scale pixmap to fit while maintaining aspect ratio
            pixmap = self._pixmap.scaled(
                self.width() - 4, self.height() - 4,
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            painter.drawPixmap(
                (self.width() - pixmap.width()) // 2,
                (self.height() - pixmap.height()) // 2,
                pixmap
            )
        else:
            # Draw placeholder
            painter.setPen(QPen(QColor(c['text_secondary']), 1, Qt.DashLine))
            painter.drawLine(rect.left() + 20, rect.top() + 20, 
                           rect.right() - 20, rect.bottom() - 20)
            painter.drawLine(rect.left() + 20, rect.bottom() - 20,
                           rect.right() - 20, rect.top() + 20)
            
            painter.setPen(QPen(QColor(c['text_secondary'])))
            font = painter.font()
            font.setPointSize(11)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignCenter, "800×800 Canvas\n(Click Auto-Fit Roblox)")
        
        # Draw overlays if any
        self._draw_overlays(painter)
    
    def _draw_overlays(self, painter: QPainter):
        """Draw click points and rectangle overlays"""
        c = self._theme_colors
        pen = QPen(QColor(c['primary']))
        pen.setWidth(2)
        painter.setPen(pen)
        
        # Draw points
        for point in self._overlay_points:
            painter.drawEllipse(point, 4, 4)
        
        # Draw rectangles
        brush = QBrush(QColor(c['primary']))
        brush.setStyle(Qt.NoBrush)
        for rect in self._overlay_rects:
            painter.drawRect(rect)
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            x, y = event.x(), event.y()
            self.click_pos.emit(x, y)
            self._add_click_point(x, y)
    
    def _add_click_point(self, x: int, y: int):
        from PySide6.QtCore import QPoint
        self._overlay_points.append(QPoint(x, y))
        self.update()
    
    def add_overlay_rect(self, rect: Rect):
        """Add a rectangle overlay to the canvas"""
        self._overlay_rects.append(QRect(rect.x, rect.y, rect.width, rect.height))
        self.update()
    
    def clear_overlays(self):
        """Clear all overlay points and rectangles"""
        self._overlay_points = []
        self._overlay_rects = []
        self.update()
    
    def start_capture_loop(self):
        self._capture_timer.start(100)
    
    def stop_capture_loop(self):
        self._capture_timer.stop()
    
    def auto_fit_roblox(self):
        """Auto-adjust and fit Roblox into the canvas window"""
        try:
            import win32gui
            import win32api
            import win32con
            
            # Find Roblox window
            hwnd = win32gui.FindWindow(None, "Roblox")
            if not hwnd:
                return False
            
            # Get canvas screen position
            parent = self.parentWidget()
            while parent and parent.parentWidget():
                parent = parent.parentWidget()
            
            main_window = parent
            pos = self.mapToGlobal(QPoint(0, 0))
            canvas_rect = QRect(pos.x(), pos.y(), self.width(), self.height())
            
            win32gui.SetWindowPos(
                hwnd, None,
                canvas_rect.x, canvas_rect.y,
                canvas_rect.width, canvas_rect.height,
                win32con.SWP_SHOWWINDOW
            )
            
            return True
        except ImportError:
            return False