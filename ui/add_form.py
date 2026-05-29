from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

# Frequency presets: label -> interval_days
PRESETS: list[tuple[str, int]] = [
    ("Daily", 1),
    ("Every 2 days", 2),
    ("Weekly", 7),
    ("Every 2 weeks", 14),
    ("Monthly", 30),
]
PRESET_LABELS = [label for label, _ in PRESETS]
CUSTOM_LABEL = "Custom…"

RECUR_COLOR = "#9B59B6"


class AddForm(tk.Frame):
    """
    Top bar: recurring controls (top row) + chore name entry + Add button (bottom row).

    Calls on_add(name, interval_days_or_None) when the user submits.
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_add: Callable[[str, Optional[int]], None],
        on_error: Callable[[str], None] = lambda _: None,
        **kwargs,
    ):
        super().__init__(parent, bg="#1E1E2E", **kwargs)
        self.on_add = on_add
        self.on_error = on_error
        self._build()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build(self) -> None:
        # Row 1 — recurring checkbox + frequency controls
        row1 = tk.Frame(self, bg="#1E1E2E")
        row1.pack(fill=tk.X, padx=12, pady=(10, 2))

        self._recurring_var = tk.BooleanVar(value=False)
        recur_chk = tk.Checkbutton(
            row1,
            text="Recurring",
            variable=self._recurring_var,
            command=self._on_recurring_toggle,
            bg="#1E1E2E",
            fg=RECUR_COLOR,
            selectcolor="#2A2A3E",
            activebackground="#1E1E2E",
            activeforeground=RECUR_COLOR,
            font=("Helvetica", 11, "bold"),
        )
        recur_chk.pack(side=tk.LEFT)

        self._freq_frame = tk.Frame(row1, bg="#1E1E2E")
        self._freq_frame.pack(side=tk.LEFT, padx=(8, 0))

        self._preset_var = tk.StringVar(value=PRESET_LABELS[2])  # default: Weekly
        self._preset_menu = ttk.Combobox(
            self._freq_frame,
            textvariable=self._preset_var,
            values=PRESET_LABELS + [CUSTOM_LABEL],
            state="readonly",
            width=14,
            font=("Helvetica", 11),
        )
        self._preset_menu.pack(side=tk.LEFT)
        self._preset_menu.bind("<<ComboboxSelected>>", self._on_preset_change)

        # Custom sub-frame — hidden until "Custom…" is selected
        self._custom_frame = tk.Frame(self._freq_frame, bg="#1E1E2E")

        tk.Label(
            self._custom_frame,
            text="Custom:",
            bg="#1E1E2E",
            fg="#AAAACC",
            font=("Helvetica", 11),
        ).pack(side=tk.LEFT, padx=(10, 4))

        self._custom_var = tk.StringVar()
        self._custom_entry = tk.Entry(
            self._custom_frame,
            textvariable=self._custom_var,
            width=5,
            font=("Helvetica", 11),
            bg="#2A2A3E",
            fg="#FFFFFF",
            insertbackground="#FFFFFF",
            relief=tk.FLAT,
        )
        self._custom_entry.pack(side=tk.LEFT, ipady=3)

        tk.Label(
            self._custom_frame,
            text="days",
            bg="#1E1E2E",
            fg="#AAAACC",
            font=("Helvetica", 11),
        ).pack(side=tk.LEFT, padx=(4, 0))

        # Hide recurrence controls until checkbox is ticked
        self._freq_frame.pack_forget()

        # Row 2 — name entry + Add button
        row2 = tk.Frame(self, bg="#1E1E2E")
        row2.pack(fill=tk.X, padx=12, pady=(2, 10))

        self._name_var = tk.StringVar()
        self._name_entry = tk.Entry(
            row2,
            textvariable=self._name_var,
            font=("Helvetica", 13),
            bg="#2A2A3E",
            fg="#FFFFFF",
            insertbackground="#FFFFFF",
            relief=tk.FLAT,
            width=28,
        )
        self._name_entry.pack(side=tk.LEFT, ipady=6, padx=(0, 8))
        self._name_entry.bind("<Return>", lambda _: self._submit())

        add_btn = tk.Button(
            row2,
            text="Add",
            command=self._submit,
            bg="#3498DB",
            fg="#FFFFFF",
            font=("Helvetica", 12, "bold"),
            relief=tk.FLAT,
            padx=14,
            pady=4,
            cursor="hand2",
        )
        add_btn.pack(side=tk.LEFT)

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_recurring_toggle(self) -> None:
        if self._recurring_var.get():
            self._freq_frame.pack(side=tk.LEFT, padx=(8, 0))
            # Re-apply custom visibility based on current selection
            self._on_preset_change()
        else:
            self._freq_frame.pack_forget()

    def _on_preset_change(self, _event=None) -> None:
        is_custom = self._preset_var.get() == CUSTOM_LABEL
        if is_custom:
            self._custom_frame.pack(side=tk.LEFT)
        else:
            self._custom_frame.pack_forget()
            self._custom_var.set("")

    def _submit(self) -> None:
        name = self._name_var.get().strip()[:30]
        if not name:
            self._name_entry.focus_set()
            self.on_error("Please type a chore into the field")
            return

        interval: Optional[int] = None
        if self._recurring_var.get():
            interval = self._resolve_interval()
            if interval is None:
                self.on_error("Please enter a number of days for the custom interval")
                return

        self._name_var.set("")
        self._name_entry.focus_set()
        self.on_add(name, interval)

    def _resolve_interval(self) -> Optional[int]:
        preset = self._preset_var.get()
        if preset == CUSTOM_LABEL:
            try:
                val = int(self._custom_var.get().strip())
                return val if val > 0 else None
            except ValueError:
                return None
        for label, days in PRESETS:
            if label == preset:
                return days
        return None
