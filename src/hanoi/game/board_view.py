"""Where everything sits on screen, and how the board is drawn.

Two kinds of functions live here:
- Layout functions (pure math): where a tower or a disk is, which tower is under the pointer.
  They are tested without opening a window.
- draw_* functions: the only ones that paint on the screen.
"""

from functools import cache

import pygame

from hanoi import config
from hanoi.game.widgets import BLACK, WHITE, Color, blend
from hanoi.logic.rules import TOWER_NAMES, Move, Position

Point = tuple[float, float]


# --- Layout (pure math) ----------------------------------------------------------------


def tower_center_x(tower: int) -> int:
    """The screen is split into three equal columns; each tower stands in the middle of one."""
    column_width = config.SCREEN_WIDTH // len(TOWER_NAMES)
    return column_width * tower + column_width // 2


def tower_at(point: Point) -> int | None:
    """Which tower's column the point is in, or None if it is outside the board area."""
    x, y = point
    if not (config.BOARD_TOP <= y <= config.BOARD_BOTTOM):
        return None
    if not (0 <= x < config.SCREEN_WIDTH):
        return None
    return int(x // (config.SCREEN_WIDTH // len(TOWER_NAMES)))


def disk_width(disk: int, disk_count: int) -> int:
    """Smallest disk is DISK_MIN_WIDTH, largest is DISK_MAX_WIDTH, evenly spaced between."""
    if disk_count == 1:
        return config.DISK_MAX_WIDTH
    step = (config.DISK_MAX_WIDTH - config.DISK_MIN_WIDTH) / (disk_count - 1)
    return round(config.DISK_MIN_WIDTH + (disk - 1) * step)


def disk_color(disk: int, disk_count: int) -> Color:
    """Spread the rainbow over the disks in play, so 3 disks still get very different colors."""
    last = len(config.DISK_COLORS) - 1
    if disk_count == 1:
        return config.DISK_COLORS[0]
    index = round((disk - 1) * last / (disk_count - 1))
    return config.DISK_COLORS[index]


def disk_rect(disk: int, level: int, tower: int, disk_count: int) -> pygame.Rect:
    """The rectangle of a disk resting on a tower. Level 0 is the bottom of the stack."""
    rect = pygame.Rect(0, 0, disk_width(disk, disk_count), config.DISK_HEIGHT)
    rect.centerx = tower_center_x(tower)
    rect.bottom = config.BASE_Y - level * config.DISK_HEIGHT
    return rect


def resting_center(position: Position, disk: int, disk_count: int) -> Point:
    """The center of a disk where it sits right now on the board."""
    for tower, stack in enumerate(position):
        if disk in stack:
            return disk_rect(disk, stack.index(disk), tower, disk_count).center
    raise ValueError(f"disk {disk} is not on the board")


def lifted_center(tower: int) -> Point:
    """Where a picked-up disk floats, above its tower."""
    return (tower_center_x(tower), config.LIFT_Y)


def peg_rect(tower: int) -> pygame.Rect:
    rect = pygame.Rect(0, 0, config.PEG_WIDTH, config.PEG_HEIGHT)
    rect.centerx = tower_center_x(tower)
    rect.bottom = config.BASE_Y
    return rect


# --- Drawing ---------------------------------------------------------------------------


def draw_board(
    surface: pygame.Surface,
    position: Position,
    disk_count: int,
    hidden_disk: int | None = None,
    label_font: pygame.font.Font | None = None,
) -> None:
    """Draw the base, the three pegs and every resting disk.

    `hidden_disk` is skipped: it is the disk the player is holding or that is flying,
    and the screen draws it separately at its moving position.
    """
    for tower, stack in enumerate(position):
        if stack and stack[0] != hidden_disk:
            _draw_reflection(surface, stack[0], tower, disk_count)
    _draw_base(surface)

    for tower, stack in enumerate(position):
        _draw_peg(surface, tower)
        if label_font is not None:
            _draw_tower_label(surface, tower, label_font)
        for level, disk in enumerate(stack):
            if disk != hidden_disk:
                center = disk_rect(disk, level, tower, disk_count).center
                draw_disk(surface, disk, disk_count, center)


def draw_disk(
    surface: pygame.Surface,
    disk: int,
    disk_count: int,
    center: Point,
    color: Color | None = None,
) -> None:
    """Draw one disk centered on `center` (pass `color` to override, e.g. red).

    Four layers, back to front: a soft shadow, a darker edge at the bottom,
    the body, and a light shine on top. Together they make a flat shape look round.
    """
    color = color or disk_color(disk, disk_count)
    rect = pygame.Rect(0, 0, disk_width(disk, disk_count), config.DISK_HEIGHT - config.DISK_GAP)
    rect.center = (round(center[0]), round(center[1]))
    radius = rect.height // 2

    surface.blit(_shadow(rect.size), (rect.x, rect.y + config.SHADOW_OFFSET))
    pygame.draw.rect(surface, blend(color, BLACK, 0.3), rect, border_radius=radius)
    body = pygame.Rect(rect.x, rect.y, rect.width, rect.height - config.DISK_EDGE)
    pygame.draw.rect(surface, color, body, border_radius=radius)
    shine = pygame.Rect(rect.x + 10, rect.y + 4, rect.width - 20, rect.height // 4)
    pygame.draw.rect(surface, blend(color, WHITE, 0.45), shine, border_radius=shine.height // 2)


def _draw_base(surface: pygame.Surface) -> None:
    base = pygame.Rect(40, config.BASE_Y, config.SCREEN_WIDTH - 80, config.BASE_HEIGHT)
    pygame.draw.rect(surface, config.PEG_COLOR, base, border_radius=config.BASE_HEIGHT // 2)
    top_light = pygame.Rect(base.x + 6, base.y + 2, base.width - 12, 2)
    pygame.draw.rect(surface, blend(config.PEG_COLOR, WHITE, 0.25), top_light)


def _draw_peg(surface: pygame.Surface, tower: int) -> None:
    peg = peg_rect(tower)
    pygame.draw.rect(surface, config.PEG_COLOR, peg, border_radius=config.PEG_WIDTH // 2)
    side_light = pygame.Rect(peg.x + 2, peg.y + 4, 3, peg.height - 8)
    pygame.draw.rect(surface, blend(config.PEG_COLOR, WHITE, 0.25), side_light, border_radius=2)


def _draw_reflection(surface: pygame.Surface, disk: int, tower: int, disk_count: int) -> None:
    """A faint copy of the bottom disk under the base that fades out, like on a glossy floor."""
    width = disk_width(disk, disk_count)
    left = tower_center_x(tower) - width // 2
    top = config.BASE_Y + config.BASE_HEIGHT
    surface.blit(_fading_reflection(width, disk_color(disk, disk_count)), (left, top))


# pygame only blends see-through shapes when they live on their own surface.
# Building those surfaces is slow, so each size is built once and then reused (cached).


@cache
def _shadow(size: tuple[int, int]) -> pygame.Surface:
    return _glow(size, BLACK, config.SHADOW_ALPHA)


@cache
def _fading_reflection(width: int, color: Color) -> pygame.Surface:
    """Rows go from REFLECTION_ALPHA at the top down to fully transparent."""
    height = config.REFLECTION_HEIGHT
    layer = pygame.Surface((width, height), pygame.SRCALPHA)
    for row in range(height):
        alpha = round(config.REFLECTION_ALPHA * (1 - row / height))
        inset = row  # each row a bit narrower: the rounded end of a disk, upside down
        pygame.draw.line(layer, (*color, alpha), (inset, row), (width - 1 - inset, row))
    return layer


@cache
def _glow(size: tuple[int, int], color: Color, alpha: int) -> pygame.Surface:
    """A rounded, see-through rectangle of one color."""
    layer = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(layer, (*color, alpha), layer.get_rect(), border_radius=size[1] // 2)
    return layer


def draw_hint(surface: pygame.Surface, move: Move, position: Position, disk_count: int) -> None:
    """Outline the disk to move and draw an arrow from its tower to the target tower."""
    source_stack = position[move.source]
    disk = source_stack[-1]
    outline = disk_rect(disk, len(source_stack) - 1, move.source, disk_count).inflate(10, 8)
    pygame.draw.rect(surface, config.HINT_COLOR, outline, width=3, border_radius=14)

    y = config.HINT_ARROW_Y
    start_x = tower_center_x(move.source)
    end_x = tower_center_x(move.target)
    direction = 1 if end_x > start_x else -1  # +1 points right, -1 points left
    head_length = 18
    pygame.draw.line(surface, config.HINT_COLOR, (start_x, y), (end_x - direction * 10, y), 5)
    arrow_head = [
        (end_x, y),
        (end_x - direction * head_length, y - 11),
        (end_x - direction * head_length, y + 11),
    ]
    pygame.draw.polygon(surface, config.HINT_COLOR, arrow_head)


def _draw_tower_label(surface: pygame.Surface, tower: int, font: pygame.font.Font) -> None:
    # The label shows the key that selects this tower (1, 2, 3).
    label = font.render(str(tower + 1), True, config.MUTED_TEXT_COLOR)
    position = (tower_center_x(tower), config.BASE_Y + config.BASE_HEIGHT + 22)
    surface.blit(label, label.get_rect(center=position))
