"""
Help dialog for JellyMacro - displays feature documentation and credits
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTextBrowser, QPushButton,
    QHBoxLayout, QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QDesktopServices
from PySide6.QtCore import QUrl

from src.theme import THEME_MANAGER


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("JellyMacro Help")
        self.resize(800, 600)
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Help content browser
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(True)
        self._browser.setOpenLinks(False)
        
        self._browser.setHtml(self._get_help_content())
        layout.addWidget(self._browser)
        
        # Link to documentation
        link_layout = QHBoxLayout()
        self._docs_btn = QPushButton("Open Documentation")
        self._docs_btn.clicked.connect(self._open_docs)
        link_layout.addWidget(self._docs_btn)
        link_layout.addStretch()
        layout.addLayout(link_layout)
        
        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        THEME_MANAGER.theme_changed.connect(self._on_theme_changed)
        self._on_theme_changed("")
    
    def _get_help_content(self) -> str:
        c = THEME_MANAGER.colors
        
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 14px; line-height: 1.6; color: {c['text_primary']}; }}
                h1 {{ color: {c['primary']}; font-size: 24px; margin-top: 20px; }}
                h2 {{ color: {c['secondary']}; font-size: 18px; margin-top: 15px; border-bottom: 1px solid {c['border']}; padding-bottom: 5px; }}
                h3 {{ color: {c['text_secondary']}; font-size: 15px; margin-top: 10px; }}
                ul {{ margin-top: 5px; }}
                li {{ margin-bottom: 5px; }}
                code {{ background-color: {c['surface_variant']}; padding: 2px 6px; border-radius: 3px; color: {c['secondary']}; }}
                .credit {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid {c['border']}; color: {c['text_secondary']}; text-align: center; }}
            </style>
        </head>
        <body>
            <h1>JellyMacro - User Guide</h1>
            <p>JellyMacro is an advanced macro automation tool designed specifically for Roblox.
               It allows you to record, save, and execute complex action sequences with conditional logic.</p>
            
            <h2>Main Features</h2>
            
            <h3>1. Screen Capture & Canvas</h3>
            <ul>
                <li>The main window contains an 800x800 pixel canvas with a "hole in the middle" design</li>
                <li>This canvas serves as the reference area for image recognition and screenshots</li>
                <li>Use "Auto-Fit Roblox" to position Roblox into the canvas area</li>
                <li>Click "Refresh Screen" to update the canvas view</li>
            </ul>
            
            <h3>2. Recording & Playing Macros</h3>
            <ul>
                <li><b>Record</b> (F9): Start recording your mouse clicks and keyboard inputs</li>
                <li><b>Stop</b>: Stop the current recording</li>
                <li><b>Play</b> (F8): Execute the recorded macro sequence</li>
                <li><b>Pause</b> (F10): Pause the macro execution</li>
            </ul>
            
            <h3>3. Action List</h3>
            <ul>
                <li>All recorded actions appear in the <b>Actions</b> tab</li>
                <li>Columns show: Serial Number, Action Name, Duration, Enabled status</li>
                <li>Drag actions using the grab bar to reorder them</li>
                <li>Right-click any action to edit, duplicate, or delete it</li>
                <li>Disabled actions (unchecked) are skipped during playback</li>
            </ul>
            
            <h3>4. Adding Actions Manually</h3>
            <ul>
                <li>Click "Add Action" to open the action type selector</li>
                <li>Choose from: Click, Key Press, Type Text, Mouse Move, Drag, Wait, Screenshot</li>
                <li>Conditional actions: If Image Visible, If Image Not Visible, If Variable</li>
                <li>Flow control: Loop Start, Loop End, Break, Continue</li>
                <li>Other: Set Variable, Counter Check, Discord Send</li>
            </ul>
            
            <h3>5. Conditionals & Image Recognition</h3>
            <ul>
                <li><b>If Image Visible</b>: Checks if a specified image appears on screen; skips the block if not found</li>
                <li><b>If Image Not Visible</b>: Opposite of above</li>
                <li><b>Find Image</b>: Searches for an image and optionally clicks on it</li>
                <li><b>Wait for Image</b>: Waits until an image appears (with timeout)</li>
                <li>Use the <b>Image Collection</b> tab to capture and manage reference images</li>
            </ul>
            
            <h3>6. Saving & Duplicating Sections</h3>
            <ul>
                <li>Use "Save Macro" to save your entire action sequence to a file</li>
                <li>"Load Macro" to load previously saved macros</li>
                <li>Select multiple actions and use "Duplicate Selection" to save them as a reusable section</li>
                <li>Sections can be used to create loops more efficiently</li>
            </ul>
            
            <h3>7. Discord Webhook Integration</h3>
            <ul>
                <li>Configure via Settings &rarr; Discord Settings</li>
                <li>Paste your Discord webhook URL</li>
                <li>Enable to send a screenshot and status update every 30 minutes (configurable)</li>
                <li>Toggle screenshot inclusion and counter/variable display</li>
                <li>Use "Test Webhook" to verify your configuration</li>
            </ul>
            
            <h3>8. Counter System</h3>
            <ul>
                <li>Track in-game values like gems, tokens, and resources</li>
                <li>Add counters in the <b>Counters</b> tab by selecting an indicator image</li>
                <li>Counters update automatically at the configured interval</li>
                <li>Counter changes are detected by checking the screen for the indicator image</li>
                <li>OCR can be enabled in Settings for reading numeric values</li>
            </ul>
            
            <h3>9. Screenshot Collection Tool</h3>
            <ul>
                <li>Found in the <b>Image Collection</b> tab</li>
                <li>Choose capture mode: Full Canvas, Manual Region, or Roblox Window</li>
                <li>Enter a descriptive name and category for each image</li>
                <li>Previews are shown after capture</li>
                <li>All images are stored in: <code>assets/images/categories/</code></li>
            </ul>
            
            <h3>10. Themes</h3>
            <ul>
                <li>Switch between <b>Dark Mode</b> (azure blue to jade green gradient) and
                    <b>Light Mode</b> (light pink to light blue gradient)</li>
                <li>Use the theme toggle button in the toolbar or Settings tab</li>
            </ul>
            
            <h3>11. Window Placement</h3>
            <ul>
                <li>The main window can be resized or maximized</li>
                <li>The 800x800 canvas maintains a consistent size for image recognition</li>
                <li>Drag the Roblox window into the canvas, or use Auto-Fit</li>
            </ul>
            
            <div class="credit">
                <p><b>JellyMacro</b><br>v1.0.0<br>Created for Roblox Macro Automation</p>
                <p><b>Credit:</b> Xeu</p>
            </div>
        </body>
        </html>
        """
    
    def _on_theme_changed(self, theme_name: str):
        c = THEME_MANAGER.colors
        self._browser.document().setDefaultStyleSheet(f"""
            body {{ background-color: {c['surface']}; }}
            QTextBrowser {{ background-color: {c['surface']}; }}
        """)
        self._browser.setHtml(self._get_help_content())
    
    def _open_docs(self):
        QDesktopServices.openUrl(QUrl("https://github.com/CloudCatcher99/JellyMacro"))