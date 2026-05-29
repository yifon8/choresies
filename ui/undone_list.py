from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import Callable, List

from chores.model import Chore


class UndoneList(tk.Frame):
    """
    Scrollable list of undone chores with a clickable checkbox and Remove button on each row.
    Calls on_done(chore_id) when the checkbox is ticked.
    Calls on_remove(chore_id) when Remove is confirmed.
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_done: Callable[[str], None],
        on_remove: Callable[[str], None],
        **kwargs,
    ):
        super().__init__(parent, bg="#F0F0F0", **kwargs)
        self.on_done = on_done
        self.on_remove = on_remove
        self._build()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build(self) -> None:
        header = tk.Label(
            self,
            text="📋 To Do",
            bg="#F0F0F0",
            fg="#222222",
            font=("Helvetica", 13, "bold"),
            anchor=tk.W,
        )
        header.pack(fill=tk.X, padx=12, pady=(10, 4))

        separator = tk.Frame(self, bg="#CCCCCC", height=1)
        separator.pack(fill=tk.X, padx=12)

        # Scrollable container
        outer = tk.Frame(self, bg="#F0F0F0")
        outer.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        scrollbar = tk.Scrollbar(outer, orient=tk.VERTICAL, bg="#CCCCCC")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._canvas = tk.Canvas(
            outer,
            bg="#F0F0F0",
            highlightthickness=0,
            yscrollcommand=scrollbar.set,
        )
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self._canvas.yview)

        self._inner = tk.Frame(self._canvas, bg="#F0F0F0")
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
                bg="#F0F0F0",
                fg="#999999",
                font=("Helvetica", 12),
            ).pack(pady=20)
            return

        for chore in undone:
            self._add_row(chore)

    # ------------------------------------------------------------------
    # Row builder
    # ------------------------------------------------------------------

    def _add_row(self, chore: Chore) -> None:
        row = tk.Frame(self._inner, bg="#FFFFFF", pady=2)
        row.pack(fill=tk.X, padx=4, pady=3)

        chk_var = tk.BooleanVar(value=False)
        chk = tk.Checkbutton(
            row,
            variable=chk_var,
            command=lambda cid=chore.id: self.on_done(cid),
            bg="#FFFFFF",
            activebackground="#FFFFFF",
            selectcolor="#FFFFFF",
            cursor="hand2",
        )
        chk.pack(side=tk.LEFT, padx=(8, 4), pady=6)

        tk.Label(
            row,
            text=chore.name,
            bg="#FFFFFF",
            fg="#222222",
            font=("Helvetica", 12),
            anchor=tk.W,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, pady=6)

        tk.Button(
            row,
            text="Remove",
            command=lambda cid=chore.id, name=chore.name: self._confirm_remove(cid, name),
            bg="#FFFFFF",
            fg="#CC4444",
            font=("Helvetica", 9),
            relief=tk.FLAT,
            padx=8,
            pady=2,
            cursor="hand2",
        ).pack(side=tk.RIGHT, padx=8, pady=6)

    def _confirm_remove(self, chore_id: str, name: str) -> None:
        confirmed = messagebox.askyesno(
            title="Remove Chore",
            message="Remove this chore from To Do list and wheel?",
        )
        if confirmed:
            self.on_remove(chore_id)

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
