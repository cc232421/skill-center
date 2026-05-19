"""
conftest.py — pytest configuration for sel-framework
"""
import sys
from pathlib import Path

# Add sel-framework/ root so skill subdirectories are importable as packages
_root = Path(__file__).parent
sys.path.insert(0, str(_root))

import os
os.environ.pop("SEL_DATA_DIR", None)          # use default ~/.sel_data
os.environ.pop("SEL_ALERT_WEBHOOK_URL", None)  # disable webhook in tests
