"""
Discord webhook integration for JellyMacro
"""

import threading
import time
import requests
import json
from typing import Optional, Dict, Any
from pathlib import Path
import base64
import io

import cv2
import numpy as np

from src.config import CONFIG
from src.engine import ENGINE


class DiscordWebhook:
    def __init__(self):
        self.webhook_url: str = ""
        self.enabled: bool = False
        self.interval_minutes: int = 30
        self.send_screenshot: bool = True
        self.custom_message: str = "JellyMacro Status Update"
        self.include_counters: bool = True
        self.include_variables: bool = False
        
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_send_time: float = 0
    
    def configure(self, webhook_url: str, enabled: bool = True,
                  interval_minutes: int = 30, send_screenshot: bool = True,
                  custom_message: str = "", include_counters: bool = True,
                  include_variables: bool = False):
        self.webhook_url = webhook_url
        self.enabled = enabled
        self.interval_minutes = interval_minutes
        self.send_screenshot = send_screenshot
        self.custom_message = custom_message or "JellyMacro Status Update"
        self.include_counters = include_counters
        self.include_variables = include_variables
        
        config = CONFIG.get()
        config.discord.webhook_url = webhook_url
        config.discord.enabled = enabled
        config.discord.interval_minutes = interval_minutes
        config.discord.send_screenshot = send_screenshot
        CONFIG.save()
    
    def start(self):
        if not self.enabled or not self.webhook_url:
            return
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
    
    def _run_loop(self):
        while not self._stop_event.is_set():
            current_time = time.time()
            if current_time - self._last_send_time >= self.interval_minutes * 60:
                self.send_status()
                self._last_send_time = current_time
            
            time.sleep(10)
    
    def send_status(self, force: bool = False) -> bool:
        if not self.webhook_url:
            return False
        
        try:
            embed = self._create_embed()
            files = {}
            
            if self.send_screenshot:
                screenshot = ENGINE.capture_canvas()
                if screenshot is not None:
                    _, buffer = cv2.imencode('.png', screenshot)
                    files['file'] = ('screenshot.png', buffer.tobytes(), 'image/png')
            
            data = {
                "embeds": [embed]
            }
            
            if files:
                response = requests.post(
                    self.webhook_url,
                    data={"payload_json": json.dumps(data)},
                    files=files,
                    timeout=10
                )
            else:
                response = requests.post(
                    self.webhook_url,
                    json=data,
                    timeout=10
                )
            
            return response.status_code == 204 or response.status_code == 200
        except Exception as e:
            print(f"Discord webhook error: {e}")
            return False
    
    def _create_embed(self) -> Dict[str, Any]:
        config = CONFIG.get()
        
        fields = [
            {
                "name": "Status",
                "value": "Running" if ENGINE.state.value == "playing" else "Stopped",
                "inline": True
            },
            {
                "name": "Current Action",
                "value": f"{ENGINE.current_action_index + 1} / {len(ENGINE.actions)}",
                "inline": True
            }
        ]
        
        if self.include_counters and ENGINE.counters:
            counter_text = "\n".join([f"**{k}**: {v}" for k, v in ENGINE.counters.items()])
            fields.append({
                "name": "Counters",
                "value": counter_text or "None",
                "inline": False
            })
        
        if self.include_variables and ENGINE.variables:
            var_text = "\n".join([f"**{k}**: {v}" for k, v in list(ENGINE.variables.items())[:10]])
            fields.append({
                "name": "Variables",
                "value": var_text or "None",
                "inline": False
            })
        
        embed = {
            "title": self.custom_message,
            "color": 0x00FF7F if ENGINE.state.value == "playing" else 0xFF4444,
            "fields": fields,
            "footer": {
                "text": "JellyMacro by Xeu"
            },
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
        return embed
    
    def send_custom(self, title: str, description: str, color: int = 0x0099FF,
                    fields: list = None, screenshot: bool = False) -> bool:
        if not self.webhook_url:
            return False
        
        try:
            embed = {
                "title": title,
                "description": description,
                "color": color,
                "fields": fields or [],
                "footer": {"text": "JellyMacro by Xeu"},
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            
            files = {}
            if screenshot or self.send_screenshot:
                img = ENGINE.capture_canvas()
                if img is not None:
                    _, buffer = cv2.imencode('.png', img)
                    files['file'] = ('screenshot.png', buffer.tobytes(), 'image/png')
            
            data = {"embeds": [embed]}
            
            if files:
                response = requests.post(
                    self.webhook_url,
                    data={"payload_json": json.dumps(data)},
                    files=files,
                    timeout=10
                )
            else:
                response = requests.post(
                    self.webhook_url,
                    json=data,
                    timeout=10
                )
            
            return response.status_code in (200, 204)
        except Exception as e:
            print(f"Discord webhook error: {e}")
            return False


DISCORD_WEBHOOK = DiscordWebhook()