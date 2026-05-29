from __future__ import annotations

import tkinter as tk
from typing import Callable, List

from chores.model import Chore


class UndoneList(tk.Frame):
    """
    Scrollable list of undone chores with a clickable checkbox on each row.
    Calls on_done(chore_id) when the user ticks the checkbox.
    """

    def __init__(self, parent: tk.Widget, on_done: Callable[[str], None], **kwargs):
        super().__init__(parent, bg="#1E1E2E", **kwargs)
        self.on_done = on_done
        self._build()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build(self) -> None:
        header = tk.Label(
            self,
            text="📋 To Do",
            bg="#1E1E2E",
            fg="#FFFFFF",
            font=("Helvetica", 13, "bold"),
            anchor=tk.W,
        )
        header.pack(fill=tk.X, padx=12, pady=(10, 4))

        separator = tk.Frame(self, bg="#3A3A5E", height=1)
        separator.pack(fill=tk.X, padx=12)

        # Scrollable container
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

        undone = [c for c in chores if c.status == "undone"]

        if not undone:
            tk.Label(
                self._inner,
                text="All done! 🎉",
                bg="#1E1E2E",
                fg="#888899",
                font=("Helvetica", 12),
            ).pack(pady=20)
            return

        for chore in undone:
            self._add_row(chore)

    # ------------------------------------------------------------------
    # Row builder
    # ------------------------------------------------------------------

    def _add_row(self, chore: Chore) -> None:
        row = tk.Frame(self._inner, bg="#2A2A3E", pady=2)
        row.pack(fill=tk.X, padx=4, pady=3)

        chk_var = tk.BooleanVar(value=False)
        chk = tk.Checkbutton(
            row,
            variable=chk_var,
            command=lambda cid=chore.id: self.on_done(cid),
            bg="#2A2A3E",
            activebackground="#2A2A3E",
            selectcolor="#2A2A3E",
            cursor="hand2",
        )
        chk.pack(side=tk.LEFT, padx=(8, 4), pady=6)

        tk.Label(
            row,
            text=chore.name,
            bg="#2A2A3E",
            fg="#FFFFFF",
            font=("Helvetica", 12),
            anchor=tk.W,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, pady=6)

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
