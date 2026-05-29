from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Optional

from chores.model import Chore

PRESETS: list[tuple[str, int]] = [
    ("Daily", 1),
    ("Every 2 days", 2),
    ("Weekly", 7),
    ("Every 2 weeks", 14),
    ("Monthly", 30),
]
PRESET_LABELS = [label for label, _ in PRESETS]
CUSTOM_LABEL = "Custom…"


class DoneList(tk.Frame):
    """
    Scrollable list of done chores.
    Each row shows name (strikethrough), completion count, due label,
    and Recur / Redo buttons with an inline recurrence editor.

    Callbacks (all provided by app.py):
      on_redo(chore_id)
      on_set_recur(chore_id, interval_days)
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_redo: Callable[[str], None],
        on_set_recur: Callable[[str, int], None],
        **kwargs,
    ):
        super().__init__(parent, bg="#1E1E2E", **kwargs)
        self.on_redo = on_redo
        self.on_set_recur = on_set_recur
        self._expanded: Optional[str] = None   # chore_id whose recur form is open
        self._build()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build(self) -> None:
        header = tk.Label(
            self,
            text="✓ Done",
            bg="#1E1E2E",
            fg="#FFFFFF",
            font=("Helvetica", 13, "bold"),
            anchor=tk.W,
        )
        header.pack(fill=tk.X, padx=12, pady=(10, 4))

        tk.Frame(self, bg="#3A3A5E", height=1).pack(fill=tk.X, padx=12)

        outer = tk.Frame(self, bg="#1E1E2E")
        outer.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        scrollbar = tk.Scrollbar(outer, orient=tk.VERTICAL, bg="#2A2A3E")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._canvas = tk.Canvas(
            outer,
            bg="#1E1E2E",
            highlightthickness=0,
            yscrollcommand=scrollbar.set,
        )
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self._canvas.yview)

        self._inner = tk.Frame(self._canvas, bg="#1E1E2E")
        self._window = self._canvas.create_window((0, 0), window=self._inner, anchor=tk.NW)

        self._inner.bind("<Configure>", self._on_inner_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind("<MouseWheel>", self._on_mousewheel)
        self._canvas.bind("<Button-4>", self._on_mousewheel)
        self._canvas.bind("<Button-5>", self._on_mousewheel)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def refresh(self, chores: List[Chore]) -> None:
        for widget in self._inner.winfo_children():
            widget.destroy()

        done = sorted(
            [c for c in chores if c.status == "done"],
            key=lambda c: c.last_done or "",
            reverse=True,
        )

        if not done:
            tk.Label(
                self._inner,
                text="Nothing done yet.",
                bg="#1E1E2E",
                fg="#888899",
                font=("Helvetica", 12),
            ).pack(pady=20)
            return

        for chore in done:
            self._add_row(chore)

    # ------------------------------------------------------------------
    # Row builder
    # ------------------------------------------------------------------

    def _add_row(self, chore: Chore) -> None:
        card = tk.Frame(self._inner, bg="#2A2A3E", pady=2)
        card.pack(fill=tk.X, padx=4, pady=3)

        # Top line: checkbox + name (strikethrough via overstrike font) + buttons
        top = tk.Frame(card, bg="#2A2A3E")
        top.pack(fill=tk.X)

        tk.Label(
            top,
            text="☑",
            bg="#2A2A3E",
            fg="#2ECC71",
            font=("Helvetica", 13),
        ).pack(side=tk.LEFT, padx=(8, 4), pady=(6, 2))

        name_label = tk.Label(
            top,
            text=f"{chore.name}  (×{chore.completions})",
            bg="#2A2A3E",
            fg="#888899",
            font=("Helvetica", 12, "overstrike"),
            anchor=tk.W,
        )
        name_label.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=(6, 2))

        # Redo button
        tk.Button(
            top,
            text="Redo →",
            command=lambda cid=chore.id: self.on_redo(cid),
            bg="#E67E22",
            fg="#FFFFFF",
            font=("Helvetica", 9, "bold"),
            relief=tk.FLAT,
            padx=8,
            pady=2,
            cursor="hand2",
        ).pack(side=tk.RIGHT, padx=(4, 8), pady=(6, 2))

        # Recur button
        tk.Button(
            top,
            text="Recur ↻",
            command=lambda cid=chore.id, c=card: self._toggle_recur_form(cid, c),
            bg="#9B59B6",
            fg="#FFFFFF",
            font=("Helvetica", 9, "bold"),
            relief=tk.FLAT,
            padx=8,
            pady=2,
            cursor="hand2",
        ).pack(side=tk.RIGHT, padx=4, pady=(6, 2))

        # Due label
        tk.Label(
            card,
            text=chore.due_label(),
            bg="#2A2A3E",
            fg="#AAAACC",
            font=("Helvetica", 10),
            anchor=tk.W,
        ).pack(fill=tk.X, padx=(34, 8), pady=(0, 6))

        # Inline recur form (hidden until Recur button clicked)
        recur_frame = tk.Frame(card, bg="#1E1E2E")
        recur_frame._chore_id = chore.id  # type: ignore[attr-defined]
        self._build_recur_form(recur_frame, chore, card)

        # Re-expand if this chore's form was open before refresh
        if self._expanded == chore.id:
            recur_frame.pack(fill=tk.X, padx=8, pady=(0, 8))

    def _build_recur_form(self, frame: tk.Frame, chore: Chore, card: tk.Frame) -> None:
        preset_var = tk.StringVar(value=PRESET_LABELS[2])
        custom_var = tk.StringVar()

        row = tk.Frame(frame, bg="#1E1E2E")
        row.pack(fill=tk.X, pady=4)

        tk.Label(row, text="Every:", bg="#1E1E2E", fg="#AAAACC",
                 font=("Helvetica", 11)).pack(side=tk.LEFT, padx=(4, 4))

        combo = ttk.Combobox(
            row,
            textvariable=preset_var,
            values=PRESET_LABELS + [CUSTOM_LABEL],
            state="readonly",
            width=13,
            font=("Helvetica", 11),
        )
        combo.pack(side=tk.LEFT)

        # Custom sub-frame — hidden until "Custom…" is selected
        custom_frame = tk.Frame(row, bg="#1E1E2E")

        custom_entry = tk.Entry(
            custom_frame,
            textvariable=custom_var,
            width=4,
            font=("Helvetica", 11),
            bg="#2A2A3E",
            fg="#FFFFFF",
            insertbackground="#FFFFFF",
            relief=tk.FLAT,
        )
        custom_entry.pack(side=tk.LEFT, padx=(6, 2), ipady=3)

        tk.Label(custom_frame, text="days", bg="#1E1E2E", fg="#AAAACC",
                 font=("Helvetica", 11)).pack(side=tk.LEFT)

        def on_preset_change(_e=None):
            is_custom = preset_var.get() == CUSTOM_LABEL
            if is_custom:
                custom_frame.pack(side=tk.LEFT)
            else:
                custom_frame.pack_forget()
                custom_var.set("")

        combo.bind("<<ComboboxSelected>>", on_preset_change)

        def save():
            interval = _resolve_interval(preset_var.get(), custom_var.get())
            if interval is None:
                return
            self._expanded = None
            frame.pack_forget()
            self.on_set_recur(chore.id, interval)

        def cancel():
            self._expanded = None
            frame.pack_forget()

        tk.Button(row, text="Save", command=save,
                  bg="#2ECC71", fg="#FFFFFF", font=("Helvetica", 10, "bold"),
                  relief=tk.FLAT, padx=8, pady=2, cursor="hand2").pack(side=tk.LEFT, padx=(10, 4))

        tk.Button(row, text="Cancel", command=cancel,
                  bg="#555577", fg="#FFFFFF", font=("Helvetica", 10),
                  relief=tk.FLAT, padx=8, pady=2, cursor="hand2").pack(side=tk.LEFT)

    def _toggle_recur_form(self, chore_id: str, card: tk.Frame) -> None:
        if self._expanded == chore_id:
            # Collapse
            self._expanded = None
            for child in card.winfo_children():
                if isinstance(child, tk.Frame) and hasattr(child, "_chore_id"):
                    child.pack_forget()
        else:
            # Collapse any other open form first, then expand this one
            self._expanded = chore_id
            for child in card.winfo_children():
                if isinstance(child, tk.Frame) and hasattr(child, "_chore_id"):
                    if child._chore_id == chore_id:  # type: ignore[attr-defined]
                        child.pack(fill=tk.X, padx=8, pady=(0, 8))
        self._on_inner_configure()

    # ------------------------------------------------------------------
    # Scroll helpers
    # ------------------------------------------------------------------

    def _on_inner_configure(self, _event=None) -> None:
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event) -> None:
        self._canvas.itemconfig(self._window, width=event.width)

    def _on_mousewheel(self, event) -> None:
        if event.num == 4:
            self._canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self._canvas.yview_scroll(1, "units")
        else:
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


# ------------------------------------------------------------------
# Standalone helper (no class state needed)
# ------------------------------------------------------------------

def _resolve_interval(preset: str, custom_raw: str) -> Optional[int]:
    if preset == CUSTOM_LABEL:
        try:
            val = int(custom_raw.strip())
            return val if val > 0 else None
        except ValueError:
            return None
    for label, days in PRESETS:
        if label == preset:
            return days
    return None
