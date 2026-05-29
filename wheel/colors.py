from __future__ import annotations

from typing import List

# 6 visually distinct colors — no two adjacent wedges will share a color
# because we assign by (index % len(PALETTE)), guaranteeing alternation
# as long as PALETTE has at least 2 entries (it has 6).
PALETTE: List[str] = [
    "#E74C3C",  # red
    "#3498DB",  # blue
    "#2ECC71",  # green
    "#F39C12",  # orange
    "#9B59B6",  # purple
    "#1ABC9C",  # teal
]

# Brighter versions of each palette color used when a wedge is highlighted
PALETTE_HIGHLIGHT: List[str] = [
    "#FF6B6B",  # red highlight
    "#5DADE2",  # blue highlight
    "#58D68D",  # green highlight
    "#F8C471",  # orange highlight
    "#BB8FCE",  # purple highlight
    "#48C9B0",  # teal highlight
]


def assign_colors(n: int) -> List[str]:
    """Return a list of n colors with no two adjacent colors the same."""
    if n == 0:
        return []
    return [PALETTE[i % len(PALETTE)] for i in range(n)]


def assign_highlight_colors(n: int) -> List[str]:
    """Return highlight colors matching assign_colors order."""
    if n == 0:
        return []
    return [PALETTE_HIGHLIGHT[i % len(PALETTE_HIGHLIGHT)] for i in range(n)]


def color_for_index(index: int) -> str:
    return PALETTE[index % len(PALETTE)]


def highlight_for_index(index: int) -> str:
    return PALETTE_HIGHLIGHT[index % len(PALETTE_HIGHLIGHT)]
