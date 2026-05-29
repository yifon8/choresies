from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional


@dataclass
class Chore:
    name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "undone"          # "undone" | "done"
    recurring: bool = False
    interval_days: Optional[int] = None
    completions: int = 0
    last_done: Optional[date] = None
    next_due: Optional[date] = None

    # ------------------------------------------------------------------
    # Mutations — all state changes go through these methods
    # ------------------------------------------------------------------

    def mark_done(self) -> None:
        today = date.today()
        self.status = "done"
        self.completions += 1
        self.last_done = today
        if self.recurring and self.interval_days:
            self.next_due = today + timedelta(days=self.interval_days)
        else:
            self.next_due = None

    def redo(self) -> None:
        # Returns chore to the wheel without touching completions/last_done/interval
        self.status = "undone"

    def set_recurrence(self, interval_days: int) -> None:
        self.recurring = True
        self.interval_days = interval_days
        if self.last_done:
            self.next_due = self.last_done + timedelta(days=interval_days)

    def clear_recurrence(self) -> None:
        self.recurring = False
        self.interval_days = None
        self.next_due = None

    def is_due(self) -> bool:
        """True if a recurring done chore should return to the wheel today."""
        return (
            self.status == "done"
            and self.recurring
            and self.next_due is not None
            and self.next_due <= date.today()
        )

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "recurring": self.recurring,
            "interval_days": self.interval_days,
            "completions": self.completions,
            "last_done": self.last_done.isoformat() if self.last_done else None,
            "next_due": self.next_due.isoformat() if self.next_due else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Chore":
        return cls(
            id=data["id"],
            name=data["name"],
            status=data.get("status", "undone"),
            recurring=data.get("recurring", False),
            interval_days=data.get("interval_days"),
            completions=data.get("completions", 0),
            last_done=date.fromisoformat(data["last_done"]) if data.get("last_done") else None,
            next_due=date.fromisoformat(data["next_due"]) if data.get("next_due") else None,
        )

    # ------------------------------------------------------------------
    # Human-friendly due-date label (used by done list)
    # ------------------------------------------------------------------

    def due_label(self) -> str:
        if not self.recurring or self.next_due is None:
            return "One-time"
        today = date.today()
        delta = (self.next_due - today).days
        if delta < 0:
            return "Overdue"
        if delta == 0:
            return "Due today"
        if delta == 1:
            return "Due tomorrow"
        if delta <= 6:
            return f"Due {self.next_due.strftime('%A')}"
        return f"Due {self.next_due.strftime('%b')} {self.next_due.day}"
