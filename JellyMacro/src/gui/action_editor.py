"""
Action editor dialog for JellyMacro - allows editing action properties
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QHBoxLayout,
    QDialogButtonBox, QLabel, QGroupBox, QListWidget,
    QListWidgetItem, QPushButton, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from src.actions import (
    Action, ActionType, ClickType,
    ClickActionData, KeyActionData, WaitActionData,
    ImageActionData, LoopActionData, VariableActionData,
    CounterActionData, Point, Rect
)
from src.vision import IMAGE_MANAGER


class ActionEditorDialog(QDialog):
    def __init__(self, action: Action, parent=None):
        super().__init__(parent)
        self.action = action
        self.setWindowTitle("Edit Action")
        self.resize(500, 600)
        
        self._setup_ui()
        self._load_action_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Action type and name section
        basic_group = QGroupBox("Basic Settings")
        basic_layout = QFormLayout(basic_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.setToolTip("Custom name for this action")
        basic_layout.addRow("Action Name:", self.name_edit)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems([t.value.replace("_", " ").title() for t in ActionType])
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        basic_layout.addRow("Action Type:", self.type_combo)
        
        layout.addWidget(basic_group)
        
        # Action-specific settings
        self.dynamic_layout = QFormLayout()
        self.dynamic_widget = QWidget()
        self.dynamic_layout_widget = QFormLayout(self.dynamic_widget)
        layout.addWidget(self.dynamic_widget)
        
        # Common settings
        common_group = QGroupBox("Common Settings")
        common_layout = QFormLayout(common_group)
        
        self.delay_before = QDoubleSpinBox()
        self.delay_before.setRange(0, 100)
        self.delay_before.setSingleValue(0.1)
        self.delay_before.setSuffix("s")
        common_layout.addRow("Delay Before:", self.delay_before)
        
        self.delay_after = QDoubleSpinBox()
        self.delay_after.setRange(0, 100)
        self.delay_after.setSingleValue(0.1)
        self.delay_after.setSuffix("s")
        common_layout.addRow("Delay After:", self.delay_after)
        
        self.repeat_count = QSpinBox()
        self.repeat_count.setRange(1, 999999)
        self.repeat_count.setValue(1)
        common_layout.addRow("Repeat:", self.repeat_count)
        
        self.enabled_check = QCheckBox("Enabled")
        self.enabled_check.setChecked(True)
        common_layout.addRow("", self.enabled_check)
        
        layout.addWidget(common_group)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _load_action_data(self):
        # Set action type
        action_type_str = self.action.type.value
        for i in range(self.type_combo.count()):
            if self.type_combo.itemText(i).lower().replace(" ", "_") == action_type_str:
                self.type_combo.setCurrentIndex(i)
                break
        
        # Set basic settings
        self.name_edit.setText(self.action.name)
        self.delay_before.setValue(self.action.delay_before)
        self.delay_after.setValue(self.action.delay_after)
        self.repeat_count.setValue(self.action.repeat_count)
        self.enabled_check.setChecked(self.action.enabled)
        
        # Load type-specific settings
        self._setup_type_specific_widgets(self.action)
    
    def _setup_type_specific_widgets(self, action: Action):
        # Clear existing widgets
        for i in reversed(range(self.dynamic_layout_widget.layout().count())):
            self.dynamic_layout_widget.layout().itemAt(i).widget().setParent(None)
        
        t = action.type
        
        if t in (ActionType.CLICK, ActionType.DOUBLE_CLICK, ActionType.RIGHT_CLICK):
            data = ClickActionData.from_dict(action.data)
            self._add_click_widgets(data)
        elif t in (ActionType.KEY_PRESS, ActionType.KEY_HOLD, ActionType.KEY_RELEASE):
            data = KeyActionData.from_dict(action.data)
            self._add_key_widgets(data)
        elif t == ActionType.TYPE_TEXT:
            self._add_text_widgets(action.data)
        elif t in (ActionType.MOUSE_MOVE, ActionType.MOUSE_DRAG):
            self._add_mouse_widgets(action.data)
        elif t in (ActionType.WAIT, ActionType.WAIT_IMAGE):
            data = WaitActionData.from_dict(action.data)
            self._add_wait_widgets(data)
        elif t in (ActionType.IF_IMAGE, ActionType.IF_NOT_IMAGE, ActionType.FIND_IMAGE):
            data = ImageActionData.from_dict(action.data)
            self._add_image_widgets(data)
        elif t in (ActionType.LOOP_START, ActionType.LOOP_END):
            data = LoopActionData.from_dict(action.data)
            self._add_loop_widgets(data)
        elif t in (ActionType.SET_VARIABLE, ActionType.IF_VARIABLE):
            data = VariableActionData.from_dict(action.data)
            self._add_variable_widgets(data)
        elif t == ActionType.COUNTER_CHECK:
            data = CounterActionData.from_dict(action.data)
            self._add_counter_widgets(data)
        elif t == ActionType.SCREENSHOT:
            self._add_screenshot_widgets(action.data)
        elif t == ActionType.DISCORD_SEND:
            self._add_discord_widgets(action.data)
        elif t == ActionType.CUSTOM:
            self._add_custom_widgets(action.data)
    
    def _add_click_widgets(self, data: ClickActionData):
        self._clear_dynamic()
        
        self.x_spin = QSpinBox()
        self.x_spin.setRange(0, 9999)
        self.x_spin.setValue(data.x)
        self._dynamic_layout().addRow("X Position:", self.x_spin)
        
        self.y_spin = QSpinBox()
        self.y_spin.setRange(0, 9999)
        self.y_spin.setValue(data.y)
        self._dynamic_layout().addRow("Y Position:", self.y_spin)
        
        self.relative_check = QCheckBox("Relative to Canvas")
        self.relative_check.setChecked(data.relative)
        self._dynamic_layout().addRow(self.relative_check)
        
        self.click_type_combo = QComboBox()
        self.click_type_combo.addItems(["left", "right", "middle", "double"])
        self.click_type_combo.setCurrentText(data.click_type.value)
        self._dynamic_layout().addRow("Click Type:", self.click_type_combo)
        
        self.click_duration = QDoubleSpinBox()
        self.click_duration.setRange(0, 5)
        self.click_duration.setSingleValue(0.01)
        self.click_duration.setSuffix("s")
        self.click_duration.setValue(data.duration)
        self._dynamic_layout().addRow("Duration:", self.click_duration)
    
    def _add_key_widgets(self, data: KeyActionData):
        self._clear_dynamic()
        
        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("e.g. 'a', 'space', 'enter'")
        self.key_edit.setText(data.key)
        self._dynamic_layout().addRow("Key:", self.key_edit)
        
        self.key_duration = QDoubleSpinBox()
        self.key_duration.setRange(0, 5)
        self.key_duration.setSingleValue(0.01)
        self.key_duration.setSuffix("s")
        self.key_duration.setValue(data.duration)
        self._dynamic_layout().addRow("Duration:", self.key_duration)
        
        self.modifiers_edit = QLineEdit()
        self.modifiers_edit.setPlaceholderText("e.g. 'shift,ctrl'")
        self.modifiers_edit.setText(",".join(data.modifiers))
        self._dynamic_layout().addRow("Modifiers:", self.modifiers_edit)
    
    def _add_text_widgets(self, data):
        self._clear_dynamic()
        
        self.text_edit = QLineEdit()
        self.text_edit.setText(data.get('text', ''))
        self._dynamic_layout().addRow("Text:", self.text_edit)
        
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0, 5)
        self.interval_spin.setSingleValue(0.01)
        self.interval_spin.setSuffix("s")
        self.interval_spin.setValue(data.get('interval', 0.05))
        self._dynamic_layout().addRow("Interval:", self.interval_spin)
    
    def _add_mouse_widgets(self, data):
        self._clear_dynamic()
        
        self.start_x = QSpinBox()
        self.start_x.setRange(-9999, 9999)
        self.start_x.setValue(data.get('start_x', 0))
        self._dynamic_layout().addRow("Start X:", self.start_x)
        
        self.start_y = QSpinBox()
        self.start_y.setRange(-9999, 9999)
        self.start_y.setValue(data.get('start_y', 0))
        self._dynamic_layout().addRow("Start Y:", self.start_y)
        
        self.end_x = QSpinBox()
        self.end_x.setRange(-9999, 9999)
        self.end_x.setValue(data.get('end_x', 0))
        self._dynamic_layout().addRow("End X:", self.end_x)
        
        self.end_y = QSpinBox()
        self.end_y.setRange(-9999, 9999)
        self.end_y.setValue(data.get('end_y', 0))
        self._dynamic_layout().addRow("End Y:", self.end_y)
        
        self.mouse_relative = QCheckBox("Relative to Canvas")
        self.mouse_relative.setChecked(data.get('relative', True))
        self._dynamic_layout().addRow(self.mouse_relative)
        
        self.mouse_duration = QDoubleSpinBox()
        self.mouse_duration.setRange(0, 10)
        self.mouse_duration.setSingleValue(0.1)
        self.mouse_duration.setSuffix("s")
        self.mouse_duration.setValue(data.get('duration', 0.5))
        self._dynamic_layout().addRow("Duration:", self.mouse_duration)
    
    def _add_wait_widgets(self, data: WaitActionData):
        self._clear_dynamic()
        
        self.wait_duration = QDoubleSpinBox()
        self.wait_duration.setRange(0, 9999)
        self.wait_duration.setSingleValue(0.1)
        self.wait_duration.setSuffix("s")
        self.wait_duration.setValue(data.duration)
        self._dynamic_layout().addRow("Duration:", self.wait_duration)
        
        self.randomize_check = QCheckBox("Randomize")
        self.randomize_check.setChecked(data.randomize)
        self._dynamic_layout().addRow(self.randomize_check)
        
        self.min_duration = QDoubleSpinBox()
        self.min_duration.setRange(0, 9999)
        self.min_duration.setSingleValue(0.1)
        self.min_duration.setSuffix("s")
        self.min_duration.setValue(data.min_duration)
        self._dynamic_layout().addRow("Min Duration:", self.min_duration)
        
        self.max_duration = QDoubleSpinBox()
        self.max_duration.setRange(0, 9999)
        self.max_duration.setSingleValue(0.1)
        self.max_duration.setSuffix("s")
        self.max_duration.setValue(data.max_duration)
        self._dynamic_layout().addRow("Max Duration:", self.max_duration)
    
    def _add_image_widgets(self, data: ImageActionData):
        self._clear_dynamic()
        
        self.image_combo = QComboBox()
        self.image_combo.setEditable(True)
        images = IMAGE_MANAGER.get_all_images()
        for img in images:
            self.image_combo.addItem(img.name, img.path)
        if data.image_path:
            self.image_combo.setEditText(data.image_path)
        self._dynamic_layout().addRow("Image:", self.image_combo)
        
        self.confidence_spin = QDoubleSpinBox()
        self.confidence_spin.setRange(0.1, 1.0)
        self.confidence_spin.setSingleValue(0.01)
        self.confidence_spin.setValue(data.confidence)
        self._dynamic_layout().addRow("Confidence:", self.confidence_spin)
        
        self.timeout_spin = QDoubleSpinBox()
        self.timeout_spin.setRange(0, 9999)
        self.timeout_spin.setSingleValue(1.0)
        self.timeout_spin.setSuffix("s")
        self.timeout_spin.setValue(data.timeout)
        self._dynamic_layout().addRow("Timeout:", self.timeout_spin)
        
        self.click_when_found = QCheckBox("Click when found")
        self.click_when_found.setChecked(data.click_when_found)
        self._dynamic_layout().addRow(self.click_when_found)
        
        self.click_offset_x = QSpinBox()
        self.click_offset_x.setRange(-9999, 9999)
        self.click_offset_x.setValue(data.click_offset.x)
        self._dynamic_layout().addRow("Click Offset X:", self.click_offset_x)
        
        self.click_offset_y = QSpinBox()
        self.click_offset_y.setRange(-9999, 9999)
        self.click_offset_y.setValue(data.click_offset.y)
        self._dynamic_layout().addRow("Click Offset Y:", self.click_offset_y)
    
    def _add_loop_widgets(self, data: LoopActionData):
        self._clear_dynamic()
        
        self.loop_count = QSpinBox()
        self.loop_count.setRange(0, 999999)
        self.loop_count.setValue(data.count)
        self._dynamic_layout().addRow("Loop Count (0=infinite):", self.loop_count)
        
        self.loop_variable = QLineEdit()
        self.loop_variable.setPlaceholderText("Variable name (loop while true)")
        self.loop_variable.setText(data.variable)
        self._dynamic_layout().addRow("Loop Variable:", self.loop_variable)
        
        self.loop_condition = QLineEdit()
        self.loop_condition.setPlaceholderText("Python condition (use variables)")
        self.loop_condition.setText(data.condition)
        self._dynamic_layout().addRow("Loop Condition:", self.loop_condition)
    
    def _add_variable_widgets(self, data: VariableActionData):
        self._clear_dynamic()
        
        self.var_name = QLineEdit()
        self.var_name.setText(data.name)
        self._dynamic_layout().addRow("Variable Name:", self.var_name)
        
        self.var_value = QLineEdit()
        self.var_value.setText(str(data.value))
        self._dynamic_layout().addRow("Value:", self.var_value)
        
        self.var_operation = QComboBox()
        self.var_operation.addItems(["set", "add", "subtract", "multiply", "divide",
                                     "equals", "not_equals", "greater", "less", "contains",
                                     "is_true", "is_false"])
        self.var_operation.setCurrentText(data.operation)
        self._dynamic_layout().addRow("Operation:", self.var_operation)
    
    def _add_counter_widgets(self, data: CounterActionData):
        self._clear_dynamic()
        
        self.counter_name = QLineEdit()
        self.counter_name.setText(data.counter_name)
        self._dynamic_layout().addRow("Counter Name:", self.counter_name)
        
        self.counter_image = QComboBox()
        self.counter_image.setEditable(True)
        images = IMAGE_MANAGER.get_all_images()
        for img in images:
            self.counter_image.addItem(img.name, img.path)
        self._dynamic_layout().addRow("Indicator Image:", self.counter_image)
        
        self.expected_change = QSpinBox()
        self.expected_change.setRange(-999, 999)
        self.expected_change.setValue(data.expected_change)
        self._dynamic_layout().addRow("Expected Change:", self.expected_change)
    
    def _add_screenshot_widgets(self, data):
        self._clear_dynamic()
        self._dynamic_layout().addRow(QLabel("Takes a screenshot of the canvas area"))
    
    def _add_discord_widgets(self, data):
        self._clear_dynamic()
        
        self.discord_message = QLineEdit()
        self.discord_message.setText(data.get('message', ''))
        self._dynamic_layout().addRow("Message:", self.discord_message)
        
        self.discord_embed = QCheckBox("Include Embed")
        self.discord_embed.setChecked(data.get('embed', True))
        self._dynamic_layout().addRow(self.discord_embed)
    
    def _add_custom_widgets(self, data):
        self._clear_dynamic()
        
        self.custom_code = QLineEdit()
        self.custom_code.setText(data.get('code', ''))
        self._dynamic_layout().addRow("Custom Code:", self.custom_code)
    
    def _clear_dynamic(self):
        for i in reversed(range(self.dynamic_widget.layout().count())):
            self.dynamic_widget.layout().itemAt(i).widget().setParent(None)
    
    def _dynamic_layout(self):
        return self.dynamic_layout_widget.layout()
    
    def _on_type_changed(self, index: int):
        action_type_str = self.type_combo.itemText(index).lower().replace(" ", "_")
        try:
            action_type = ActionType(action_type_str)
            new_action = Action(type=action_type)
            self._setup_type_specific_widgets(new_action)
        except ValueError:
            pass
    
    def get_action(self) -> Action:
        action_type_str = self.type_combo.currentText().lower().replace(" ", "_")
        try:
            action_type = ActionType(action_type_str)
        except ValueError:
            action_type = self.action.type
        
        action = Action(
            id=self.action.id,
            type=action_type,
            name=self.name_edit.text() or self.action.name,
            enabled=self.enabled_check.isChecked(),
            delay_before=self.delay_before.value(),
            delay_after=self.delay_after.value(),
            repeat_count=self.repeat_count.value()
        )
        
        action.data = self._collect_type_specific_data(action_type)
        return action
    
    def _collect_type_specific_data(self, action_type: ActionType) -> dict:
        if action_type in (ActionType.CLICK, ActionType.DOUBLE_CLICK, ActionType.RIGHT_CLICK):
            return {
                "x": self.x_spin.value(),
                "y": self.y_spin.value(),
                "relative": self.relative_check.isChecked(),
                "click_type": self.click_type_combo.currentText(),
                "duration": self.click_duration.value()
            }
        elif action_type in (ActionType.KEY_PRESS, ActionType.KEY_HOLD, ActionType.KEY_RELEASE):
            modifiers = [m.strip() for m in self.modifiers_edit.text().split(",") if m.strip()]
            return {
                "key": self.key_edit.text(),
                "duration": self.key_duration.value(),
                "modifiers": modifiers
            }
        elif action_type == ActionType.TYPE_TEXT:
            return {
                "text": self.text_edit.text(),
                "interval": self.interval_spin.value()
            }
        elif action_type in (ActionType.MOUSE_MOVE, ActionType.MOUSE_DRAG):
            return {
                "start_x": self.start_x.value(),
                "start_y": self.start_y.value(),
                "end_x": self.end_x.value(),
                "end_y": self.end_y.value(),
                "relative": self.mouse_relative.isChecked(),
                "duration": self.mouse_duration.value()
            }
        elif action_type in (ActionType.WAIT, ActionType.WAIT_IMAGE):
            return {
                "duration": self.wait_duration.value(),
                "randomize": self.randomize_check.isChecked(),
                "min_duration": self.min_duration.value(),
                "max_duration": self.max_duration.value()
            }
        elif action_type in (ActionType.IF_IMAGE, ActionType.IF_NOT_IMAGE, ActionType.FIND_IMAGE):
            data = {
                "image_path": self.image_combo.currentText(),
                "confidence": self.confidence_spin.value(),
                "timeout": self.timeout_spin.value(),
                "click_when_found": self.click_when_found.isChecked(),
                "click_offset": {"x": self.click_offset_x.value(), "y": self.click_offset_y.value()}
            }
            return data
        elif action_type in (ActionType.LOOP_START, ActionType.LOOP_END):
            return {
                "count": self.loop_count.value(),
                "variable": self.loop_variable.text(),
                "condition": self.loop_condition.text()
            }
        elif action_type in (ActionType.SET_VARIABLE, ActionType.IF_VARIABLE):
            try:
                value = int(self.var_value.text())
            except ValueError:
                value = self.var_value.text()
            return {
                "name": self.var_name.text(),
                "value": value,
                "operation": self.var_operation.currentText()
            }
        elif action_type == ActionType.COUNTER_CHECK:
            return {
                "counter_name": self.counter_name.text(),
                "image_path": self.counter_image.currentText(),
                "expected_change": self.expected_change.value()
            }
        elif action_type == ActionType.SCREENSHOT:
            return {}
        elif action_type == ActionType.DISCORD_SEND:
            return {
                "message": self.discord_message.text(),
                "embed": self.discord_embed.isChecked()
            }
        elif action_type == ActionType.CUSTOM:
            return {
                "code": self.custom_code.text()
            }
        return self.action.data