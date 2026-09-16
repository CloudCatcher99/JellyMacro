"""
Main Window for JellyMacro - The primary application window
"""

from PySide6.QtWidgets import (
    QMainWindow, QHBoxLayout, QVBoxLayout, QWidget, QSplitter,
    QTabBar, QTabWidget, QToolBar, QToolButton, QStatusBar,
    QLabel, QSpacerItem, QSizePolicy, QStyle, QStyleOption,
    QStyleOptionTab, QStylePainter, QFrame, QComboBox, QMessageBox,
    QInputDialog, QApplication
)
from PySide6.QtCore import Qt, QSize, Signal, Property, QRect, QPoint
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QAction, QIcon
from PySide6.QtGui import QFont, QFontMetrics, QPalette

from src.theme import THEME_MANAGER
from src.config import CONFIG
from src.engine import ENGINE, PlaybackState
from src.vision import SCREENSHOT_TOOL, IMAGE_MANAGER, SCREEN_CAPTURE
from src.discord_webhook import DISCORD_WEBHOOK

from src.gui.action_list import ActionListWidget
from src.gui.canvas_widget import CanvasWidget
from src.gui.discord_settings import DiscordSettingsDialog
from src.gui.counter_widget import CounterWidget
from src.gui.screenshot_tool import ScreenshotToolWidget
from src.gui.settings_dialog import SettingsDialog
from src.gui.help_dialog import HelpDialog


class GradientTabBar(QTabBar):
    """Custom tab bar with gradient styling"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setExpanding(True)
        self.setDrawBase(False)
        self.setShape(QTabBar.RoundedNorth)
    
    def tabLayoutChange(self):
        super().tabLayoutChange()
        self.setDrawBase(False)


class StyledTabWidget(QTabWidget):
    """Custom tab widget with gradient effects"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_tab_bar()
    
    def _setup_tab_bar(self):
        bar = self.tabBar()
        bar.setExpanding(True)
        bar.setDrawBase(False)
        bar.setShape(QTabBar.RoundedNorth)
        
        # Add new tab button
        self.setMovable(True)
        self.setDocumentMode(True)


