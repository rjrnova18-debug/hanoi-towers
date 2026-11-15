"""Reusable pieces of the interface: fonts, text, buttons and stars.

Every screen uses them, so they live here instead of being copied into each screen.
"""

import math
from dataclasses import dataclass

import pygame

from hanoi import config

Point = tuple[float, float]


@dataclass(frozen=True)
class Fonts:
    """The four text sizes used by the game."""

    title: pygame.font.Font
    large: pygame.font.Font
    normal: pygame.font.Font
    small: pygame.font.Font


def load_fonts() -> Fonts:
    """pygame's built-in font: no font files to ship, works the same on PC and browser."""
    return Fonts(
        title=pygame.font.Font(None, 76),
        large=pygame.font.Font(None, 46),
        normal=pygame.font.Font(None, 32),
        small=pygame.font.Font(None, 24),
    )


def draw_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    center: Point,
    color: tuple[int, int, int] = config.TEXT_COLOR,
) -> None:
    image = font.render(text, True, color)
    surface.blit(image, image.get_rect(center=(round(center[0]), round(center[1]))))


class Button:
    """A rounded button that reacts to the mouse (or a finger) and to a keyboard key."""

    def __init__(self, label: str, center: Point, width: int = 170, key: int | None = None) -> None:
        self.label = label
        self.key = key
        self.rect = pygame.Rect(0, 0, width, 44)
        self.rect.center = (round(center[0]), round(center[1]))

    def is_pressed(self, event: pygame.event.Event) -> bool:
        """True if this event clicks the button or presses its key."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.key is not None:
            return event.key == self.key
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        color = config.BUTTON_HOVER_COLOR if hovered else config.BUTTON_COLOR
        pygame.draw.rect(surface, color, self.rect, border_radius=12)
        draw_text(surface, self.label, font, self.rect.center)


def draw_star(surface: pygame.Surface, center: Point, radius: float, filled: bool) -> None:
    """A five-pointed star drawn as a polygon (the default font has no star symbol)."""
    center_x, center_y = center
    points = []
    for corner in range(10):
        # Corners alternate between the outer tip and an inner notch, every 36 degrees.
        distance = radius if corner % 2 == 0 else radius * 0.45
        angle = math.radians(-90 + corner * 36)
        points.append(
            (center_x + distance * math.cos(angle), center_y + distance * math.sin(angle))
        )
    color = config.STAR_ON_COLOR if filled else config.STAR_OFF_COLOR
    pygame.draw.polygon(surface, color, points)
