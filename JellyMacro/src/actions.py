"""
Action models for JellyMacro - defines all action types and their properties
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from pathlib import Path
import uuid
import time


class ActionType(Enum):
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    KEY_PRESS = "key_press"
    KEY_HOLD = "key_hold"
    KEY_RELEASE = "key_release"
    TYPE_TEXT = "type_text"
    MOUSE_MOVE = "mouse_move"
    MOUSE_DRAG = "mouse_drag"
    WAIT = "wait"
    WAIT_IMAGE = "wait_image"
    IF_IMAGE = "if_image"
    IF_NOT_IMAGE = "if_not_image"
    FIND_IMAGE = "find_image"
    LOOP_START = "loop_start"
    LOOP_END = "loop_end"
    BREAK = "break"
    CONTINUE = "continue"
    SET_VARIABLE = "set_variable"
    IF_VARIABLE = "if_variable"
    COUNTER_CHECK = "counter_check"
    SCREENSHOT = "screenshot"
    DISCORD_SEND = "discord_send"
    CUSTOM = "custom"


class ClickType(Enum):
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"
    DOUBLE = "double"


@dataclass
class Point:
    x: int
    y: int
    
    def to_tuple(self) -> tuple:
        return (self.x, self.y)
    
    @classmethod
    def from_tuple(cls, t: tuple):
        return cls(t[0], t[1])


@dataclass
class Rect:
    x: int
    y: int
    width: int
    height: int
    
    def contains(self, point: Point) -> bool:
        return (self.x <= point.x < self.x + self.width and 
                self.y <= point.y < self.y + self.height)
    
    def center(self) -> Point:
        return Point(self.x + self.width // 2, self.y + self.height // 2)


@dataclass
class Action:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: ActionType = ActionType.WAIT
    name: str = "New Action"
    enabled: bool = True
    duration: float = 0.0
    delay_before: float = 0.0
    delay_after: float = 0.0
    repeat_count: int = 1
    data: Dict[str, Any] = field(default_factory=dict)
    children: List['Action'] = field(default_factory=list)
    parent_id: Optional[str] = None
    condition: Optional[str] = None
    
    def __post_init__(self):
        if isinstance(self.type, str):
            self.type = ActionType(self.type)
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['type'] = self.type.value
        result['children'] = [child.to_dict() for child in self.children]
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Action':
        children_data = data.pop('children', [])
        action = cls(**data)
        action.children = [cls.from_dict(child) for child in children_data]
        for child in action.children:
            child.parent_id = action.id
        return action
    
    def copy(self) -> 'Action':
        new_action = Action.from_dict(self.to_dict())
        new_action.id = str(uuid.uuid4())[:8]
        return new_action
    
    def get_display_name(self) -> str:
        if self.name != "New Action":
            return self.name
        
        type_names = {
            ActionType.CLICK: "Click",
            ActionType.DOUBLE_CLICK: "Double Click",
            ActionType.RIGHT_CLICK: "Right Click",
            ActionType.KEY_PRESS: "Key Press",
            ActionType.KEY_HOLD: "Key Hold",
            ActionType.KEY_RELEASE: "Key Release",
            ActionType.TYPE_TEXT: "Type Text",
            ActionType.MOUSE_MOVE: "Mouse Move",
            ActionType.MOUSE_DRAG: "Mouse Drag",
            ActionType.WAIT: "Wait",
            ActionType.WAIT_IMAGE: "Wait for Image",
            ActionType.IF_IMAGE: "If Image Visible",
            ActionType.IF_NOT_IMAGE: "If Image Not Visible",
            ActionType.FIND_IMAGE: "Find Image",
            ActionType.LOOP_START: "Loop Start",
            ActionType.LOOP_END: "Loop End",
            ActionType.BREAK: "Break",
            ActionType.CONTINUE: "Continue",
            ActionType.SET_VARIABLE: "Set Variable",
            ActionType.IF_VARIABLE: "If Variable",
            ActionType.COUNTER_CHECK: "Counter Check",
            ActionType.SCREENSHOT: "Screenshot",
            ActionType.DISCORD_SEND: "Discord Send",
        }
        return type_names.get(self.type, self.type.value)


@dataclass
class ClickActionData:
    x: int = 0
    y: int = 0
    relative: bool = True
    click_type: ClickType = ClickType.LEFT
    duration: float = 0.05
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ClickActionData':
        click_type = data.get('click_type', 'left')
        if isinstance(click_type, str):
            click_type = ClickType(click_type)
        return cls(
            x=data.get('x', 0),
            y=data.get('y', 0),
            relative=data.get('relative', True),
            click_type=click_type,
            duration=data.get('duration', 0.05)
        )


@dataclass
class KeyActionData:
    key: str = ""
    duration: float = 0.05
    modifiers: List[str] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KeyActionData':
        return cls(
            key=data.get('key', ''),
            duration=data.get('duration', 0.05),
            modifiers=data.get('modifiers', [])
        )


@dataclass
class WaitActionData:
    duration: float = 1.0
    randomize: bool = False
    min_duration: float = 0.5
    max_duration: float = 2.0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WaitActionData':
        return cls(
            duration=data.get('duration', 1.0),
            randomize=data.get('randomize', False),
            min_duration=data.get('min_duration', 0.5),
            max_duration=data.get('max_duration', 2.0)
        )


@dataclass
class ImageActionData:
    image_path: str = ""
    confidence: float = 0.8
    region: Optional[Rect] = None
    timeout: float = 10.0
    click_when_found: bool = False
    click_offset: Point = field(default_factory=lambda: Point(0, 0))
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImageActionData':
        region = data.get('region')
        if region and isinstance(region, dict):
            region = Rect(**region)
        click_offset = data.get('click_offset', {'x': 0, 'y': 0})
        if isinstance(click_offset, dict):
            click_offset = Point(**click_offset)
        return cls(
            image_path=data.get('image_path', ''),
            confidence=data.get('confidence', 0.8),
            region=region,
            timeout=data.get('timeout', 10.0),
            click_when_found=data.get('click_when_found', False),
            click_offset=click_offset
        )


@dataclass
class LoopActionData:
    count: int = 0
    condition: str = ""
    variable: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LoopActionData':
        return cls(
            count=data.get('count', 0),
            condition=data.get('condition', ''),
            variable=data.get('variable', '')
        )


@dataclass
class VariableActionData:
    name: str = ""
    value: Any = ""
    operation: str = "set"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VariableActionData':
        return cls(
            name=data.get('name', ''),
            value=data.get('value', ''),
            operation=data.get('operation', 'set')
        )


@dataclass
class CounterActionData:
    counter_name: str = ""
    image_path: str = ""
    region: Optional[Rect] = None
    expected_change: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CounterActionData':
        region = data.get('region')
        if region and isinstance(region, dict):
            region = Rect(**region)
        return cls(
            counter_name=data.get('counter_name', ''),
            image_path=data.get('image_path', ''),
            region=region,
            expected_change=data.get('expected_change', 0)
        )


def create_click_action(x: int, y: int, relative: bool = True, 
                        click_type: ClickType = ClickType.LEFT,
                        name: str = "") -> Action:
    data = ClickActionData(x=x, y=y, relative=relative, click_type=click_type)
    return Action(
        type=ActionType.CLICK,
        name=name or f"Click at ({x}, {y})",
        data=data.__dict__
    )


def create_key_action(key: str, action_type: ActionType = ActionType.KEY_PRESS,
                      duration: float = 0.05, name: str = "") -> Action:
    data = KeyActionData(key=key, duration=duration)
    return Action(
        type=action_type,
        name=name or f"{action_type.value.replace('_', ' ').title()} {key}",
        data=data.__dict__
    )


def create_wait_action(duration: float, name: str = "") -> Action:
    data = WaitActionData(duration=duration)
    return Action(
        type=ActionType.WAIT,
        name=name or f"Wait {duration}s",
        data=data.__dict__
    )


def create_image_action(image_path: str, action_type: ActionType = ActionType.IF_IMAGE,
                        confidence: float = 0.8, name: str = "") -> Action:
    data = ImageActionData(image_path=image_path, confidence=confidence)
    return Action(
        type=action_type,
        name=name or f"{action_type.value.replace('_', ' ').title()}: {Path(image_path).stem}",
        data=data.__dict__
    )


def create_loop_action(count: int = 0, name: str = "") -> Action:
    data = LoopActionData(count=count)
    return Action(
        type=ActionType.LOOP_START,
        name=name or f"Loop {'∞' if count == 0 else f'x{count}'}",
        data=data.__dict__
    )


def create_counter_action(counter_name: str, image_path: str, 
                          region: Optional[Rect] = None, name: str = "") -> Action:
    data = CounterActionData(counter_name=counter_name, image_path=image_path, region=region)
    return Action(
        type=ActionType.COUNTER_CHECK,
        name=name or f"Counter: {counter_name}",
        data=data.__dict__
    )


def create_action_with_prompt(action_type: ActionType, action_name: str = "") -> Optional[Action]:
    """Create an action, optionally prompting for details"""
    
    if action_type == ActionType.CLICK:
        data = ClickActionData()
        return Action(type=action_type, name=action_name or "Click", data=data.__dict__)
    
    elif action_type == ActionType.DOUBLE_CLICK:
        data = ClickActionData(click_type=ClickType.DOUBLE)
        return Action(type=action_type, name=action_name or "Double Click", data=data.__dict__)
    
    elif action_type == ActionType.RIGHT_CLICK:
        data = ClickActionData(click_type=ClickType.RIGHT)
        return Action(type=action_type, name=action_name or "Right Click", data=data.__dict__)
    
    elif action_type in (ActionType.KEY_PRESS, ActionType.KEY_HOLD, ActionType.KEY_RELEASE):
        data = KeyActionData()
        return Action(type=action_type, name=action_name or f"{action_type.value}", data=data.__dict__)
    
    elif action_type == ActionType.TYPE_TEXT:
        data = {"text": "", "interval": 0.05}
        return Action(type=action_type, name=action_name or "Type Text", data=data)
    
    elif action_type in (ActionType.MOUSE_MOVE, ActionType.MOUSE_DRAG):
        data = {
            "start_x": 0, "start_y": 0,
            "end_x": 0, "end_y": 0,
            "relative": True, "duration": 0.5
        }
        return Action(type=action_type, name=action_name or "Mouse Move", data=data)
    
    elif action_type == ActionType.WAIT:
        data = WaitActionData()
        return Action(type=action_type, name=action_name or "Wait", data=data.__dict__)
    
    elif action_type == ActionType.WAIT_IMAGE:
        data = ImageActionData()
        return Action(type=action_type, name=action_name or "Wait for Image", data=data.__dict__)
    
    elif action_type in (ActionType.IF_IMAGE, ActionType.IF_NOT_IMAGE, ActionType.FIND_IMAGE):
        data = ImageActionData()
        return Action(type=action_type, name=action_name or f"{action_type.value}", data=data.__dict__)
    
    elif action_type == ActionType.LOOP_START:
        data = LoopActionData()
        return Action(type=action_type, name=action_name or "Loop Start", data=data.__dict__)
    
    elif action_type == ActionType.LOOP_END:
        data = LoopActionData()
        return Action(type=action_type, name=action_name or "Loop End", data=data.__dict__)
    
    elif action_type == ActionType.BREAK:
        return Action(type=action_type, name=action_name or "Break")
    
    elif action_type == ActionType.CONTINUE:
        return Action(type=action_type, name=action_name or "Continue")
    
    elif action_type == ActionType.SET_VARIABLE:
        data = VariableActionData()
        return Action(type=action_type, name=action_name or "Set Variable", data=data.__dict__)
    
    elif action_type == ActionType.IF_VARIABLE:
        data = VariableActionData()
        return Action(type=action_type, name=action_name or "If Variable", data=data.__dict__)
    
    elif action_type == ActionType.COUNTER_CHECK:
        data = CounterActionData()
        return Action(type=action_type, name=action_name or "Counter Check", data=data.__dict__)
    
    elif action_type == ActionType.SCREENSHOT:
        return Action(type=action_type, name=action_name or "Screenshot")
    
    elif action_type == ActionType.DISCORD_SEND:
        data = {"message": "", "embed": True}
        return Action(type=action_type, name=action_name or "Discord Send", data=data)
    
    elif action_type == ActionType.CUSTOM:
        data = {"code": ""}
        return Action(type=action_type, name=action_name or "Custom", data=data)
    
    return None