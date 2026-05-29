import pytest
from wheel.colors import assign_colors, assign_highlight_colors, color_for_index, highlight_for_index, PALETTE


def test_empty():
    assert assign_colors(0) == []
    assert assign_highlight_colors(0) == []


def test_length_matches_n():
    for n in range(1, 20):
        assert len(assign_colors(n)) == n


def test_no_adjacent_duplicates():
    for n in range(2, 20):
        colors = assign_colors(n)
        for i in range(len(colors) - 1):
            assert colors[i] != colors[i + 1], f"Adjacent duplicate at index {i} for n={n}"


def test_cycles_palette():
    colors = assign_colors(len(PALETTE) * 2)
    assert colors[:len(PALETTE)] == colors[len(PALETTE):]


def test_color_for_index_wraps():
    assert color_for_index(0) == color_for_index(len(PALETTE))


def test_highlight_for_index_wraps():
    assert highlight_for_index(0) == highlight_for_index(len(PALETTE))


def test_highlight_differs_from_normal():
    for i in range(len(PALETTE)):
        assert color_for_index(i) != highlight_for_index(i)
