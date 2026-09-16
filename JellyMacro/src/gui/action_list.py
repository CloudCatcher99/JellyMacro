"""
Action list widget for JellyMacro - displays and manages actions with drag-and-drop
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QHBoxLayout, QToolButton, QMenu,
    QToolBar, QSpacerItem, QMessageBox, QInputDialog
)
from PySide6.QtCore import Qt, Signal, QPoint, QSize, QRect
from PySide6.QtGui import QColor, QAction, QIcon, QFont, QCursor
from PySide6.QtWidgets import QAbstractItemView

from src.actions import Action, ActionType, ClickType, create_action_with_prompt
from src.engine import ENGINE
from src.vision import IMAGE_MANAGER
from typing import List, Optional
from pathlib import Path

try:
    from PySide6.QtWidgets import QStyle
except:
    QStyle = None

class ActionListWidget(QWidget):
    action_added = Signal()
    action_duplicated = Signal()
    action_removed = Signal()
    action_modified = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._actions: List[Action] = []
        self._drag_start_position: Optional[QPoint] = None
        self._current_row: int = -1
        
        self._setup_ui()
        self._setup_add_menu()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("Action Sequence")
        title_font = QFont("Segoe UI", 14, QFont.Bold)
        title.setFont(title_font)
        
        add_btn = QToolButton()
        add_btn.setText("Add Action")
        add_btn.setToolTip("Add a new action")
        add_btn.clicked.connect(lambda: self._show_add_menu(add_btn.mapToGlobal(QPoint(0, add_btn.height()))))
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(add_btn)
        layout.addLayout(header)
        
        # Toolbar for section management
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setFixedHeight(35)
        
        self.btn_duplicate_section = QToolButton()
        self.btn_duplicate_section.setText("Duplicate Selection")
        self.btn_duplicate_section.setToolTip("Duplicate selected actions as a reusable section")
        
        self.btn_delete_section = QToolButton()
        self.btn_delete_section.setText("Delete Selection")
        self.btn_delete_section.setToolTip("Delete selected actions")
        
        self.btn_clear_all = QToolButton()
        self.btn_clear_all.setText("Clear All")
        self.btn_clear_all.setToolTip("Remove all actions")
        
        self.btn_save_macro = QToolButton()
        self.btn_save_macro.setText("Save Macro")
        self.btn_save_macro.setToolTip("Save macro to file")
        
        self.btn_load_macro = QToolButton()
        self.btn_load_macro.setText("Load Macro")
        self.btn_load_macro.setToolTip("Load macro from file")
        
        toolbar.addWidget(QLabel("Sections: "))
        toolbar.addSeparator()
        toolbar.addWidget(self.btn_duplicate_section)
        toolbar.addWidget(self.btn_delete_section)
        toolbar.addWidget(self.btn_clear_all)
        toolbar.addSeparator()
        toolbar.addWidget(self.btn_save_macro)
        toolbar.addWidget(self.btn_load_macro)
        toolbar.addSeparator()
        
        layout.addWidget(toolbar)
        
        # Action table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["#", "Action", "Duration", "Enabled", "Options"])
        self._table.verticalHeader().setDefaultSectionSize(32)
        self._table.verticalHeader().setMinimumSectionSize(32)
        
        header_view = self._table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.Stretch)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(4, QHeaderView.Fixed)
        header_view.resizeSection(4, 24)
        
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)
        
        self._table.setDragEnabled(True)
        self._table.setAcceptDrops(True)
        self._table.setDragDropMode(QAbstractItemView.InternalMove)
        self._table.setDragDropOverwriteMode(False)
        self._table.setDropIndicatorShown(True)
        
        self._table.horizontalHeader().setStretchLastSection(False)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setSelectionMode(QTableWidget.SingleSelection)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout.addWidget(self._table)
        
        # Connect signals
        self._table.cellClicked.connect(self._on_cell_clicked)
        self._table.cellChanged.connect(self._on_cell_changed)
        
        self.btn_duplicate_section.clicked.connect(self._on_duplicate_section)
        self.btn_delete_section.clicked.connect(self._on_delete_selection)
        self.btn_clear_all.clicked.connect(self._on_clear_all)
        self.btn_save_macro.clicked.connect(self._on_save_macro)
        self.btn_load_macro.clicked.connect(self._on_load_macro)
    
    def _setup_add_menu(self):
        self._add_menu = QMenu()
        
        actions_menu = self._add_menu.addMenu("Actions")
        actions_menu.addAction("Click", lambda: self._add_action(ActionType.CLICK))
        actions_menu.addAction("Double Click", lambda: self._add_action(ActionType.DOUBLE_CLICK))
        actions_menu.addAction("Right Click", lambda: self._add_action(ActionType.RIGHT_CLICK))
        actions_menu.addAction("Key Press", lambda: self._add_action(ActionType.KEY_PRESS))
        actions_menu.addAction("Key Hold", lambda: self._add_action(ActionType.KEY_HOLD))
        actions_menu.addAction("Key Release", lambda: self._add_action(ActionType.KEY_RELEASE))
        actions_menu.addAction("Type Text", lambda: self._add_action(ActionType.TYPE_TEXT))
        actions_menu.addAction("Mouse Move", lambda: self._add_action(ActionType.MOUSE_MOVE))
        actions_menu.addAction("Mouse Drag", lambda: self._add_action(ActionType.MOUSE_DRAG))
        actions_menu.addSeparator()
        actions_menu.addAction("Wait", lambda: self._add_action(ActionType.WAIT))
        actions_menu.addAction("Wait for Image", lambda: self._add_action(ActionType.WAIT_IMAGE))
        actions_menu.addAction("Screenshot", lambda: self._add_action(ActionType.SCREENSHOT))
        
        self._add_menu.addSeparator()
        
        conditionals_menu = self._add_menu.addMenu("Conditionals")
        conditionals_menu.addAction("If Image Visible", lambda: self._add_action(ActionType.IF_IMAGE))
        conditionals_menu.addAction("If Image Not Visible", lambda: self._add_action(ActionType.IF_NOT_IMAGE))
        conditionals_menu.addAction("If Variable", lambda: self._add_action(ActionType.IF_VARIABLE))
        conditionals_menu.addAction("Find Image", lambda: self._add_action(ActionType.FIND_IMAGE))
        
        self._add_menu.addSeparator()
        
        flow_menu = self._add_menu.addMenu("Flow Control")
        flow_menu.addAction("Loop Start", lambda: self._add_action(ActionType.LOOP_START))
        flow_menu.addAction("Loop End", lambda: self._add_action(ActionType.LOOP_END))
        flow_menu.addAction("Break", lambda: self._add_action(ActionType.BREAK))
        flow_menu.addAction("Continue", lambda: self._add_action(ActionType.CONTINUE))
        
        self._add_menu.addSeparator()
        
        other_menu = self._add_menu.addMenu("Other")
        other_menu.addAction("Set Variable", lambda: self._add_action(ActionType.SET_VARIABLE))
        other_menu.addAction("Counter Check", lambda: self._add_action(ActionType.COUNTER_CHECK))
        other_menu.addAction("Discord Send", lambda: self._add_action(ActionType.DISCORD_SEND))
        other_menu.addAction("Custom", lambda: self._add_action(ActionType.CUSTOM))
    
    def _show_add_menu(self, position: QPoint):
        self._add_menu.popup(position)
    
    def _add_action(self, action_type: ActionType) -> Action:
        action = create_action_with_prompt(action_type)
        if action:
            self.add_action(action)
            self.action_added.emit()
        return action
    
    def add_action(self, action: Action, index: int = None):
        if index is None:
            self._actions.append(action)
            self._refresh_table()
        else:
            self._actions.insert(index, action)
            self._refresh_table()
    
    def set_actions(self, actions: List[Action]):
        self._actions = actions[:]
        self._refresh_table()
    
    def get_actions(self) -> List[Action]:
        return [a.copy() for a in self._actions]
    
    def _refresh_table(self):
        self._table.setRowCount(0)
        
        for row, action in enumerate(self._actions):
            self._table.insertRow(row)
            
            # Serial number
            serial_item = QTableWidgetItem(str(row + 1))
            serial_item.setTextAlignment(Qt.AlignCenter)
            serial_item.setFlags(serial_item.flags() & ~Qt.ItemIsEditable)
            self._table.setItem(row, 0, serial_item)
            
            # Action name
            name_item = QTableWidgetItem(action.get_display_name())
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self._table.setItem(row, 1, name_item)
            
            # Duration
            duration_item = QTableWidgetItem(f"{action.duration:.2f}s" if action.duration > 0 else "")
            duration_item.setTextAlignment(Qt.AlignCenter)
            duration_item.setFlags(duration_item.flags() & ~Qt.ItemIsEditable)
            self._table.setItem(row, 2, duration_item)
            
            # Enabled checkbox
            enabled_item = QTableWidgetItem()
            enabled_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            enabled_item.setCheckState(Qt.Checked if action.enabled else Qt.Unchecked)
            self._table.setItem(row, 3, enabled_item)
            
            # Action type indicator
            type_item = QTableWidgetItem()
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self._table.setItem(row, 4, type_item)
            
            # Color code based on action type
            color = self._get_action_color(action.type)
            name_item.setForeground(QColor(color))
    
    def _get_action_color(self, action_type: ActionType) -> str:
        colors = {
            ActionType.CLICK: "#00b4d8",
            ActionType.DOUBLE_CLICK: "#00b4d8",
            ActionType.RIGHT_CLICK: "#00b4d8",
            ActionType.KEY_PRESS: "#f093fb",
            ActionType.KEY_HOLD: "#f093fb",
            ActionType.KEY_RELEASE: "#f093fb",
            ActionType.TYPE_TEXT: "#f093fb",
            ActionType.MOUSE_MOVE: "#aae3f5",
            ActionType.MOUSE_DRAG: "#aae3f5",
            ActionType.WAIT: "#8b949e",
            ActionType.WAIT_IMAGE: "#8b949e",
            ActionType.IF_IMAGE: "#f7dc6f",
            ActionType.IF_NOT_IMAGE: "#f7dc6f",
            ActionType.IF_VARIABLE: "#f7dc6f",
            ActionType.FIND_IMAGE: "#9b59b6",
            ActionType.LOOP_START: "#2ecc71",
            ActionType.LOOP_END: "#2ecc71",
            ActionType.BREAK: "#e74c3c",
            ActionType.CONTINUE: "#e74c3c",
            ActionType.SET_VARIABLE: "#00b894",
            ActionType.COUNTER_CHECK: "#00b894",
            ActionType.SCREENSHOT: "#00cec9",
            ActionType.DISCORD_SEND: "#9b59b6",
            ActionType.CUSTOM: "#95a5a6",
        }
        return colors.get(action_type, "#ffffff")
    
    def _on_cell_clicked(self, row: int, column: int):
        self._current_row = row
        action = self._actions[row] if row < len(self._actions) else None
    
    def _on_cell_changed(self, row: int, column: int):
        if column == 3:
            item = self._table.item(row, column)
            if item:
                is_enabled = item.checkState() == Qt.Checked
                if row < len(self._actions):
                    self._actions[row].enabled = is_enabled
                    self.action_modified.emit()
    
    def _on_context_menu(self, position: QPoint):
        item = self._table.itemAt(position)
        if item:
            row = item.row()
            action = self._actions[row] if row < len(self._actions) else None
            if action:
                menu = QMenu()
                menu.addAction("Duplicate", lambda: self._duplicate_action(row))
                menu.addAction("Edit", lambda: self._edit_action(row))
                menu.addSeparator()
                menu.addAction("Delete", lambda: self._delete_action(row))
                menu.addAction("Move Up", lambda: self._move_action(row, row - 1))
                menu.addAction("Move Down", lambda: self._move_action(row, row + 1))
                menu.addSeparator()
                menu.addAction("Copy to Clipboard", lambda: self._copy_action(row))
                menu.addAction("Paste from Clipboard", lambda: self._paste_action(row))
                
                menu.popup(self._table.mapToGlobal(position))
        else:
            menu = QMenu()
            menu.addAction("Paste Action", lambda: self._paste_action_after_last())
            menu.popup(self._table.mapToGlobal(position))
    
    def _duplicate_action(self, row: int):
        if 0 <= row < len(self._actions):
            action = self._actions[row].copy()
            self._actions.insert(row + 1, action)
            self._refresh_table()
            self.action_duplicated.emit()
    
    def _edit_action(self, row: int):
        if 0 <= row < len(self._actions):
            from src.gui.action_editor import ActionEditorDialog
            dialog = ActionEditorDialog(self._actions[row], self)
            if dialog.exec() == dialog.Accepted:
                updated_action = dialog.get_action()
                self._actions[row] = updated_action
                self._refresh_table()
                self.action_modified.emit()
    
    def _delete_action(self, row: int):
        if 0 <= row < len(self._actions):
            self._actions.pop(row)
            self._refresh_table()
            self.action_removed.emit()
    
    def _move_action(self, from_row: int, to_row: int):
        if 0 <= from_row < len(self._actions) and 0 <= to_row < len(self._actions):
            action = self._actions.pop(from_row)
            self._actions.insert(to_row, action)
            self._refresh_table()
            self.action_modified.emit()
    
    def _copy_action(self, row: int):
        if 0 <= row < len(self._actions):
            import json
            data = self._actions[row].to_dict()
            clipboard_text = json.dumps(data, indent=2)
            QApplication_clipboard = None
            from PySide6.QtWidgets import QApplication
            cb = QApplication.clipboard()
            cb.setText(clipboard_text)
    
    def _paste_action(self, row: int):
        from PySide6.QtWidgets import QApplication
        cb = QApplication.clipboard()
        text = cb.text()
        try:
            import json
            data = json.loads(text)
            action = Action.from_dict(data)
            if 0 <= row < len(self._actions):
                self._actions.insert(row, action)
            else:
                self._actions.append(action)
            self._refresh_table()
            self.action_added.emit()
        except:
            pass
    
    def _paste_action_after_last(self):
        from PySide6.QtWidgets import QApplication
        cb = QApplication.clipboard()
        text = cb.text()
        try:
            import json
            data = json.loads(text)
            action = Action.from_dict(data)
            self._actions.append(action)
            self._refresh_table()
            self.action_added.emit()
        except:
            pass
    
    def _on_duplicate_section(self):
        selected_rows = sorted(set(item.row() for item in self._table.selectedItems()))
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select actions to duplicate")
            return
        
        name, ok = QInputDialog.getText(self, "Duplicate Section", "Enter section name:")
        if ok and name:
            from src.gui.section_manager import SectionManager
            manager = SectionManager()
            manager.duplicate_section(self._actions, selected_rows, name)
            self.action_duplicated.emit()
    
    def _on_delete_selection(self):
        selected_rows = sorted(set(item.row() for item in self._table.selectedItems()), reverse=True)
        if not selected_rows:
            return
        
        reply = QMessageBox.question(self, "Confirm Delete", 
                                    f"Delete {len(selected_rows)} action(s)?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            for row in selected_rows:
                if row < len(self._actions):
                    self._actions.pop(row)
            self._refresh_table()
            self.action_removed.emit()
    
    def _on_clear_all(self):
        if self._actions:
            reply = QMessageBox.question(self, "Confirm Clear", 
                                        "Remove all actions?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self._actions.clear()
                self._refresh_table()
                self.action_removed.emit()
    
    def _on_save_macro(self):
        from src.engine import MACRO_MANAGER
        name, ok = QInputDialog.getText(self, "Save Macro", "Enter macro name:")
        if ok and name:
            filepath = MACRO_MANAGER.save_macro(name)
            QMessageBox.information(self, "Saved", f"Macro saved as: {filepath}")
    
    def _on_load_macro(self):
        from src.engine import MACRO_MANAGER
        macros = MACRO_MANAGER.list_macros()
        if not macros:
            QMessageBox.information(self, "No Macros", "No saved macros found")
            return
        
        name, ok = QInputDialog.getItem(self, "Load Macro", "Select a macro:", macros)
        if ok and name:
            if MACRO_MANAGER.load_macro(name):
                self.set_actions(ENGINE.actions)
                self.action_added.emit()
    
    def dragMoveEvent(self, event):
        pass
    
    def dropEvent(self, event):
        pass
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start_position = event.pos()
        super().mousePressEvent(event)