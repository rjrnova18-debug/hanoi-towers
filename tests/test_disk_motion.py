"""Tests for the disk in motion (game/disk_motion.py), through its interface only."""

import pygame
import pytest

from hanoi import config
from hanoi.game.board_view import lifted_center
from hanoi.game.disk_motion import DiskMotion

A, C = 0, 2
DISK_1_ON_C = ((3, 2), (), (1,))  # the board right after moving disk 1 from A to C


def run(motion, seconds):
    """Advance time in small frames; return every disk that landed meanwhile."""
    landed = []
    for _ in range(round(seconds * 120)):
        disk = motion.update(1 / 120)
        if disk is not None:
            landed.append(disk)
    return landed


def test_nothing_moves_at_first():
    motion = DiskMotion(3)

    assert motion.disk is None
    assert not motion.is_flying
    assert motion.update(1 / 60) is None


def test_a_flight_lands_once_and_says_which_disk():
    motion = DiskMotion(3)

    motion.fly(1, lifted_center(A), DISK_1_ON_C)

    assert motion.is_flying
    assert motion.disk == 1  # the board hides it while it flies
    assert run(motion, seconds=2) == [1]
    assert not motion.is_flying


def test_a_landed_disk_hops_then_rests():
    motion = DiskMotion(3)
    motion.fly(1, lifted_center(A), DISK_1_ON_C)

    while motion.update(1 / 120) is None:  # until it lands
        pass

    assert motion.disk == 1  # still hidden from the board: it is bouncing
    assert not motion.is_flying  # input may continue during the hop
    run(motion, seconds=config.BOUNCE_DURATION + 0.05)
    assert motion.disk is None


def test_without_bounce_the_disk_rests_at_once():
    motion = DiskMotion(3)
    motion.fly(1, lifted_center(A), DISK_1_ON_C, bounce=False)

    run(motion, seconds=2)

    assert motion.disk is None


def test_a_shake_ends_without_landing_anything():
    motion = DiskMotion(3)

    motion.shake(2)

    assert motion.disk == 2
    assert not motion.is_flying
    assert run(motion, seconds=config.SHAKE_DURATION + 0.05) == []
    assert motion.disk is None


def test_a_new_motion_replaces_the_old_one():
    motion = DiskMotion(3)
    motion.shake(2)

    motion.fly(1, lifted_center(A), DISK_1_ON_C)

    assert motion.disk == 1
    assert run(motion, seconds=2) == [1]


@pytest.mark.parametrize("start", ["nothing", "flying", "shaking", "bouncing"])
def test_every_motion_can_be_drawn(start):
    pygame.init()
    surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    motion = DiskMotion(3)
    if start in ("flying", "bouncing"):
        motion.fly(1, lifted_center(A), DISK_1_ON_C)
    if start == "bouncing":
        while motion.update(1 / 120) is None:
            pass
    if start == "shaking":
        motion.shake(1)

    motion.draw(surface, DISK_1_ON_C)  # must not raise
