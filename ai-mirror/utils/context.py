# utils/context.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

def get_context() -> Dict:
    """
    Load optional runtime context (e.g., settings) from config.json at repo root.
    Returns {} if the file does not exist or is invalid.
    """
    try:
        root = Path(__file__).resolve().parents[1]  # repo root (../.. from utils/)
        cfg = root / "config.json"
        if cfg.is_file():
            with cfg.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
    except Exception:
        pass
    return {}
