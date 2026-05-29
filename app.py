from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, filedialog
from typing import List, Optional
from datetime import date

from chores.model import Chore
from chores.store import load_chores, save_chores, check_recurring_returns
from wheel.canvas import WheelCanvas
from ui.add_form import AddForm
from ui.undone_list import UndoneList
from ui.done_list import DoneList

WINDOW_TITLE = "Chore Wheel 🎡"
WINDOW_MIN_W = 900
WINDOW_MIN_H = 600
RECURRING_CHECK_INTERVAL_MS = 60 * 60 * 1000  # 1 hour


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(WINDOW_TITLE)
        self.minsize(WINDOW_MIN_W, WINDOW_MIN_H)
        self.configure(bg="#1E1E2E")

        self.chores: List[Chore] = load_chores()

        self._build_layout()
        self._refresh_all()

        # Auto-return overdue recurring chores on launch
        if check_recurring_returns(self.chores):
            save_chores(self.chores)
            self._refresh_all()

        # Hourly recurring check
        self._schedule_recurring_check()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_layout(self) -> None:
        # Top bar: add form
        self._add_form = AddForm(self, on_add=self._on_add)
        self._add_form.pack(fill=tk.X)

        tk.Frame(self, bg="#3A3A5E", height=1).pack(fill=tk.X)

        # Main area: wheel (left) + lists (right)
        main = tk.Frame(self, bg="#1E1E2E")
        main.pack(fill=tk.BOTH, expand=True)

        # Left panel — wheel + spin button + result label
        left = tk.Frame(main, bg="#1E1E2E")
        left.pack(side=tk.LEFT, fill=tk.BOTH, padx=8, pady=8)

        self._wheel = WheelCanvas(left, on_winner=self._on_winner)
        self._wheel.set_mark_done_callback(self.mark_done)
        self._wheel.pack()

        spin_btn = tk.Button(
            left,
            text="🎯  Spin",
            command=self._wheel.spin,
            bg="#3498DB",
            fg="#FFFFFF",
            font=("Helvetica", 14, "bold"),
            relief=tk.FLAT,
            padx=24,
            pady=8,
            cursor="hand2",
        )
        spin_btn.pack(pady=(8, 4))

        self._result_var = tk.StringVar(value="")
        self._result_label = tk.Label(
            left,
            textvariable=self._result_var,
            bg="#1E1E2E",
            fg="#F39C12",
            font=("Helvetica", 13, "bold"),
        )
        self._result_label.pack()

        # Right panel — undone list (top) + done list (bottom)
        right = tk.Frame(main, bg="#1E1E2E")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8), pady=8)

        self._undone_list = UndoneList(right, on_done=self.mark_done)
        self._undone_list.pack(fill=tk.BOTH, expand=True)

        tk.Frame(right, bg="#3A3A5E", height=1).pack(fill=tk.X, padx=8)

        self._done_list = DoneList(
            right,
            on_redo=self.redo_chore,
            on_set_recur=self._on_set_recur,
        )
        self._done_list.pack(fill=tk.BOTH, expand=True)

        # Bottom bar: export & clear button
        tk.Frame(self, bg="#3A3A5E", height=1).pack(fill=tk.X)
        bottom = tk.Frame(self, bg="#1E1E2E")
        bottom.pack(fill=tk.X, padx=12, pady=8)
        tk.Button(
            bottom,
            text="⬇ Export & Clear Lists",
            command=self._on_export_and_clear,
            bg="#555577",
            fg="#FFFFFF",
            font=("Helvetica", 11),
            relief=tk.FLAT,
            padx=14,
            pady=5,
            cursor="hand2",
        ).pack(side=tk.RIGHT)

        # Floating error overlay (hidden until needed)
        self._error_label = tk.Label(
            self,
            text="",
            bg="#C0392B",
            fg="#FFFFFF",
            font=("Helvetica", 12, "bold"),
            padx=18,
            pady=10,
            wraplength=360,
            justify=tk.CENTER,
            relief=tk.FLAT,
        )
        self._error_dismiss_job: Optional[str] = None

    # ------------------------------------------------------------------
    # Single source of truth: state mutations
    # ------------------------------------------------------------------

    def mark_done(self, chore_id: str) -> None:
        chore = self._find(chore_id)
        if chore is None or chore.status == "done":
            return
        chore.mark_done()
        save_chores(self.chores)
        self._refresh_all()

    def redo_chore(self, chore_id: str) -> None:
        chore = self._find(chore_id)
        if chore is None or chore.status == "undone":
            return
        chore.redo()
        save_chores(self.chores)
        self._refresh_all()

    # ------------------------------------------------------------------
    # Callbacks from UI panels
    # ------------------------------------------------------------------

    def _on_add(self, name: str, interval_days: Optional[int]) -> None:
        name_lower = name.lower()
        for existing in self.chores:
            if existing.name.lower() == name_lower:
                if existing.status == "undone":
                    self._show_error("Chore already in To Do list")
                else:
                    self._show_error("Chore in Done list, please Redo, or schedule Recurrence")
                return
        chore = Chore(name=name)
        if interval_days is not None:
            chore.set_recurrence(interval_days)
        self.chores.append(chore)
        save_chores(self.chores)
        self._refresh_all()

    def _on_winner(self, chore: Chore) -> None:
        self._result_var.set(f"🎯  {chore.name}")

    def _on_set_recur(self, chore_id: str, interval_days: int) -> None:
        chore = self._find(chore_id)
        if chore is None:
            return
        chore.set_recurrence(interval_days)
        # If next_due is already past, return chore to wheel immediately
        if chore.is_due():
            chore.status = "undone"
        save_chores(self.chores)
        self._refresh_all()

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    def _refresh_all(self) -> None:
        self._wheel.set_chores(self.chores)
        self._undone_list.refresh(self.chores)
        self._done_list.refresh(self.chores)

    # ------------------------------------------------------------------
    # Recurring auto-return (hourly)
    # ------------------------------------------------------------------

    def _schedule_recurring_check(self) -> None:
        self.after(RECURRING_CHECK_INTERVAL_MS, self._recurring_check)

    def _recurring_check(self) -> None:
        if self._wheel.is_spinning:
            self._schedule_recurring_check()
            return
        if check_recurring_returns(self.chores):
            save_chores(self.chores)
            self._refresh_all()
        self._schedule_recurring_check()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _on_export_and_clear(self) -> None:
        confirmed = messagebox.askyesno(
            title="Export & Clear",
            message="Download To Do and Done lists as a text file and clear the lists and wheel?",
            icon=messagebox.WARNING,
        )
        if not confirmed:
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text file", "*.txt")],
            initialfile=f"chores_{date.today().isoformat()}.txt",
            title="Save chore list as",
        )
        if not path:
            return  # user cancelled the save dialog

        self._write_export(path)
        self.chores.clear()
        save_chores(self.chores)
        self._refresh_all()

    def _write_export(self, path: str) -> None:
        undone = [c for c in self.chores if c.status == "undone"]
        done = [c for c in self.chores if c.status == "done"]
        lines = []
        lines.append(f"Chore Wheel export — {date.today().isoformat()}")
        lines.append("=" * 48)
        lines.append("")
        lines.append("TO DO")
        lines.append("-" * 24)
        if undone:
            for c in undone:
                lines.append(f"  • {c.name}")
        else:
            lines.append("  (none)")
        lines.append("")
        lines.append("DONE")
        lines.append("-" * 24)
        if done:
            for c in sorted(done, key=lambda c: c.last_done or "", reverse=True):
                recur = f"  every {c.interval_days}d" if c.recurring and c.interval_days else ""
                lines.append(f"  • {c.name}  (×{c.completions}){recur}  {c.due_label()}")
        else:
            lines.append("  (none)")
        lines.append("")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _show_error(self, message: str) -> None:
        # Cancel any existing dismiss timer
        if self._error_dismiss_job:
            self.after_cancel(self._error_dismiss_job)
        self._error_label.config(text=message)
        # Centre the overlay near the top of the window
        self._error_label.place(relx=0.5, rely=0.08, anchor=tk.CENTER)
        self._error_label.lift()
        self._error_dismiss_job = self.after(3000, self._hide_error)

    def _hide_error(self) -> None:
        self._error_label.place_forget()
        self._error_dismiss_job = None

    def _find(self, chore_id: str) -> Optional[Chore]:
        return next((c for c in self.chores if c.id == chore_id), None)
