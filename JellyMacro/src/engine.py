"""
Automation engine for JellyMacro - handles recording, playback, and execution of actions
"""

import time
import threading
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid
from pathlib import Path

import pyautogui
import cv2
import numpy as np
from pynput import mouse, keyboard

from src.config import CONFIG
from src.actions import (
    Action, ActionType, Point, Rect, ClickType,
    ClickActionData, KeyActionData, WaitActionData,
    ImageActionData, LoopActionData, VariableActionData,
    CounterActionData
)


class PlaybackState(Enum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    RECORDING = "recording"


@dataclass
class RecordedEvent:
    timestamp: float
    event_type: str
    data: Dict[str, Any]


class AutomationEngine:
    def __init__(self):
        self.state = PlaybackState.STOPPED
        self.actions: List[Action] = []
        self.current_action_index = 0
        self.variables: Dict[str, Any] = {}
        self.counters: Dict[str, int] = {}
        self.loop_stack: List[Dict[str, Any]] = []
        
        self._playback_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        
        self._mouse_listener: Optional[mouse.Listener] = None
        self._keyboard_listener: Optional[keyboard.Listener] = None
        self._recorded_events: List[RecordedEvent] = []
        self._record_start_time: float = 0
        
        self.on_state_change: Optional[Callable[[PlaybackState], None]] = None
        self.on_action_execute: Optional[Callable[[Action, int], None]] = None
        self.on_log: Optional[Callable[[str], None]] = None
        self.on_screenshot: Optional[Callable[[np.ndarray], None]] = None
        
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.01
    
    def _log(self, message: str):
        if self.on_log:
            self.on_log(message)
    
    def _notify_state_change(self, state: PlaybackState):
        self.state = state
        if self.on_state_change:
            self.on_state_change(state)
    
    def _notify_action_execute(self, action: Action, index: int):
        if self.on_action_execute:
            self.on_action_execute(action, index)
    
    def set_actions(self, actions: List[Action]):
        self.actions = actions
    
    def add_action(self, action: Action, index: Optional[int] = None):
        if index is None:
            self.actions.append(action)
        else:
            self.actions.insert(index, action)
    
    def remove_action(self, index: int):
        if 0 <= index < len(self.actions):
            self.actions.pop(index)
    
    def move_action(self, from_index: int, to_index: int):
        if 0 <= from_index < len(self.actions) and 0 <= to_index < len(self.actions):
            action = self.actions.pop(from_index)
            self.actions.insert(to_index, action)
    
    def start_playback(self):
        if self.state == PlaybackState.PLAYING:
            return
        
        self._stop_event.clear()
        self._pause_event.clear()
        self.current_action_index = 0
        self.loop_stack = []
        
        self._playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
        self._playback_thread.start()
        self._notify_state_change(PlaybackState.PLAYING)
    
    def pause_playback(self):
        if self.state == PlaybackState.PLAYING:
            self._pause_event.set()
            self._notify_state_change(PlaybackState.PAUSED)
    
    def resume_playback(self):
        if self.state == PlaybackState.PAUSED:
            self._pause_event.clear()
            self._notify_state_change(PlaybackState.PLAYING)
    
    def stop_playback(self):
        self._stop_event.set()
        self._pause_event.clear()
        if self._playback_thread and self._playback_thread.is_alive():
            self._playback_thread.join(timeout=2.0)
        self._notify_state_change(PlaybackState.STOPPED)
    
    def _playback_loop(self):
        try:
            while self.current_action_index < len(self.actions) and not self._stop_event.is_set():
                if self._pause_event.is_set():
                    time.sleep(0.1)
                    continue
                
                action = self.actions[self.current_action_index]
                
                if not action.enabled:
                    self.current_action_index += 1
                    continue
                
                self._notify_action_execute(action, self.current_action_index)
                
                if action.delay_before > 0:
                    self._sleep_with_check(action.delay_before)
                
                try:
                    self._execute_action(action)
                except Exception as e:
                    self._log(f"Error executing action {action.name}: {e}")
                
                if action.delay_after > 0:
                    self._sleep_with_check(action.delay_after)
                
                self.current_action_index += 1
        
        except Exception as e:
            self._log(f"Playback error: {e}")
        finally:
            if not self._stop_event.is_set():
                self._notify_state_change(PlaybackState.STOPPED)
    
    def _sleep_with_check(self, duration: float):
        end_time = time.time() + duration
        while time.time() < end_time and not self._stop_event.is_set():
            if self._pause_event.is_set():
                time.sleep(0.1)
            else:
                time.sleep(min(0.05, end_time - time.time()))
    
    def _execute_action(self, action: Action):
        action_type = action.type
        data = action.data
        
        if action_type == ActionType.CLICK:
            self._execute_click(data)
        elif action_type == ActionType.DOUBLE_CLICK:
            self._execute_double_click(data)
        elif action_type == ActionType.RIGHT_CLICK:
            self._execute_right_click(data)
        elif action_type == ActionType.KEY_PRESS:
            self._execute_key_press(data)
        elif action_type == ActionType.KEY_HOLD:
            self._execute_key_hold(data)
        elif action_type == ActionType.KEY_RELEASE:
            self._execute_key_release(data)
        elif action_type == ActionType.TYPE_TEXT:
            self._execute_type_text(data)
        elif action_type == ActionType.MOUSE_MOVE:
            self._execute_mouse_move(data)
        elif action_type == ActionType.MOUSE_DRAG:
            self._execute_mouse_drag(data)
        elif action_type == ActionType.WAIT:
            self._execute_wait(data)
        elif action_type == ActionType.WAIT_IMAGE:
            self._execute_wait_image(data)
        elif action_type == ActionType.IF_IMAGE:
            self._execute_if_image(action, data)
        elif action_type == ActionType.IF_NOT_IMAGE:
            self._execute_if_not_image(action, data)
        elif action_type == ActionType.FIND_IMAGE:
            self._execute_find_image(data)
        elif action_type == ActionType.LOOP_START:
            self._execute_loop_start(action, data)
        elif action_type == ActionType.LOOP_END:
            self._execute_loop_end()
        elif action_type == ActionType.BREAK:
            self._execute_break()
        elif action_type == ActionType.CONTINUE:
            self._execute_continue()
        elif action_type == ActionType.SET_VARIABLE:
            self._execute_set_variable(data)
        elif action_type == ActionType.IF_VARIABLE:
            self._execute_if_variable(action, data)
        elif action_type == ActionType.COUNTER_CHECK:
            self._execute_counter_check(data)
        elif action_type == ActionType.SCREENSHOT:
            self._execute_screenshot(data)
        elif action_type == ActionType.DISCORD_SEND:
            self._execute_discord_send(data)
    
    def _execute_click(self, data: Dict[str, Any]):
        click_data = ClickActionData.from_dict(data)
        x, y = click_data.x, click_data.y
        
        if click_data.relative:
            canvas_rect = self._get_canvas_rect()
            x += canvas_rect.x
            y += canvas_rect.y
        
        pyautogui.click(x, y, duration=click_data.duration, 
                       button=click_data.click_type.value)
    
    def _execute_double_click(self, data: Dict[str, Any]):
        click_data = ClickActionData.from_dict(data)
        x, y = click_data.x, click_data.y
        
        if click_data.relative:
            canvas_rect = self._get_canvas_rect()
            x += canvas_rect.x
            y += canvas_rect.y
        
        pyautogui.doubleClick(x, y, duration=click_data.duration)
    
    def _execute_right_click(self, data: Dict[str, Any]):
        click_data = ClickActionData.from_dict(data)
        x, y = click_data.x, click_data.y
        
        if click_data.relative:
            canvas_rect = self._get_canvas_rect()
            x += canvas_rect.x
            y += canvas_rect.y
        
        pyautogui.rightClick(x, y, duration=click_data.duration)
    
    def _execute_key_press(self, data: Dict[str, Any]):
        key_data = KeyActionData.from_dict(data)
        
        for mod in key_data.modifiers:
            pyautogui.keyDown(mod)
        
        pyautogui.press(key_data.key, interval=key_data.duration)
        
        for mod in reversed(key_data.modifiers):
            pyautogui.keyUp(mod)
    
    def _execute_key_hold(self, data: Dict[str, Any]):
        key_data = KeyActionData.from_dict(data)
        
        for mod in key_data.modifiers:
            pyautogui.keyDown(mod)
        
        pyautogui.keyDown(key_data.key)
    
    def _execute_key_release(self, data: Dict[str, Any]):
        key_data = KeyActionData.from_dict(data)
        
        pyautogui.keyUp(key_data.key)
        
        for mod in reversed(key_data.modifiers):
            pyautogui.keyUp(mod)
    
    def _execute_type_text(self, data: Dict[str, Any]):
        text = data.get('text', '')
        interval = data.get('interval', 0.05)
        pyautogui.write(text, interval=interval)
    
    def _execute_mouse_move(self, data: Dict[str, Any]):
        x = data.get('x', 0)
        y = data.get('y', 0)
        relative = data.get('relative', True)
        duration = data.get('duration', 0.5)
        
        if relative:
            canvas_rect = self._get_canvas_rect()
            x += canvas_rect.x
            y += canvas_rect.y
        
        pyautogui.moveTo(x, y, duration=duration)
    
    def _execute_mouse_drag(self, data: Dict[str, Any]):
        start_x = data.get('start_x', 0)
        start_y = data.get('start_y', 0)
        end_x = data.get('end_x', 0)
        end_y = data.get('end_y', 0)
        relative = data.get('relative', True)
        duration = data.get('duration', 0.5)
        
        if relative:
            canvas_rect = self._get_canvas_rect()
            start_x += canvas_rect.x
            start_y += canvas_rect.y
            end_x += canvas_rect.x
            end_y += canvas_rect.y
        
        pyautogui.moveTo(start_x, start_y)
        pyautogui.dragTo(end_x, end_y, duration=duration, button='left')
    
    def _execute_wait(self, data: Dict[str, Any]):
        wait_data = WaitActionData.from_dict(data)
        duration = wait_data.duration
        
        if wait_data.randomize:
            import random
            duration = random.uniform(wait_data.min_duration, wait_data.max_duration)
        
        self._sleep_with_check(duration)
    
    def _execute_wait_image(self, data: Dict[str, Any]):
        img_data = ImageActionData.from_dict(data)
        self._wait_for_image(img_data.image_path, img_data.confidence, 
                            img_data.timeout, img_data.region)
    
    def _execute_if_image(self, action: Action, data: Dict[str, Any]):
        img_data = ImageActionData.from_dict(data)
        found = self._find_image(img_data.image_path, img_data.confidence, img_data.region)
        
        if not found:
            self._skip_to_matching_end(action)
    
    def _execute_if_not_image(self, action: Action, data: Dict[str, Any]):
        img_data = ImageActionData.from_dict(data)
        found = self._find_image(img_data.image_path, img_data.confidence, img_data.region)
        
        if found:
            self._skip_to_matching_end(action)
    
    def _execute_find_image(self, data: Dict[str, Any]):
        img_data = ImageActionData.from_dict(data)
        result = self._find_image(img_data.image_path, img_data.confidence, img_data.region)
        
        if result and img_data.click_when_found:
            x, y = result
            x += img_data.click_offset.x
            y += img_data.click_offset.y
            pyautogui.click(x, y)
        
        self.variables['last_find_result'] = result
    
    def _execute_loop_start(self, action: Action, data: Dict[str, Any]):
        loop_data = LoopActionData.from_dict(data)
        
        loop_info = {
            'action_index': self.current_action_index,
            'count': loop_data.count,
            'current': 0,
            'condition': loop_data.condition,
            'variable': loop_data.variable
        }
        self.loop_stack.append(loop_info)
    
    def _execute_loop_end(self):
        if not self.loop_stack:
            return
        
        loop_info = self.loop_stack[-1]
        loop_info['current'] += 1
        
        should_continue = False
        if loop_info['count'] == 0:
            should_continue = True
        elif loop_info['current'] < loop_info['count']:
            should_continue = True
        elif loop_info['condition']:
            try:
                should_continue = eval(loop_info['condition'], {}, self.variables)
            except:
                should_continue = False
        elif loop_info['variable'] and loop_info['variable'] in self.variables:
            should_continue = bool(self.variables[loop_info['variable']])
        
        if should_continue:
            self.current_action_index = loop_info['action_index']
        else:
            self.loop_stack.pop()
    
    def _execute_break(self):
        if self.loop_stack:
            self.loop_stack.pop()
            self._skip_to_after_loop_end()
    
    def _execute_continue(self):
        if self.loop_stack:
            loop_info = self.loop_stack[-1]
            self.current_action_index = loop_info['action_index']
    
    def _execute_set_variable(self, data: Dict[str, Any]):
        var_data = VariableActionData.from_dict(data)
        
        if var_data.operation == "set":
            self.variables[var_data.name] = var_data.value
        elif var_data.operation == "add":
            self.variables[var_data.name] = self.variables.get(var_data.name, 0) + var_data.value
        elif var_data.operation == "subtract":
            self.variables[var_data.name] = self.variables.get(var_data.name, 0) - var_data.value
        elif var_data.operation == "multiply":
            self.variables[var_data.name] = self.variables.get(var_data.name, 1) * var_data.value
        elif var_data.operation == "divide":
            self.variables[var_data.name] = self.variables.get(var_data.name, 1) / var_data.value
    
    def _execute_if_variable(self, action: Action, data: Dict[str, Any]):
        var_data = VariableActionData.from_dict(data)
        value = self.variables.get(var_data.name, None)
        
        condition_met = False
        if var_data.operation == "equals":
            condition_met = value == var_data.value
        elif var_data.operation == "not_equals":
            condition_met = value != var_data.value
        elif var_data.operation == "greater":
            condition_met = value > var_data.value
        elif var_data.operation == "less":
            condition_met = value < var_data.value
        elif var_data.operation == "contains":
            condition_met = var_data.value in str(value)
        elif var_data.operation == "is_true":
            condition_met = bool(value)
        elif var_data.operation == "is_false":
            condition_met = not bool(value)
        
        if not condition_met:
            self._skip_to_matching_end(action)
    
    def _execute_counter_check(self, data: Dict[str, Any]):
        counter_data = CounterActionData.from_dict(data)
        
        current_value = self._read_counter(counter_data.image_path, counter_data.region)
        previous_value = self.counters.get(counter_data.counter_name, 0)
        
        if current_value is not None:
            self.counters[counter_data.counter_name] = current_value
            change = current_value - previous_value
            
            if counter_data.expected_change != 0 and change != counter_data.expected_change:
                self._log(f"Counter {counter_data.counter_name} changed by {change}, expected {counter_data.expected_change}")
    
    def _execute_screenshot(self, data: Dict[str, Any]):
        screenshot = self.capture_canvas()
        if self.on_screenshot:
            self.on_screenshot(screenshot)
    
    def _execute_discord_send(self, data: Dict[str, Any]):
        pass
    
    def _get_canvas_rect(self) -> Rect:
        return Rect(0, 0, CONFIG.get().canvas.width, CONFIG.get().canvas.height)
    
    def _find_image(self, image_path: str, confidence: float = 0.8, 
                    region: Optional[Rect] = None) -> Optional[tuple]:
        if not image_path or not Path(image_path).exists():
            return None
        
        try:
            screenshot = self.capture_canvas(region)
            if screenshot is None:
                return None
            
            template = cv2.imread(image_path, cv2.IMREAD_COLOR)
            if template is None:
                return None
            
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= confidence:
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                
                if region:
                    center_x += region.x
                    center_y += region.y
                
                return (center_x, center_y)
        except Exception as e:
            self._log(f"Image find error: {e}")
        
        return None
    
    def _wait_for_image(self, image_path: str, confidence: float, 
                        timeout: float, region: Optional[Rect]):
        start_time = time.time()
        while time.time() - start_time < timeout and not self._stop_event.is_set():
            if self._pause_event.is_set():
                time.sleep(0.1)
                continue
            
            result = self._find_image(image_path, confidence, region)
            if result:
                return result
            time.sleep(0.1)
        return None
    
    def _skip_to_matching_end(self, action: Action):
        depth = 1
        for i in range(self.current_action_index + 1, len(self.actions)):
            next_action = self.actions[i]
            if next_action.type in (ActionType.IF_IMAGE, ActionType.IF_NOT_IMAGE, 
                                   ActionType.IF_VARIABLE, ActionType.LOOP_START):
                depth += 1
            elif next_action.type in (ActionType.LOOP_END,):
                depth -= 1
                if depth == 0:
                    self.current_action_index = i
                    return
        self.current_action_index = len(self.actions)
    
    def _skip_to_after_loop_end(self):
        depth = 1
        for i in range(self.current_action_index + 1, len(self.actions)):
            next_action = self.actions[i]
            if next_action.type == ActionType.LOOP_START:
                depth += 1
            elif next_action.type == ActionType.LOOP_END:
                depth -= 1
                if depth == 0:
                    self.current_action_index = i
                    return
        self.current_action_index = len(self.actions)
    
    def capture_canvas(self, region: Optional[Rect] = None) -> Optional[np.ndarray]:
        try:
            canvas_config = CONFIG.get().canvas
            if region:
                x, y, w, h = region.x, region.y, region.width, region.height
            else:
                x, y, w, h = 0, 0, canvas_config.width, canvas_config.height
            
            screenshot = pyautogui.screenshot(region=(x, y, w, h))
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        except Exception as e:
            self._log(f"Screenshot error: {e}")
            return None
    
    def _read_counter(self, image_path: str, region: Optional[Rect]) -> Optional[int]:
        try:
            result = self._find_image(image_path, 0.8, region)
            if not result:
                return None
            
            x, y = result
            read_region = Rect(x, y + 30, 100, 40)
            screenshot = self.capture_canvas(read_region)
            
            if screenshot is not None:
                gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
                
                import pytesseract
                try:
                    text = pytesseract.image_to_string(thresh, config='--psm 7 digits')
                    return int(''.join(filter(str.isdigit, text)))
                except:
                    pass
        except Exception as e:
            self._log(f"Counter read error: {e}")
        return None
    
    def start_recording(self):
        if self.state == PlaybackState.RECORDING:
            return
        
        self._recorded_events = []
        self._record_start_time = time.time()
        self._stop_event.clear()
        
        self._mouse_listener = mouse.Listener(
            on_click=self._on_mouse_click,
            on_move=self._on_mouse_move,
            on_scroll=self._on_mouse_scroll
        )
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        
        self._mouse_listener.start()
        self._keyboard_listener.start()
        self._notify_state_change(PlaybackState.RECORDING)
    
    def stop_recording(self) -> List[Action]:
        if self.state != PlaybackState.RECORDING:
            return []
        
        if self._mouse_listener:
            self._mouse_listener.stop()
        if self._keyboard_listener:
            self._keyboard_listener.stop()
        
        self._mouse_listener = None
        self._keyboard_listener = None
        
        actions = self._convert_events_to_actions()
        self._notify_state_change(PlaybackState.STOPPED)
        return actions
    
    def _on_mouse_click(self, x: int, y: int, button: mouse.Button, pressed: bool):
        if pressed:
            canvas_rect = self._get_canvas_rect()
            rel_x = x - canvas_rect.x
            rel_y = y - canvas_rect.y
            
            click_type = ClickType.LEFT
            if button == mouse.Button.right:
                click_type = ClickType.RIGHT
            elif button == mouse.Button.middle:
                click_type = ClickType.MIDDLE
            
            self._recorded_events.append(RecordedEvent(
                timestamp=time.time() - self._record_start_time,
                event_type="click",
                data={"x": rel_x, "y": rel_y, "click_type": click_type.value}
            ))
    
    def _on_mouse_move(self, x: int, y: int):
        pass
    
    def _on_mouse_scroll(self, x: int, y: int, dx: int, dy: int):
        self._recorded_events.append(RecordedEvent(
            timestamp=time.time() - self._record_start_time,
            event_type="scroll",
            data={"dx": dx, "dy": dy}
        ))
    
    def _on_key_press(self, key):
        try:
            key_str = key.char if hasattr(key, 'char') else str(key).replace('Key.', '')
            self._recorded_events.append(RecordedEvent(
                timestamp=time.time() - self._record_start_time,
                event_type="key_press",
                data={"key": key_str}
            ))
        except:
            pass
    
    def _on_key_release(self, key):
        try:
            key_str = key.char if hasattr(key, 'char') else str(key).replace('Key.', '')
            self._recorded_events.append(RecordedEvent(
                timestamp=time.time() - self._record_start_time,
                event_type="key_release",
                data={"key": key_str}
            ))
        except:
            pass
    
    def _convert_events_to_actions(self) -> List[Action]:
        actions = []
        last_time = 0
        
        for event in self._recorded_events:
            wait_time = event.timestamp - last_time
            if wait_time > 0.1:
                actions.append(create_wait_action(wait_time))
            
            if event.event_type == "click":
                data = event.data
                action = create_click_action(
                    data["x"], data["y"],
                    click_type=ClickType(data["click_type"])
                )
                actions.append(action)
            elif event.event_type == "key_press":
                action = create_key_action(event.data["key"], ActionType.KEY_PRESS)
                actions.append(action)
        
        return actions
    
    def save_macro(self, filepath: str):
        import json
        data = {
            "version": "1.0",
            "actions": [action.to_dict() for action in self.actions],
            "variables": self.variables,
            "counters": self.counters
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_macro(self, filepath: str):
        import json
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.actions = [Action.from_dict(a) for a in data.get("actions", [])]
        self.variables = data.get("variables", {})
        self.counters = data.get("counters", {})


class MacroManager:
    def __init__(self, engine: AutomationEngine):
        self.engine = engine
        self.macro_folder = Path(CONFIG.get().macro_folder)
        self.macro_folder.mkdir(parents=True, exist_ok=True)
    
    def save_macro(self, name: str) -> str:
        filepath = self.macro_folder / f"{name}.json"
        self.engine.save_macro(str(filepath))
        return str(filepath)
    
    def load_macro(self, name: str) -> bool:
        filepath = self.macro_folder / f"{name}.json"
        if filepath.exists():
            self.engine.load_macro(str(filepath))
            return True
        return False
    
    def list_macros(self) -> List[str]:
        return [f.stem for f in self.macro_folder.glob("*.json")]
    
    def delete_macro(self, name: str) -> bool:
        filepath = self.macro_folder / f"{name}.json"
        if filepath.exists():
            filepath.unlink()
            return True
        return False
    
    def duplicate_macro(self, name: str, new_name: str) -> bool:
        filepath = self.macro_folder / f"{name}.json"
        new_filepath = self.macro_folder / f"{new_name}.json"
        if filepath.exists():
            import shutil
            shutil.copy2(filepath, new_filepath)
            return True
        return False


ENGINE = AutomationEngine()
MACRO_MANAGER = MacroManager(ENGINE)