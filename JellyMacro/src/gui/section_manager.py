"""
Section manager for JellyMacro - handles saving and duplicating sections
"""

import json
import os
import shutil
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

from src.actions import Action
from src.config import CONFIG


@dataclass
class Section:
    name: str
    description: str
    actions: List[Action]
    created_at: float
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "actions": [a.to_dict() for a in self.actions],
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Section':
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            actions=[Action.from_dict(a) for a in data.get("actions", [])],
            created_at=data.get("created_at", 0)
        )


class SectionManager:
    def __init__(self):
        self.sections_folder = Path(CONFIG.get().macro_folder) / "sections"
        self.sections_folder.mkdir(parents=True, exist_ok=True)
    
    def save_section(self, name: str, actions: List[Action], 
                     description: str = "") -> str:
        """Save a group of actions as a reusable section"""
        import time
        section = Section(
            name=name,
            description=description,
            actions=[a.copy() for a in actions],
            created_at=time.time()
        )
        
        filepath = self.sections_folder / f"{name}.json"
        with open(filepath, 'w') as f:
            json.dump(section.to_dict(), f, indent=2)
        
        return str(filepath)
    
    def load_section(self, name: str) -> Optional[Section]:
        filepath = self.sections_folder / f"{name}.json"
        if filepath.exists():
            with open(filepath, 'r') as f:
                data = json.load(f)
            return Section.from_dict(data)
        return None
    
    def list_sections(self) -> List[str]:
        return [f.stem for f in self.sections_folder.glob("*.json")]
    
    def delete_section(self, name: str) -> bool:
        filepath = self.sections_folder / f"{name}.json"
        if filepath.exists():
            filepath.unlink()
            return True
        return False
    
    def duplicate_section(self, actions: List[Action], indices: List[int],
                          name: str, description: str = "") -> Optional[str]:
        """Duplicate selected actions as a section"""
        selected_actions = [actions[i].copy() for i in indices if 0 <= i < len(actions)]
        if not selected_actions:
            return None
        
        return self.save_section(name, selected_actions, description)
    
    def get_section_as_actions(self, name: str) -> List[Action]:
        section = self.load_section(name)
        if section:
            return [a.copy() for a in section.actions]
        return []