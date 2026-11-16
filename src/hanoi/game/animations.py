"""Small animations: a disk flying to its tower and a disk shaking after a mistake.

Each animation only computes WHERE the disk is at a given moment.
The screen calls update(dt) every frame and draws the disk at position().
"""

import math
from dataclasses import dataclass, field
from itertools import pairwise

from hanoi import config

Point = tuple[float, float]


@dataclass
class Flight:
    """A disk moving along a path: up, across, then down onto its tower.

    The speed is constant, so a short hop takes less time than a long trip.
    """

    disk: int
    waypoints: list[Point]
    speed: float = config.FLIGHT_SPEED  # pixels per second
    elapsed: float = 0.0
    duration: float = field(init=False)

    def __post_init__(self) -> None:
        self.duration = max(path_length(self.waypoints) / self.speed, 0.05)

    @classmethod
    def between(
        cls, disk: int, start: Point, end: Point, speed: float = config.FLIGHT_SPEED
    ) -> "Flight":
        """Up from `start` to the lift height, across, and down to `end`."""
        lift_y = min(config.LIFT_Y, start[1], end[1])
        waypoints = [start, (start[0], lift_y), (end[0], lift_y), end]
        return cls(disk, waypoints, speed)

    def update(self, dt: float) -> None:
        self.elapsed = min(self.elapsed + dt, self.duration)

    @property
    def done(self) -> bool:
        return self.elapsed >= self.duration

    def position(self) -> Point:
        return point_along_path(self.waypoints, self.elapsed / self.duration)


@dataclass
class Shake:
    """A disk wiggling left and right, fading out. Used for illegal moves."""

    disk: int
    elapsed: float = 0.0

    def update(self, dt: float) -> None:
        self.elapsed = min(self.elapsed + dt, config.SHAKE_DURATION)

    @property
    def done(self) -> bool:
        return self.elapsed >= config.SHAKE_DURATION

    def offset_x(self) -> float:
        """Horizontal offset in pixels: a sine wave that shrinks to zero."""
        progress = self.elapsed / config.SHAKE_DURATION
        wiggles = 4
        return config.SHAKE_AMPLITUDE * math.sin(progress * wiggles * 2 * math.pi) * (1 - progress)


def path_length(waypoints: list[Point]) -> float:
    return sum(math.dist(a, b) for a, b in pairwise(waypoints))


def point_along_path(waypoints: list[Point], fraction: float) -> Point:
    """The point found after walking `fraction` (0 to 1) of the whole path."""
    remaining = path_length(waypoints) * min(max(fraction, 0.0), 1.0)
    for start, end in pairwise(waypoints):
        segment = math.dist(start, end)
        if remaining <= segment and segment > 0:
            t = remaining / segment
            return (start[0] + (end[0] - start[0]) * t, start[1] + (end[1] - start[1]) * t)
        remaining -= segment
    return waypoints[-1]
