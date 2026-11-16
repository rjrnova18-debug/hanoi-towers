"""Tests for the small pure helpers in game/widgets.py."""

from hanoi import config
from hanoi.game.widgets import BLACK, WHITE, blend, button_row_centers


def test_blend_ends_and_middle():
    red = (200, 40, 40)

    assert blend(red, WHITE, 0) == red
    assert blend(red, WHITE, 1) == WHITE
    assert blend(BLACK, WHITE, 0.5) == (128, 128, 128)


def test_blend_towards_black_makes_a_darker_color():
    red = (200, 40, 40)

    darker = blend(red, BLACK, 0.3)

    assert all(dark < original for dark, original in zip(darker, red, strict=True))


def test_button_row_is_centered_on_the_screen():
    centers = button_row_centers(5, y=500)

    middle_x = centers[2][0]
    assert middle_x == config.SCREEN_WIDTH / 2
    assert all(y == 500 for _, y in centers)


def test_button_row_is_evenly_spaced():
    xs = [x for x, _ in button_row_centers(4, y=0)]

    gaps = {round(b - a, 6) for a, b in zip(xs, xs[1:], strict=False)}
    assert len(gaps) == 1
