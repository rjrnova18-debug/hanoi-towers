"""The disk in motion: the one disk that is out of its stack because it flies, shakes or bounces.

Screens only say what should happen ("fly this disk there", "shake it") and then ask
which disk to hide and draw. This module keeps the animation and knows where the disk is.

The disk the player is holding is not here: that is input, and the play screen keeps it.
"""

import pygame

from hanoi import config
from hanoi.game.animations import Bounce, Flight, Point, Shake
from hanoi.game.board_view import draw_disk, resting_center
from hanoi.logic.rules import Position


class DiskMotion:
    """At most one disk moves at a time: starting a new motion replaces the old one."""

    def __init__(self, disk_count: int) -> None:
        self.disk_count = disk_count
        # A single field, so two animations can never run at once.
        self._animation: Flight | Shake | Bounce | None = None
        self._bounce_on_landing = True

    @property
    def disk(self) -> int | None:
        """The disk that is not resting in its stack right now: the board must skip it."""
        return self._animation.disk if self._animation is not None else None

    @property
    def is_flying(self) -> bool:
        return isinstance(self._animation, Flight)

    def fly(
        self,
        disk: int,
        start: Point,
        position: Position,
        speed: float = config.FLIGHT_SPEED,
        bounce: bool = True,
    ) -> None:
        """Fly `disk` from `start` to where it rests in `position`.

        With `bounce`, it hops a little when it lands.
        """
        end = resting_center(position, disk, self.disk_count)
        self._animation = Flight.between(disk, start, end, speed)
        self._bounce_on_landing = bounce

    def shake(self, disk: int) -> None:
        """Wiggle `disk` in red where it rests: the move was not allowed."""
        self._animation = Shake(disk)

    def update(self, dt: float) -> int | None:
        """Move time forward. Returns the disk that landed during this frame, if any."""
        animation = self._animation
        if animation is None:
            return None
        animation.update(dt)
        if not animation.done:
            return None
        self._animation = None
        if not isinstance(animation, Flight):
            return None  # a shake or a bounce ended: nothing landed
        if self._bounce_on_landing:
            self._animation = Bounce(animation.disk)
        return animation.disk

    def draw(self, surface: pygame.Surface, position: Position) -> None:
        """Draw the moving disk where it is right now (nothing if no disk is moving)."""
        animation = self._animation
        if isinstance(animation, Flight):
            draw_disk(surface, animation.disk, self.disk_count, animation.position())
        elif isinstance(animation, Shake):
            x, y = resting_center(position, animation.disk, self.disk_count)
            center = (x + animation.offset_x(), y)
            draw_disk(surface, animation.disk, self.disk_count, center, config.ERROR_COLOR)
        elif isinstance(animation, Bounce):
            x, y = resting_center(position, animation.disk, self.disk_count)
            draw_disk(surface, animation.disk, self.disk_count, (x, y + animation.offset_y()))
