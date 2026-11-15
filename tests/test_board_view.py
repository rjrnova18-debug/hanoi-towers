"""Tests for the board layout (game/board_view.py). Pure math: no window is opened."""

import pytest

from hanoi import config
from hanoi.game.board_view import (
    disk_color,
    disk_rect,
    disk_width,
    peg_rect,
    resting_center,
    tower_at,
    tower_center_x,
)
from hanoi.logic.rules import Towers

A, B, C = 0, 1, 2
ALL_DISK_COUNTS = range(config.MIN_DISKS, config.MAX_DISKS + 1)


def test_towers_are_evenly_spaced_and_centered():
    assert [tower_center_x(t) for t in (A, B, C)] == [160, 480, 800]


@pytest.mark.parametrize(("x", "expected_tower"), [(0, A), (319, A), (320, B), (700, C), (959, C)])
def test_tower_at_finds_the_column_under_the_pointer(x, expected_tower):
    assert tower_at((x, 300)) == expected_tower


@pytest.mark.parametrize("point", [(480, 20), (480, 500), (-5, 300), (960, 300)])
def test_tower_at_ignores_points_outside_the_board(point):
    # Above the board is the score bar, below it the buttons.
    assert tower_at(point) is None


@pytest.mark.parametrize("disk_count", ALL_DISK_COUNTS)
def test_disks_grow_from_smallest_to_largest(disk_count):
    widths = [disk_width(disk, disk_count) for disk in range(1, disk_count + 1)]

    assert widths[0] == config.DISK_MIN_WIDTH
    assert widths[-1] == config.DISK_MAX_WIDTH
    assert widths == sorted(set(widths))  # strictly growing


def test_largest_disk_fits_between_two_towers():
    gap_between_towers = tower_center_x(B) - tower_center_x(A)

    assert gap_between_towers > config.DISK_MAX_WIDTH


@pytest.mark.parametrize("disk_count", ALL_DISK_COUNTS)
def test_every_disk_gets_a_different_color(disk_count):
    colors = [disk_color(disk, disk_count) for disk in range(1, disk_count + 1)]

    assert len(set(colors)) == disk_count


def test_full_stack_sits_on_the_base_and_below_the_top_of_the_peg():
    disk_count = config.MAX_DISKS
    bottom_disk = disk_rect(disk_count, 0, A, disk_count)
    top_disk = disk_rect(1, disk_count - 1, A, disk_count)

    assert bottom_disk.bottom == config.BASE_Y
    assert top_disk.top > peg_rect(A).top  # the peg still sticks out above the stack
    assert peg_rect(A).top > config.LIFT_Y  # a lifted disk floats above every peg


def test_stacked_disks_touch_without_overlapping():
    lower = disk_rect(3, 0, A, 3)
    upper = disk_rect(2, 1, A, 3)

    assert upper.bottom == lower.top


def test_resting_center_finds_a_disk_on_the_board():
    position = Towers([[3], [2, 1], []]).position()

    assert resting_center(position, 1, 3) == disk_rect(1, 1, B, 3).center
