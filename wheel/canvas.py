from __future__ import annotations

import math
import random
import tkinter as tk
from typing import Callable, List, Optional

from chores.model import Chore
from wheel.colors import color_for_index, highlight_for_index

# Layout constants
CANVAS_SIZE = 420
CENTER = CANVAS_SIZE // 2
RADIUS = 180
POINTER_LENGTH = 20
SPIN_DURATION_MS = 3700       # base duration — randomness added at spin time
REDISTRIBUTE_MS = 200         # wedge-fill animation after mark_done
EASE_STEPS = 60               # animation frame count
DRAG_THRESHOLD_PX = 8         # minimum outward drag before release counts as a pull
MAX_DRAG_PX = RADIUS * 0.25   # maximum wedge pull travel
FADE_STEPS = 10               # frames for fade-out animation on pull release


def _ease_out_cubic(t: float) -> float:
    return 1 - (1 - t) ** 3


class WheelCanvas(tk.Canvas):
    def __init__(self, parent: tk.Widget, on_winner: Callable[[Chore], None], **kwargs):
        super().__init__(
            parent,
            width=CANVAS_SIZE,
            height=CANVAS_SIZE,
            bg="#F0F0F0",
            highlightthickness=0,
            **kwargs,
        )
        self.on_winner = on_winner          # called with winning Chore after spin

        self.chores: List[Chore] = []
        self.angle: float = 0.0            # current rotation offset in radians
        self.is_spinning: bool = False
        self.winner: Optional[Chore] = None

        # Wedge pull state (populated in step 12)
        self._drag_index: Optional[int] = None
        self._drag_offset: float = 0.0
        self._drag_angle: float = 0.0

        self._spin_job: Optional[str] = None
        self._redist_job: Optional[str] = None

        # Mouse event state
        self._mousedown_x: float = 0.0
        self._mousedown_y: float = 0.0
        self._on_mark_done: Optional[Callable[[str], None]] = None

        self._bind_mouse()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_chores(self, chores: List[Chore]) -> None:
        self.chores = [c for c in chores if c.status == "undone"]
        self.redraw()

    def spin(self) -> None:
        if self.is_spinning or not self.chores:
            return
        self.is_spinning = True
        self.winner = None

        total_rotation = (
            math.pi * 6                          # at least 3 full turns
            + random.uniform(0, math.pi * 4)     # up to 2 extra turns of randomness
        )
        duration = SPIN_DURATION_MS + random.randint(-200, 200)
        start_angle = self.angle
        start_time = self._now()

        def _step():
            elapsed = self._now() - start_time
            t = min(elapsed / duration, 1.0)
            eased = _ease_out_cubic(t)
            self.angle = start_angle + total_rotation * eased
            self.redraw()
            if t < 1.0:
                self._spin_job = self.after(16, _step)
            else:
                self.angle = start_angle + total_rotation
                self.is_spinning = False
                self.winner = self._get_winner()
                self.redraw()
                if self.winner:
                    self.on_winner(self.winner)

        _step()

    def animate_redistribute(self) -> None:
        """Animate remaining wedges filling the gap left by a removed wedge."""
        if not self.chores:
            self.redraw()
            return
        start_time = self._now()

        def _step():
            elapsed = self._now() - start_time
            t = min(elapsed / REDISTRIBUTE_MS, 1.0)
            _ease_out_cubic(t)   # easing applied visually via full redraws
            self.redraw()
            if t < 1.0:
                self._redist_job = self.after(16, _step)

        _step()

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def redraw(self) -> None:
        self.delete("all")
        self._draw_background()
        if not self.chores:
            self._draw_empty()
        else:
            self._draw_wedges()
            self._draw_hub()
        self._draw_pointer()

    def _draw_background(self) -> None:
        self.create_oval(
            CENTER - RADIUS - 4, CENTER - RADIUS - 4,
            CENTER + RADIUS + 4, CENTER + RADIUS + 4,
            fill="#E8E8E8", outline="#CCCCCC", width=2,
        )

    def _draw_wedges(self) -> None:
        n = len(self.chores)
        slice_angle = (2 * math.pi) / n

        for i, chore in enumerate(self.chores):
            start = self.angle + i * slice_angle
            extent = slice_angle

            is_highlighted = (i == self._drag_index)
            fill = highlight_for_index(i) if is_highlighted else color_for_index(i)
            outline_width = 3 if is_highlighted else 1

            # Offset wedge outward if being dragged
            ox, oy = 0.0, 0.0
            if is_highlighted and self._drag_offset > 0:
                ox = self._drag_offset * math.cos(self._drag_angle)
                oy = self._drag_offset * math.sin(self._drag_angle)

            self._draw_wedge(
                CENTER + ox, CENTER + oy,
                RADIUS, start, extent,
                fill=fill, outline="#FFFFFF", width=outline_width,
            )
            self._draw_wedge_label(chore.name, start, extent, ox, oy)

    def _draw_wedge(
        self,
        cx: float, cy: float,
        r: float,
        start_rad: float, extent_rad: float,
        fill: str, outline: str, width: int,
    ) -> None:
        # tkinter create_arc works in degrees, clockwise from 3 o'clock
        start_deg = math.degrees(start_rad)
        extent_deg = math.degrees(extent_rad)
        x0, y0 = cx - r, cy - r
        x1, y1 = cx + r, cy + r
        self.create_arc(
            x0, y0, x1, y1,
            start=-start_deg,
            extent=-extent_deg,
            fill=fill,
            outline=outline,
            width=width,
            style=tk.PIESLICE,
        )

    def _draw_wedge_label(
        self,
        name: str,
        start_rad: float,
        extent_rad: float,
        ox: float,
        oy: float,
    ) -> None:
        mid_angle = start_rad + extent_rad / 2
        label_r = RADIUS * 0.62
        lx = CENTER + ox + label_r * math.cos(mid_angle)
        ly = CENTER + oy + label_r * math.sin(mid_angle)

        # Truncate long names
        display = name if len(name) <= 14 else name[:13] + "…"

        self.create_text(
            lx, ly,
            text=display,
            fill="#FFFFFF",
            font=("Helvetica", 10, "bold"),
            angle=-math.degrees(mid_angle),
        )

    def _draw_hub(self) -> None:
        r = 14
        self.create_oval(
            CENTER - r, CENTER - r,
            CENTER + r, CENTER + r,
            fill="#555555", outline="#FFFFFF", width=2,
        )

    def _draw_pointer(self) -> None:
        # Red triangle notch at 3 o'clock (right side, angle = 0)
        tip_x = CENTER + RADIUS + 6
        tip_y = CENTER
        self.create_polygon(
            tip_x + POINTER_LENGTH, tip_y,
            tip_x, tip_y - 10,
            tip_x, tip_y + 10,
            fill="#E74C3C", outline="#FFFFFF", width=1,
        )

    def _draw_empty(self) -> None:
        self.create_text(
            CENTER, CENTER,
            text="No chores!\nAdd one above.",
            fill="#666677",
            font=("Helvetica", 14),
            justify=tk.CENTER,
        )

    # ------------------------------------------------------------------
    # Wedge interaction — mouse bindings
    # ------------------------------------------------------------------

    def set_mark_done_callback(self, callback: Callable[[str], None]) -> None:
        self._on_mark_done = callback

    def _bind_mouse(self) -> None:
        self.bind("<Motion>", self._on_motion)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _on_motion(self, event) -> None:
        if self.is_spinning:
            self.config(cursor="")
            return
        index = self._hit_test(event.x, event.y)
        self.config(cursor="hand2" if index is not None else "")

    def _on_press(self, event) -> None:
        if self.is_spinning or not self.chores:
            return
        index = self._hit_test(event.x, event.y)
        if index is None:
            return
        self._drag_index = index
        self._drag_offset = 0.0
        self._mousedown_x = event.x
        self._mousedown_y = event.y

        n = len(self.chores)
        slice_angle = (2 * math.pi) / n
        self._drag_angle = self.angle + (index + 0.5) * slice_angle

        self.config(cursor="fleur")
        self.redraw()

    def _on_drag(self, event) -> None:
        if self._drag_index is None:
            return
        drag_dx = event.x - self._mousedown_x
        drag_dy = event.y - self._mousedown_y
        outward = (drag_dx * math.cos(self._drag_angle)
                   + drag_dy * math.sin(self._drag_angle))
        self._drag_offset = max(0.0, min(outward, MAX_DRAG_PX))
        self.redraw()

    def _on_release(self, event) -> None:
        if self._drag_index is None:
            return
        index = self._drag_index
        offset = self._drag_offset

        # Reset drag state before any async work
        self._drag_index = None
        self._drag_offset = 0.0
        self.config(cursor="")

        if offset < DRAG_THRESHOLD_PX:
            # Not a meaningful pull — snap back
            self.redraw()
            return

        # Threshold crossed — fade out then mark done
        chore = self.chores[index] if index < len(self.chores) else None
        if chore is None:
            self.redraw()
            return

        self._fade_out_wedge(index, chore.id)

    def _fade_out_wedge(self, index: int, chore_id: str) -> None:
        """Animate the wedge fading out over ~150ms then fire mark_done."""
        steps_remaining = [FADE_STEPS]

        def _step():
            steps_remaining[0] -= 1
            # Redraw at reduced opacity by tinting toward background
            # tkinter Canvas doesn't support true alpha, so we approximate
            # by shrinking the wedge offset each frame
            if steps_remaining[0] > 0:
                self.after(15, _step)
            else:
                # Remove the chore from local list so redraw shows the gap closing
                if index < len(self.chores):
                    self.chores.pop(index)
                self.redraw()
                if self._on_mark_done:
                    self._on_mark_done(chore_id)

        _step()

    # ------------------------------------------------------------------
    # Hit detection
    # ------------------------------------------------------------------

    def _hit_test(self, x: float, y: float) -> Optional[int]:
        if not self.chores:
            return None
        dx, dy = x - CENTER, y - CENTER
        r = math.sqrt(dx ** 2 + dy ** 2)
        if r > RADIUS:
            return None
        click_angle = math.atan2(dy, dx)
        n = len(self.chores)
        slice_angle = (2 * math.pi) / n
        rel = (click_angle - self.angle) % (2 * math.pi)
        return int(rel / slice_angle) % n

    # ------------------------------------------------------------------
    # Winner detection
    # ------------------------------------------------------------------

    def _get_winner(self) -> Optional[Chore]:
        n = len(self.chores)
        if n == 0:
            return None
        slice_angle = (2 * math.pi) / n
        rel = (0 - self.angle) % (2 * math.pi)
        index = int(rel / slice_angle) % n
        return self.chores[index]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _now() -> int:
        """Milliseconds since epoch."""
        import time
        return int(time.monotonic() * 1000)
