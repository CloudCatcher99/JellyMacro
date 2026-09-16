"""
Image recognition and screen capture utilities for JellyMacro
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass, field
import json
import time

import pyautogui
from PIL import Image

from src.config import CONFIG
from src.actions import Rect, Point


@dataclass
class TemplateMatch:
    x: int
    y: int
    width: int
    height: int
    confidence: float
    image_path: str
    
    @property
    def center(self) -> Point:
        return Point(self.x + self.width // 2, self.y + self.height // 2)
    
    @property
    def rect(self) -> Rect:
        return Rect(self.x, self.y, self.width, self.height)


@dataclass
class StoredImage:
    name: str
    path: str
    category: str = "general"
    description: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    size: Tuple[int, int] = (0, 0)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "category": self.category,
            "description": self.description,
            "tags": self.tags,
            "created_at": self.created_at,
            "size": self.size
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StoredImage':
        return cls(**data)


class ImageManager:
    def __init__(self):
        self.image_folder = Path(CONFIG.get().image_folder)
        self.image_folder.mkdir(parents=True, exist_ok=True)
        self.categories_folder = self.image_folder / "categories"
        self.categories_folder.mkdir(parents=True, exist_ok=True)
        
        self.index_file = self.image_folder / "index.json"
        self.images: Dict[str, StoredImage] = {}
        self.load_index()
    
    def load_index(self):
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    data = json.load(f)
                for item in data.get("images", []):
                    img = StoredImage.from_dict(item)
                    self.images[img.name] = img
            except Exception:
                pass
    
    def save_index(self):
        data = {
            "version": "1.0",
            "images": [img.to_dict() for img in self.images.values()]
        }
        with open(self.index_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_image(self, name: str, image: np.ndarray, 
                  category: str = "general", description: str = "",
                  tags: List[str] = None) -> StoredImage:
        category_folder = self.categories_folder / category
        category_folder.mkdir(parents=True, exist_ok=True)
        
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{safe_name}.png"
        filepath = category_folder / filename
        
        counter = 1
        while filepath.exists():
            filename = f"{safe_name}_{counter}.png"
            filepath = category_folder / filename
            counter += 1
        
        cv2.imwrite(str(filepath), image)
        
        h, w = image.shape[:2]
        stored = StoredImage(
            name=name,
            path=str(filepath.relative_to(self.image_folder)),
            category=category,
            description=description,
            tags=tags or [],
            size=(w, h)
        )
        
        self.images[name] = stored
        self.save_index()
        return stored
    
    def remove_image(self, name: str) -> bool:
        if name in self.images:
            img = self.images[name]
            full_path = self.image_folder / img.path
            if full_path.exists():
                full_path.unlink()
            del self.images[name]
            self.save_index()
            return True
        return False
    
    def get_image(self, name: str) -> Optional[StoredImage]:
        return self.images.get(name)
    
    def get_images_by_category(self, category: str) -> List[StoredImage]:
        return [img for img in self.images.values() if img.category == category]
    
    def get_all_images(self) -> List[StoredImage]:
        return list(self.images.values())
    
    def search_images(self, query: str) -> List[StoredImage]:
        query = query.lower()
        return [img for img in self.images.values() 
                if query in img.name.lower() or 
                   query in img.description.lower() or
                   any(query in tag.lower() for tag in img.tags)]
    
    def load_image(self, name: str) -> Optional[np.ndarray]:
        img = self.get_image(name)
        if img:
            full_path = self.image_folder / img.path
            return cv2.imread(str(full_path))
        return None
    
    def get_categories(self) -> List[str]:
        categories = set()
        for img in self.images.values():
            categories.add(img.category)
        return sorted(list(categories))


class ScreenCapture:
    def __init__(self):
        self.canvas_config = CONFIG.get().canvas
    
    def capture_fullscreen(self) -> np.ndarray:
        screenshot = pyautogui.screenshot()
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    
    def capture_region(self, region: Rect) -> np.ndarray:
        screenshot = pyautogui.screenshot(region=(region.x, region.y, region.width, region.height))
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    
    def capture_canvas(self) -> np.ndarray:
        return self.capture_region(Rect(0, 0, self.canvas_config.width, self.canvas_config.height))
    
    def capture_window(self, window_title: str) -> Optional[np.ndarray]:
        import win32gui
        import win32ui
        import win32con
        import win32api
        
        hwnd = win32gui.FindWindow(None, window_title)
        if not hwnd:
            return None
        
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        w = right - left
        h = bottom - top
        
        hwnd_dc = win32gui.GetWindowDC(hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()
        
        save_bitmap = win32ui.CreateBitmap()
        save_bitmap.CreateCompatibleBitmap(mfc_dc, w, h)
        save_dc.SelectObject(save_bitmap)
        
        result = win32gui.PrintWindow(hwnd, save_dc.GetSafeHdc(), 3)
        
        bmpinfo = save_bitmap.GetInfo()
        bmpstr = save_bitmap.GetBitmapBits(True)
        
        img = np.frombuffer(bmpstr, dtype=np.uint8).reshape((h, w, 4))
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        
        win32gui.DeleteObject(save_bitmap.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwnd_dc)
        
        return img if result else None


class ImageRecognizer:
    def __init__(self):
        self.image_manager = ImageManager()
        self.screen_capture = ScreenCapture()
        self.default_confidence = 0.8
    
    def find_image(self, image_path: str, confidence: float = None,
                   region: Optional[Rect] = None) -> Optional[TemplateMatch]:
        if confidence is None:
            confidence = self.default_confidence
        
        full_path = Path(image_path)
        if not full_path.is_absolute():
            full_path = CONFIG.get().image_folder / image_path
        
        if not full_path.exists():
            return None
        
        template = cv2.imread(str(full_path), cv2.IMREAD_COLOR)
        if template is None:
            return None
        
        if region:
            screenshot = self.screen_capture.capture_region(region)
            offset_x, offset_y = region.x, region.y
        else:
            screenshot = self.screen_capture.capture_canvas()
            offset_x, offset_y = 0, 0
        
        if screenshot is None or screenshot.size == 0:
            return None
        
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= confidence:
            h, w = template.shape[:2]
            return TemplateMatch(
                x=max_loc[0] + offset_x,
                y=max_loc[1] + offset_y,
                width=w,
                height=h,
                confidence=max_val,
                image_path=str(full_path)
            )
        
        return None
    
    def find_all_images(self, image_path: str, confidence: float = None,
                        region: Optional[Rect] = None, 
                        max_results: int = 10) -> List[TemplateMatch]:
        if confidence is None:
            confidence = self.default_confidence
        
        full_path = Path(image_path)
        if not full_path.is_absolute():
            full_path = CONFIG.get().image_folder / image_path
        
        if not full_path.exists():
            return []
        
        template = cv2.imread(str(full_path), cv2.IMREAD_COLOR)
        if template is None:
            return []
        
        if region:
            screenshot = self.screen_capture.capture_region(region)
            offset_x, offset_y = region.x, region.y
        else:
            screenshot = self.screen_capture.capture_canvas()
            offset_x, offset_y = 0, 0
        
        if screenshot is None or screenshot.size == 0:
            return []
        
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        h, w = template.shape[:2]
        
        matches = []
        threshold = confidence
        
        while len(matches) < max_results:
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            if max_val < threshold:
                break
            
            matches.append(TemplateMatch(
                x=max_loc[0] + offset_x,
                y=max_loc[1] + offset_y,
                width=w,
                height=h,
                confidence=max_val,
                image_path=str(full_path)
            ))
            
            cv2.rectangle(result, max_loc, (max_loc[0] + w, max_loc[1] + h), 0, -1)
        
        return matches
    
    def wait_for_image(self, image_path: str, confidence: float = None,
                       timeout: float = 10.0, region: Optional[Rect] = None,
                       check_interval: float = 0.1) -> Optional[TemplateMatch]:
        start_time = time.time()
        while time.time() - start_time < timeout:
            match = self.find_image(image_path, confidence, region)
            if match:
                return match
            time.sleep(check_interval)
        return None
    
    def is_image_visible(self, image_path: str, confidence: float = None,
                         region: Optional[Rect] = None) -> bool:
        return self.find_image(image_path, confidence, region) is not None
    
    def click_image(self, image_path: str, confidence: float = None,
                    region: Optional[Rect] = None, offset: Point = None) -> bool:
        match = self.find_image(image_path, confidence, region)
        if match:
            click_x = match.center.x
            click_y = match.center.y
            if offset:
                click_x += offset.x
                click_y += offset.y
            pyautogui.click(click_x, click_y)
            return True
        return False


class ScreenshotTool:
    def __init__(self):
        self.screen_capture = ScreenCapture()
        self.image_manager = ImageManager()
        self.capturing = False
        self.start_point: Optional[Point] = None
        self.current_rect: Optional[Rect] = None
    
    def start_capture(self):
        self.capturing = True
    
    def stop_capture(self):
        self.capturing = False
    
    def capture_selection(self, rect: Rect, name: str, 
                          category: str = "general") -> Optional[StoredImage]:
        screenshot = self.screen_capture.capture_region(rect)
        if screenshot is not None and screenshot.size > 0:
            return self.image_manager.add_image(name, screenshot, category)
        return None
    
    def capture_full_canvas(self, name: str, category: str = "general") -> Optional[StoredImage]:
        screenshot = self.screen_capture.capture_canvas()
        if screenshot is not None:
            return self.image_manager.add_image(name, screenshot, category)
        return None


IMAGE_MANAGER = ImageManager()
SCREEN_CAPTURE = ScreenCapture()
IMAGE_RECOGNIZER = ImageRecognizer()
SCREENSHOT_TOOL = ScreenshotTool()