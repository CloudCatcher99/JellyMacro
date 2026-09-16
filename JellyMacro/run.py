#!/usr/bin/env python3
"""
JellyMacro - Advanced Macro Automation Tool for Roblox
Author: Xeu
"""

import sys
import os
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.main import main

if __name__ == "__main__":
    main()