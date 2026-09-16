"""
Configuration and settings management for JellyMacro
"""

import json
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict, Any
import os


@dataclass
class DiscordConfig:
    webhook_url: str = ""
    enabled: bool = False
    interval_minutes: int = 30
    send_screenshot: bool = True


@dataclass
class ThemeConfig:
    dark_mode: bool = True
    custom_colors: Dict[str, str] = field(default_factory=dict)


@dataclass
class CanvasConfig:
    width: int = 800
    height: int = 800
    auto_fit_roblox: bool = True


@dataclass
class ActionConfig:
    default_delay: float = 0.1
    click_duration: float = 0.05
    key_press_duration: float = 0.05


@dataclass
class CounterConfig:
    enabled: bool = True
    update_interval: float = 1.0
    ocr_enabled: bool = False


@dataclass
class AppConfig:
    discord: DiscordConfig = field(default_factory=DiscordConfig)
    theme: ThemeConfig = field(default_factory=ThemeConfig)
    canvas: CanvasConfig = field(default_factory=CanvasConfig)
    actions: ActionConfig = field(default_factory=ActionConfig)
    counters: CounterConfig = field(default_factory=CounterConfig)
    hotkeys: Dict[str, str] = field(default_factory=lambda: {
        "start_stop": "f8",
        "record": "f9",
        "pause": "f10",
        "screenshot": "f11"
    })
    image_folder: str = "assets/images"
    macro_folder: str = "macros"
    log_level: str = "INFO"


class ConfigManager:
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            self.config_path = Path.home() / ".jellymacro" / "config.json"
        else:
            self.config_path = Path(config_path)
        
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config = self.load()
    
    def load(self) -> AppConfig:
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                return self._dict_to_config(data)
            except Exception:
                pass
        return AppConfig()
    
    def _dict_to_config(self, data: Dict[str, Any]) -> AppConfig:
        config = AppConfig()
        
        if "discord" in data:
            config.discord = DiscordConfig(**data["discord"])
        if "theme" in data:
            config.theme = ThemeConfig(**data["theme"])
        if "canvas" in data:
            config.canvas = CanvasConfig(**data["canvas"])
        if "actions" in data:
            config.actions = ActionConfig(**data["actions"])
        if "counters" in data:
            config.counters = CounterConfig(**data["counters"])
        if "hotkeys" in data:
            config.hotkeys = data["hotkeys"]
        if "image_folder" in data:
            config.image_folder = data["image_folder"]
        if "macro_folder" in data:
            config.macro_folder = data["macro_folder"]
        if "log_level" in data:
            config.log_level = data["log_level"]
        
        return config
    
    def save(self):
        data = {
            "discord": asdict(self.config.discord),
            "theme": asdict(self.config.theme),
            "canvas": asdict(self.config.canvas),
            "actions": asdict(self.config.actions),
            "counters": asdict(self.config.counters),
            "hotkeys": self.config.hotkeys,
            "image_folder": self.config.image_folder,
            "macro_folder": self.config.macro_folder,
            "log_level": self.config.log_level
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=4)
    
    def get(self) -> AppConfig:
        return self.config
    
    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.save()


CONFIG = ConfigManager()