class MainWindow(QMainWindow):
    stateChanged = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JellyMacro")
        self.resize(1400, 900)
        self.setMinimumSize(1000, 700)
        
        # State tracking
        self.is_recording = False
        self.is_playing = False
        self.action_count = 0
        self.counter_values = {}
        
        self._setup_ui()
        self._setup_toolbar()
        self._setup_statusbar()
        self._connect_signals()
        
        # Initialize counter values
        self._load_counters()
        
        # Apply theme
        THEME_MANAGER.theme_changed.connect(self._on_theme_changed)
        self._apply_theme()
    
    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        
        # Left panel - Canvas and controls
        left_panel = QVBoxLayout()
        left_panel.setSpacing(12)
        
        # Canvas container with hole-in-middle design
        canvas_container = QFrame()
        canvas_container.setObjectName("canvasContainer")
        canvas_layout = QVBoxLayout(canvas_container)
        canvas_layout.setContentsMargins(12, 12, 12, 12)
        
        self.canvas = CanvasWidget()
        self.canvas.setFixedSize(800, 800)
        canvas_layout.addWidget(self.canvas, alignment=Qt.AlignCenter)
        
        # Canvas controls
        canvas_controls = QHBoxLayout()
        canvas_controls.setSpacing(10)
        
        self.btn_auto_fit = QToolButton()
        self.btn_auto_fit.setText("Auto-Fit Roblox")
        self.btn_auto_fit.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self.btn_auto_fit.setToolTip("Auto-adjust and fit Roblox into the canvas window")
        
        self.btn_refresh_screen = QToolButton()
        self.btn_refresh_screen.setText("Refresh Screen")
        self.btn_refresh_screen.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.btn_refresh_screen.setToolTip("Refresh the canvas screen capture")
        
        self.btn_take_screenshot = QToolButton()
        self.btn_take_screenshot.setText("Collect Image")
        self.btn_take_screenshot.setIcon(self.style().standardIcon(QStyle.SP_DesktopIcon))
        self.btn_take_screenshot.setToolTip("Collect screenshots for image recognition")
        
        canvas_controls.addWidget(self.btn_auto_fit)
        canvas_controls.addWidget(self.btn_refresh_screen)
        canvas_controls.addWidget(self.btn_take_screenshot)
        canvas_controls.addStretch()
        
        left_panel.addWidget(canvas_container)
        left_panel.addLayout(canvas_controls)
        
        # Right panel - Action list and tabs
        right_panel = QVBoxLayout()
        right_panel.setSpacing(12)
        
        # Action list header with controls
        action_header = QHBoxLayout()
        action_header.setSpacing(8)
        
        self.btn_record = QToolButton()
        self.btn_record.setText("Record")
        self.btn_record.setCheckable(True)
        self.btn_record.setToolTip("Start recording actions (F9)")
        
        self.btn_stop_record = QToolButton()
        self.btn_stop_record.setText("Stop")
        self.btn_stop_record.setToolTip("Stop recording")
        self.btn_stop_record.setEnabled(False)
        
        self.btn_play = QToolButton()
        self.btn_play.setText("Play")
        self.btn_play.setCheckable(True)
        self.btn_play.setToolTip("Start playing actions (F8)")
        
        self.btn_pause = QToolButton()
        self.btn_pause.setText("Pause")
        self.btn_pause.setToolTip("Pause playback (F10)")
        self.btn_pause.setEnabled(False)
        
        self.btn_stop = QToolButton()
        self.btn_stop.setText("Stop")
        self.btn_stop.setToolTip("Stop playback")
        self.btn_stop.setEnabled(False)
        
        action_header.addWidget(self.btn_record)
        action_header.addWidget(self.btn_stop_record)
        action_header.addWidget(self.btn_play)
        action_header.addWidget(self.btn_pause)
        action_header.addWidget(self.btn_stop)
        action_header.addStretch()
        
        # Tabs for different functions
        self.tab_widget = StyledTabWidget()
        
        # Actions tab
        self.action_list = ActionListWidget()
        self.action_list.action_added.connect(self._on_action_added)
        self.action_list.action_duplicated.connect(self._on_action_duplicated)
        self.action_list.action_removed.connect(self._on_action_removed)
        
        # Counters tab
        self.counter_widget = CounterWidget()
        self.counter_widget.counter_changed.connect(self._on_counter_changed)
        
        # Screenshot tool tab
        self.screenshot_tool = ScreenshotToolWidget()
        self.screenshot_tool.image_collected.connect(self._on_image_collected)
        
        # Settings tab
        self.settings_widget = QWidget()
        self._setup_settings_tab()
        
        self.tab_widget.addTab(self.action_list, "Actions")
        self.tab_widget.addTab(self.counter_widget, "Counters")
        self.tab_widget.addTab(self.screenshot_tool, "Image Collection")
        self.tab_widget.addTab(self.settings_widget, "Settings")
        
        right_panel.addLayout(action_header)
        right_panel.addWidget(self.tab_widget)
        
        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(right_panel, 2)
        
        # Set initial tab
        self.tab_widget.setCurrentWidget(self.action_list)
    
    def _setup_settings_tab(self):
        layout = QVBoxLayout(self.settings_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        config = CONFIG.get()
        
        # Theme toggle
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Theme:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.setCurrentIndex(0 if config.theme.dark_mode else 1)
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        layout.addLayout(theme_layout)
        
        # Discord settings button
        discord_btn = QToolButton()
        discord_btn.setText("Discord Webhook Settings")
        discord_btn.setToolTip("Configure Discord webhook for status updates")
        
        # Settings button
        settings_btn = QToolButton()
        settings_btn.setText("Advanced Settings")
        settings_btn.setToolTip("Configure application settings")
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(discord_btn)
        button_layout.addWidget(settings_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        layout.addStretch()
        
        discord_btn.clicked.connect(self._open_discord_settings)
        settings_btn.clicked.connect(self._open_settings)
    
    def _setup_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setFixedHeight(40)
        self.addToolBar(toolbar)
        
        # Title label
        title_label = QLabel("JellyMacro")
        title_font = QFont("Segoe UI", 14, QFont.Bold)
        title_label.setFont(title_font)
        toolbar.addWidget(title_label)
        
        toolbar.addSeparator()
        
        # Macro actions
        self.new_action = self._add_toolbar_action(toolbar, "New", "Create new macro")
        self.save_action = self._add_toolbar_action(toolbar, "Save", "Save current macro")
        self.save_as_action = self._add_toolbar_action(toolbar, "Save As", "Save macro as...")
        self.open_action = self._add_toolbar_action(toolbar, "Open", "Open saved macro")
        
        self.new_action.triggered.connect(self._on_new_macro)
        self.save_action.triggered.connect(self._on_save_macro)
        self.save_as_action.triggered.connect(self._on_save_as_macro)
        self.open_action.triggered.connect(self._on_open_macro)
        
        toolbar.addSeparator()
        
        # Theme toggle
        self.theme_action = self._add_toolbar_action(toolbar, "Toggle Theme", "Switch between dark and light mode")
        self.theme_action.setCheckable(True)
        self.theme_action.setChecked(True)
        
        toolbar.addSeparator()
        
        # Help button
        help_action = self._add_toolbar_action(toolbar, "?", "Help and documentation")
        help_action.setToolTip("Help and documentation (credits: Xeu)")
        
        # Spacer
        toolbar.addWidget(QLabel(""))
        toolbar.addSeparator()
        
        # Status indicators
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #8b949e;")
        toolbar.addWidget(self.status_label)
        
        # Connect help action
        help_action.triggered.connect(self._show_help)
        self.theme_action.triggered.connect(self._toggle_theme)
    
    def _add_toolbar_action(self, toolbar, text, tooltip):
        action = QAction(text, self)
        action.setToolTip(tooltip)
        toolbar.addAction(action)
        return action
    
    def _setup_statusbar(self):
        from PySide6.QtWidgets import QStatusBar
        statusbar = self.statusBar()
        statusbar.setFixedHeight(30)
        
        self.status_left = QLabel("Ready")
        statusbar.addWidget(self.status_left)
        
        statusbar.addPermanentWidget(QLabel(" "))
        status_spacer = QLabel()
        status_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        statusbar.addWidget(status_spacer)
        
        self.status_mode = QLabel("Mode: Stopped")
        statusbar.addPermanentWidget(self.status_mode)
        
        statusbar.addPermanentWidget(QLabel(" "))
        status_spacer2 = QLabel()
        status_spacer2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        statusbar.addPermanentWidget(status_spacer2)
        
        self.status_actions = QLabel("Actions: 0")
        statusbar.addPermanentWidget(self.status_actions)
        
        statusbar.addPermanentWidget(QLabel(" "))
        status_spacer3 = QLabel()
        status_spacer3.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        statusbar.addPermanentWidget(status_spacer3)
        
        self.status_theme = QLabel("Theme: Dark")
        statusbar.addPermanentWidget(self.status_theme)
    
    def _connect_signals(self):
        # Engine callbacks
        ENGINE.on_state_change = self._on_engine_state_change
        ENGINE.on_action_execute = self._on_engine_action_execute
        ENGINE.on_log = self._on_engine_log
        ENGINE.on_screenshot = self._on_engine_screenshot
        
        # Connect buttons to engine
        self.btn_record.toggled.connect(self._on_record_toggled)
        self.btn_stop_record.clicked.connect(self._on_stop_record)
        self.btn_play.toggled.connect(self._on_play_toggled)
        self.btn_pause.clicked.connect(self._on_pause_clicked)
        self.btn_stop.clicked.connect(self._on_stop_clicked)
        
        # Auto-fit roblox button
        self.btn_auto_fit.clicked.connect(self._on_auto_fit_clicked)
        
        # Refresh screen button
        self.btn_refresh_screen.clicked.connect(self._on_refresh_screen)
        
        # Screenshot tool button
        self.btn_take_screenshot.clicked.connect(self._on_collect_screenshot)
        
        # Theme
        self.theme_combo.currentTextChanged.connect(self._on_theme_combo_changed)
    
    def _apply_theme(self):
        app = QApplication.instance()
        app.setStyleSheet(THEME_MANAGER.get_stylesheet())
        
        theme_name = THEME_MANAGER.current_theme
        self.status_theme.setText(f"Theme: {theme_name.capitalize()}")
        
        # Update canvas appearance
        self.canvas.update_theme()
        self.canvas.update()
    
    def _on_theme_changed(self, theme_name: str):
        self._apply_theme()
        self._save_theme_setting()
    
    def _save_theme_setting(self):
        config = CONFIG.get()
        config.theme.dark_mode = (THEME_MANAGER.current_theme == "dark")
        CONFIG.save()
    
    def _toggle_theme(self):
        THEME_MANAGER.toggle_theme()
        self.theme_combo.setCurrentIndex(0 if THEME_MANAGER.current_theme == "dark" else 1)
    
    def _on_theme_combo_changed(self, text: str):
        if text == "Dark":
            THEME_MANAGER.set_theme("dark")
        else:
            THEME_MANAGER.set_theme("light")
    
    def _on_engine_state_change(self, state: PlaybackState):
        state_name = state.value
        self.status_mode.setText(f"Mode: {state_name.capitalize()}")
        self.status_left.setText(f"Status: {state_name.capitalize()}")
        
        self.is_recording = (state == PlaybackState.RECORDING)
        self.is_playing = (state == PlaybackState.PLAYING or state == PlaybackState.PAUSED)
        
        self.btn_record.setChecked(self.is_recording)
        self.btn_stop_record.setEnabled(self.is_recording)
        self.btn_play.setChecked(self.is_playing)
        self.btn_pause.setEnabled(self.is_playing)
        self.btn_stop.setEnabled(self.is_playing or self.is_recording)
        
        self.tab_widget.setDisabled(self.is_recording or self.is_playing)
        
        self.stateChanged.emit(state_name)
    
    def _on_engine_action_execute(self, action, index: int):
        self.current_action_index = index
        self.status_actions.setText(f"Actions: {len(ENGINE.actions)} (executing: {index + 1})")
    
    def _on_engine_log(self, message: str):
        self.status_left.setText(f"Log: {message}")
    
    def _on_engine_screenshot(self, screenshot):
        self.canvas.update_screenshot(screenshot)
    
    def _on_record_toggled(self, checked: bool):
        if checked:
            ENGINE.start_recording()
            self.status_left.setText("Recording...")
        else:
            self._on_stop_record()
    
    def _on_stop_record(self):
        if self.is_recording:
            actions = ENGINE.stop_recording()
            self.action_list.set_actions(actions)
            self.action_count = len(actions)
            self.status_actions.setText(f"Actions: {self.action_count}")
            self.btn_record.setChecked(False)
            self.btn_stop_record.setEnabled(False)
    
    def _on_play_toggled(self, checked: bool):
        if checked:
            if not self.action_list.get_actions():
                QMessageBox.information(self, "No Actions", "Please add actions first")
                self.btn_play.setChecked(False)
                return
            self._sync_actions_to_engine()
            ENGINE.start_playback()
            self.status_left.setText("Playing...")
        else:
            ENGINE.stop_playback()
    
    def _on_pause_clicked(self):
        if self.is_playing:
            if ENGINE.state == PlaybackState.PLAYING:
                ENGINE.pause_playback()
                self.btn_pause.setText("Resume")
                self.status_left.setText("Paused")
            else:
                ENGINE.resume_playback()
                self.btn_pause.setText("Pause")
                self.status_left.setText("Playing...")
    
    def _on_stop_clicked(self):
        ENGINE.stop_playback()
        self.btn_play.setChecked(False)
        self.btn_pause.setText("Pause")
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)
    
    def _on_action_added(self):
        self.action_count = len(self.action_list.actions)
        self.status_actions.setText(f"Actions: {self.action_count}")
        self._sync_actions_to_engine()
    
    def _on_action_duplicated(self):
        self._sync_actions_to_engine()
    
    def _on_action_removed(self):
        self.action_count = len(self.action_list.actions)
        self.status_actions.setText(f"Actions: {self.action_count}")
        self._sync_actions_to_engine()
    
    def _sync_actions_to_engine(self):
        ENGINE.set_actions(self.action_list.get_actions())
    
    @property
    def actions(self):
        return self.action_list.get_actions()
    
    def _on_counter_changed(self, name: str, value: int):
        self.counter_values[name] = value
        status_text = f"Counters: {', '.join([f'{k}={v}' for k, v in self.counter_values.items()])}"
        # Update status with counters
    
    def _on_image_collected(self, name: str, image_path: str):
        self.status_left.setText(f"Image collected: {name}")
    
    def _on_auto_fit_clicked(self):
        self.status_left.setText("Auto-fitting Roblox...")
        # This will be implemented - uses win32 API to find and resize Roblox
        try:
            import win32gui
            import win32api
            import win32con
            
            # Find Roblox window
            hwnd = win32gui.FindWindow(None, "Roblox")
            if hwnd:
                # Move and resize to fit canvas
                canvas_rect = self._get_canvas_screen_position()
                win32gui.SetWindowPos(
                    hwnd, None,
                    canvas_rect.x, canvas_rect.y,
                    canvas_rect.width, canvas_rect.height,
                    win32con.SWP_SHOWWINDOW
                )
                self.status_left.setText("Roblox auto-fit complete!")
            else:
                self.status_left.setText("Roblox window not found!")
        except ImportError:
            self.status_left.setText("Auto-fit feature requires Windows pywin32")
    
    def _get_canvas_screen_position(self):
        # Get the screen position of the canvas widget
        pos = self.canvas.mapToGlobal(QPoint(0, 0))
        return QRect(pos.x(), pos.y(), self.canvas.width(), self.canvas.height())
    
    def _on_refresh_screen(self):
        self.canvas.refresh_capture()
    
    def _on_collect_screenshot(self):
        # Open the screenshot collection tool
        self.tab_widget.setCurrentWidget(self.screenshot_tool)
        self.screenshot_tool.start_capture_mode()
    
    def _open_discord_settings(self):
        dialog = DiscordSettingsDialog(self)
        dialog.webhook_updated.connect(self._on_webhook_updated)
        dialog.exec()
    
    def _on_webhook_updated(self):
        config = CONFIG.get()
        if config.discord.enabled and config.discord.webhook_url:
            DISCORD_WEBHOOK.configure(
                webhook_url=config.discord.webhook_url,
                enabled=config.discord.enabled,
                interval_minutes=config.discord.interval_minutes,
                send_screenshot=config.discord.send_screenshot
            )
            DISCORD_WEBHOOK.start()
    
    def _open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()
    
    def _show_help(self):
        dialog = HelpDialog(self)
        dialog.exec()
    
    def _on_new_macro(self):
        if self.action_list.get_actions():
            reply = QMessageBox.question(self, "New Macro", 
                                         "Discard current actions and create new?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
        self.action_list.set_actions([])
        self.action_count = 0
        self.status_actions.setText("Actions: 0")
    
    def _on_save_macro(self):
        if self.action_list.get_actions():
            name, ok = QInputDialog.getText(self, "Save Macro", "Enter macro name:")
            if ok and name:
                from src.engine import MACRO_MANAGER
                filepath = MACRO_MANAGER.save_macro(name)
                QMessageBox.information(self, "Saved", f"Macro saved as: {filepath}")
        else:
            QMessageBox.information(self, "No Actions", "No actions to save")
    
    def _on_save_as_macro(self):
        self._on_save_macro()
    
    def _on_open_macro(self):
        from src.engine import MACRO_MANAGER
        macros = MACRO_MANAGER.list_macros()
        if not macros:
            QMessageBox.information(self, "No Macros", "No saved macros found")
            return
        
        name, ok = QInputDialog.getItem(self, "Open Macro", "Select a macro:", macros)
        if ok and name:
            if MACRO_MANAGER.load_macro(name):
                self.action_list.set_actions(ENGINE.actions)
                self.action_count = len(self.action_list.get_actions())
                self.status_actions.setText(f"Actions: {self.action_count}")



    
    def _load_counters(self):
        config = CONFIG.get()
        if config.counters.enabled:
            self.counter_widget.load_counters()
    
    def closeEvent(self, event):
        ENGINE.stop_playback()
        DISCORD_WEBHOOK.stop()
        self._sync_actions_to_engine()
        super().closeEvent(event)