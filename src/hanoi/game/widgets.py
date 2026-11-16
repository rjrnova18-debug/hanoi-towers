"""Reusable pieces of the interface: colors, background, fonts, text, buttons and stars.

Every screen uses them, so they live here instead of being copied into each screen.
"""

import math
from dataclasses import dataclass
from functools import cache

import pygame

from hanoi import config

Point = tuple[float, float]
Color = tuple[int, int, int]

BLACK: Color = (0, 0, 0)
WHITE: Color = (255, 255, 255)


def blend(color: Color, other: Color, amount: float) -> Color:
    """Mix two colors: amount 0 gives `color`, 1 gives `other`, 0.5 is halfway.

    blend(red, WHITE, 0.4) is a lighter red; blend(red, BLACK, 0.3) a darker one.
    """
    return (
        round(color[0] + (other[0] - color[0]) * amount),
        round(color[1] + (other[1] - color[1]) * amount),
        round(color[2] + (other[2] - color[2]) * amount),
    )


def draw_background(surface: pygame.Surface) -> None:
    """A vertical gradient: night blue at the top, almost black at the bottom."""
    surface.blit(_background_gradient(), (0, 0))


@cache  # the gradient never changes: paint it once, reuse it every frame
def _background_gradient() -> pygame.Surface:
    gradient = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    for y in range(config.SCREEN_HEIGHT):
        color = blend(
            config.BACKGROUND_TOP_COLOR, config.BACKGROUND_BOTTOM_COLOR, y / config.SCREEN_HEIGHT
        )
        pygame.draw.line(gradient, color, (0, y), (config.SCREEN_WIDTH, y))
    return gradient


def draw_dark_overlay(surface: pygame.Surface, alpha: int) -> None:
    """Cover the screen with see-through black (alpha 0-255) to push it into the background."""
    surface.blit(_dark_layer(alpha), (0, 0))


@cache
def _dark_layer(alpha: int) -> pygame.Surface:
    layer = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
    layer.fill((0, 0, 0, alpha))
    return layer


@dataclass(frozen=True)
class Fonts:
    """The four text sizes used by the game."""

    title: pygame.font.Font
    large: pygame.font.Font
    normal: pygame.font.Font
    small: pygame.font.Font


def load_fonts() -> Fonts:
    """Fredoka (SIL Open Font License, see src/assets/fonts/OFL.txt): rounded and friendly."""
    return Fonts(
        title=pygame.font.Font(config.FONT_BOLD, 64),
        large=pygame.font.Font(config.FONT_BOLD, 38),
        normal=pygame.font.Font(config.FONT_REGULAR, 26),
        small=pygame.font.Font(config.FONT_REGULAR, 19),
    )


def draw_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    center: Point,
    color: Color = config.TEXT_COLOR,
) -> None:
    image = font.render(text, True, color)
    surface.blit(image, image.get_rect(center=(round(center[0]), round(center[1]))))


BUTTON_WIDTH = 160
BUTTON_SPACING = 175  # distance between the centers of two buttons in a row


def button_row_centers(count: int, y: float) -> list[Point]:
    """Centers for `count` buttons in a row, centered on the screen."""
    first_x = config.SCREEN_WIDTH / 2 - BUTTON_SPACING * (count - 1) / 2
    return [(first_x + index * BUTTON_SPACING, y) for index in range(count)]


class Button:
    """A rounded button that reacts to the mouse (or a finger) and to a keyboard key."""

    def __init__(
        self, label: str, center: Point, width: int = BUTTON_WIDTH, key: int | None = None
    ) -> None:
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
        """A key seen from the front: a darker side below it, which the top covers
        when the button is held down, so it looks pushed in.
        """
        hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        pressed = hovered and pygame.mouse.get_pressed()[0]
        color = config.BUTTON_HOVER_COLOR if hovered else config.BUTTON_COLOR

        side = self.rect.move(0, config.BUTTON_DEPTH)
        pygame.draw.rect(surface, blend(config.BUTTON_COLOR, BLACK, 0.45), side, border_radius=12)
        top = self.rect.move(0, config.BUTTON_DEPTH if pressed else 0)
        pygame.draw.rect(surface, color, top, border_radius=12)
        draw_text(surface, self.label, font, top.center)


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


def format_time(seconds: float) -> str:
    """75.4 seconds -> "1:15"."""
    minutes, whole_seconds = divmod(int(seconds), 60)
    return f"{minutes}:{whole_seconds:02d}"
