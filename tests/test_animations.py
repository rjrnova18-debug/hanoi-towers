"""Tests for the animations (game/animations.py)."""

import pytest

from hanoi import config
from hanoi.game.animations import Bounce, Flight, Shake, ease_in_out, point_along_path


def test_point_along_path_walks_by_distance():
    path = [(0, 0), (0, 10), (30, 10)]  # 10 px up, then 30 px across: 40 px in total

    assert point_along_path(path, 0) == (0, 0)
    assert point_along_path(path, 0.25) == (0, 10)  # 10 of 40 px: the corner
    assert point_along_path(path, 0.5) == (10, 10)
    assert point_along_path(path, 1) == (30, 10)


def test_flight_goes_up_across_and_down():
    flight = Flight.between(disk=1, start=(100, 400), end=(500, 380))

    xs = [x for x, _ in flight.waypoints]
    ys = [y for _, y in flight.waypoints]
    assert xs == [100, 100, 500, 500]
    assert ys == [400, config.LIFT_Y, config.LIFT_Y, 380]


def test_flight_ends_exactly_on_its_target():
    flight = Flight.between(disk=1, start=(100, 400), end=(500, 380))

    for _ in range(1000):  # far more frames than needed
        flight.update(1 / 60)

    assert flight.done
    assert flight.position() == (500, 380)


def test_longer_flights_take_longer():
    short = Flight.between(disk=1, start=(160, 400), end=(480, 400))
    long = Flight.between(disk=1, start=(160, 400), end=(800, 400))

    assert long.duration > short.duration


def test_shake_fades_out_and_finishes():
    shake = Shake(disk=2)
    shake.update(config.SHAKE_DURATION / 8)
    assert shake.offset_x() != 0

    shake.update(config.SHAKE_DURATION)

    assert shake.done
    assert shake.offset_x() == pytest.approx(0)


def test_a_faster_flight_takes_less_time():
    normal = Flight.between(disk=1, start=(160, 400), end=(800, 400))
    twice_as_fast = Flight.between(disk=1, start=(160, 400), end=(800, 400), speed=2 * normal.speed)

    assert twice_as_fast.duration == pytest.approx(normal.duration / 2)


def test_ease_in_out_starts_and_ends_slow():
    assert ease_in_out(0) == 0
    assert ease_in_out(0.5) == 0.5
    assert ease_in_out(1) == 1
    assert ease_in_out(0.1) < 0.1  # slower than constant speed at the start
    assert ease_in_out(0.9) > 0.9  # and gently arriving at the end


def test_bounce_hops_up_then_settles():
    bounce = Bounce(disk=1)
    bounce.update(config.BOUNCE_DURATION / 3)
    assert bounce.offset_y() < 0  # up on screen

    bounce.update(config.BOUNCE_DURATION)

    assert bounce.done
    assert bounce.offset_y() == pytest.approx(0)
