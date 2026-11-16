"""Small animations: a disk flying, bouncing and shaking; stars popping in; confetti.

Each animation only computes WHERE the disk is at a given moment.
The screen calls update(dt) every frame and draws the disk at position().
"""

import math
import random
from dataclasses import dataclass, field
from itertools import pairwise

from hanoi import config
from hanoi.game.widgets import Color

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
        progress = self.elapsed / self.duration
        return point_along_path(self.waypoints, ease_in_out(progress))


@dataclass
class Bounce:
    """A disk that just landed hops up a little and settles, like a real object."""

    disk: int
    elapsed: float = 0.0

    def update(self, dt: float) -> None:
        self.elapsed = min(self.elapsed + dt, config.BOUNCE_DURATION)

    @property
    def done(self) -> bool:
        return self.elapsed >= config.BOUNCE_DURATION

    def offset_y(self) -> float:
        """Vertical offset in pixels: one hop up (negative y is up on screen), then rest."""
        progress = self.elapsed / config.BOUNCE_DURATION
        return -config.BOUNCE_HEIGHT * math.sin(progress * math.pi) * (1 - progress)


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


def pop_scale(elapsed: float, start: float) -> float:
    """Size of something that pops in at time `start`: 0 before, then grows a bit past its
    full size and settles back to 1, like a balloon inflating.
    """
    progress = (elapsed - start) / config.STAR_POP_DURATION
    if progress <= 0:
        return 0.0
    if progress >= 1:
        return 1.0
    peak = config.STAR_POP_OVERSHOOT
    if progress < 0.6:
        return peak * progress / 0.6  # growing
    return peak - (peak - 1) * (progress - 0.6) / 0.4  # settling back


@dataclass
class ConfettiPiece:
    """One paper square: thrown up, slowed by the air, falling while it flips."""

    x: float
    y: float
    speed_x: float
    speed_y: float
    color: Color
    size: float
    angle: float  # how far it has flipped; only used to draw it thinner or wider
    spin: float

    def update(self, dt: float) -> None:
        self.speed_x -= self.speed_x * config.CONFETTI_AIR_DRAG * dt
        self.speed_y = min(self.speed_y + config.CONFETTI_GRAVITY * dt, config.CONFETTI_MAX_FALL)
        self.x += self.speed_x * dt
        self.y += self.speed_y * dt
        self.angle += self.spin * dt


def confetti_burst(rng: random.Random, colors: list[Color]) -> list[ConfettiPiece]:
    """Two cannons, one in each bottom corner, shooting up and towards the middle.

    `rng` is passed in so tests can use a fixed seed and always get the same confetti.
    """
    pieces = []
    for index in range(config.CONFETTI_COUNT):
        from_left = index % 2 == 0
        towards_middle = 1 if from_left else -1
        pieces.append(
            ConfettiPiece(
                x=0 if from_left else config.SCREEN_WIDTH,
                y=config.SCREEN_HEIGHT,
                speed_x=towards_middle * rng.uniform(250, 950),  # air drag stops it ~v/1.5 px later
                speed_y=rng.uniform(-1000, -450),  # negative = up
                color=rng.choice(colors),
                size=rng.uniform(6, 11),
                angle=rng.uniform(0, math.tau),
                spin=rng.uniform(-12, 12),
            )
        )
    return pieces


def ease_in_out(progress: float) -> float:
    """Start slow, speed up, end slow ("smoothstep"). 0 -> 0, 0.5 -> 0.5, 1 -> 1.

    Real objects don't jump to full speed and stop dead; easing makes motion feel natural.
    """
    return progress * progress * (3 - 2 * progress)


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
