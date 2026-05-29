from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import List
import sys

from chores.model import Chore


def get_data_path() -> Path:
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle
        return Path(sys.executable).parent / "data"
    return Path(__file__).parent.parent / "data"


DATA_FILE = get_data_path() / "chores.json"


def load_chores() -> List[Chore]:
    if not DATA_FILE.exists():
        return []
    with DATA_FILE.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return [Chore.from_dict(item) for item in raw]


def save_chores(chores: List[Chore]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump([c.to_dict() for c in chores], f, indent=2)


def check_recurring_returns(chores: List[Chore]) -> bool:
    """
    Flip any overdue recurring chores back to undone.
    Returns True if any chores changed (so the caller knows to redraw).
    """
    changed = False
    for chore in chores:
        if chore.is_due():
            chore.status = "undone"
            changed = True
    return changed
