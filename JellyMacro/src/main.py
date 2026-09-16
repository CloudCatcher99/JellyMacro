#!/usr/bin/env python3
"""
JellyMacro - Advanced Macro Automation Tool for Roblox
Author: Xeu
Main entry point for the application
"""

import sys
import os
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QDir
from PySide6.QtGui import QIcon

from src.gui.main_window import MainWindow
from src.theme import THEME_MANAGER
from src.config import CONFIG
from src.engine import ENGINE
from src.discord_webhook import DISCORD_WEBHOOK
from src.vision import IMAGE_MANAGER


def main():
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    app = QApplication(sys.argv)
    app.setApplicationName("JellyMacro")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Xeu")
    
    # Apply theme
    config = CONFIG.get()
    if config.theme.dark_mode:
        THEME_MANAGER.set_theme("dark")
    else:
        THEME_MANAGER.set_theme("light")
    
    app.setStyleSheet(THEME_MANAGER.get_stylesheet())
    
    # Set application icon
    icon_path = Path(__file__).parent.parent / "assets" / "icons" / "jellymacro.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Create and show main window
    window = MainWindow()
    window.show()
    window.raise_()
    window.activateWindow()
    
    # Start Discord webhook if configured
    if config.discord.enabled and config.discord.webhook_url:
        DISCORD_WEBHOOK.configure(
            webhook_url=config.discord.webhook_url,
            enabled=config.discord.enabled,
            interval_minutes=config.discord.interval_minutes,
            send_screenshot=config.discord.send_screenshot
        )
        DISCORD_WEBHOOK.start()
    
    # Connect engine signals
    ENGINE.on_state_change = window._on_engine_state_change
    ENGINE.on_action_execute = window._on_engine_action_execute
    ENGINE.on_log = window._on_engine_log
    ENGINE.on_screenshot = window._on_engine_screenshot
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()