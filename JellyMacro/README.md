# JellyMacro

A powerful macro automation tool for Roblox, featuring screen capture, action recording, image recognition, and Discord webhook integration.

Built with: PySide6, OpenCV, PyAutoGUI, PyInstaller

## Features

- **Screen Capture & Canvas**: 800x800 pixel canvas for consistent image recognition
- **Recording & Playback**: Record mouse clicks, keystrokes, and waits; save/load macros
- **Conditional Actions**: If image visible, check for picture, find image
- **Image Recognition**: Store screenshots, manage image collections
- **Counter System**: Track gems, tokens, and other in-game values
- **Discord Integration**: Send screenshots to Discord webhook every 30 minutes
- **Themes**: Dark mode (azure blue to jade green) and Light mode (pink to blue)
- **Cross-Platform**: Built with Python and PySide6

## Installation

### From Source (Development)

1. Clone the repository:
   ```bash
   git clone https://github.com/CloudCatcher99/JellyMacro.git
   cd JellyMacro
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python run.py
   ```

### Pre-built Executable (Windows)

Download the latest `JellyMacro.exe` from the releases page or build it yourself:

```bash
python -m PyInstaller --onefile --name "JellyMacro" --icon "assets/icons/jellymacro.ico" run.py
```

## Usage

1. Launch JellyMacro
2. Click "Auto-Fit Roblox" to position Roblox into the canvas
3. Use "Record" to capture your actions
4. Actions appear in the Actions tab - drag to reorder
5. Right-click actions to edit, duplicate, or delete
6. Use "Play" to execute the macro
7. Add conditional actions (If Image Visible, etc.) from the "Add Action" menu
8. Use the "Image Collection" tab to capture reference screenshots
9. Configure Discord webhook in Settings

## Project Structure

```
JellyMacro/
├── src/
│   ├── main.py              # Application entry point
│   ├── actions.py           # Action models and types
│   ├── config.py            # Configuration management
│   ├── engine.py            # Automation engine (recording, playback)
│   ├── vision.py            # Image recognition and screen capture
│   ├── discord_webhook.py   # Discord webhook integration
│   ├── theme.py             # Dark/Light theme management
│   └── gui/
│       ├── main_window.py   # Main application window
│       ├── action_list.py   # Action list with drag-and-drop
│       ├── action_editor.py # Action editing dialog
│       ├── canvas_widget.py # Screen capture canvas
│       ├── counter_widget.py # Gem/token counters
│       ├── screenshot_tool.py# Screenshot collection
│       ├── discord_settings.py # Discord settings dialog
│       ├── settings_dialog.py   # Application settings
│       ├── help_dialog.py       # Help and documentation
│       ├── section_manager.py   # Macro section management
│       └── __init__.py
├── assets/
│   ├── icons/
│   │   └── jellymacro.ico
│   └── images/
│       └── categories/
├── macros/                  # Saved macros
├── build/                   # Build configuration
└── run.py                   # Application entry point
```

## Building the EXE

The application can be packaged into a standalone Windows executable using PyInstaller:

```bash
python -m PyInstaller --clean --noconfirm --onefile --name "JellyMacro" --icon "assets/icons/jellymacro.ico" --add-data "assets;assets" --add-data "macros;macros" run.py
```

The resulting executable can be found in `dist/JellyMacro.exe`.

## Requirements

- Python 3.8+
- Windows 10 (for full functionality with Roblox window detection)
- PySide6
- OpenCV (opencv-python)
- NumPy
- PyAutoGUI
- pynput
- Pillow
- Requests
- PyInstaller (for building)
- pywin32 (Windows only, for window detection)

## License

[License information would go here]

## Credits

Created by **Xeu**