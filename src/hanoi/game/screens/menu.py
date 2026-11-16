"""The first screen: the title and one button per disk count, with the best record under each.

Behind it, a small game solves itself back and forth (DemoBoard), darkened so it never
distracts from the menu.
"""

import pygame

from hanoi import config
from hanoi.game.board_view import draw_board, resting_center
from hanoi.game.disk_motion import DiskMotion
from hanoi.game.screens.base import AppServices, Screen
from hanoi.game.widgets import (
    Button,
    draw_background,
    draw_dark_overlay,
    draw_text,
    format_time,
)
from hanoi.logic.rules import GOAL_TOWER, START_TOWER, Move, Towers
from hanoi.logic.solver import solve_from

BUTTON_ROW_Y = 300
BUTTON_SPACING = 130
CENTER_X = config.SCREEN_WIDTH / 2


class DemoBoard:
    """A tower that moves itself from A to C, rests, and goes back to A, forever."""

    def __init__(self) -> None:
        self.towers = Towers.new_game(config.MENU_DEMO_DISKS)
        self.motion = DiskMotion(config.MENU_DEMO_DISKS)
        self.target = START_TOWER  # flipped to GOAL_TOWER before the first trip
        self.moves_left: list[Move] = []
        self.wait = config.MENU_DEMO_PAUSE

    def update(self, dt: float) -> None:
        self.motion.update(dt)
        if self.motion.is_flying:
            return
        self.wait -= dt
        if self.wait > 0:
            return
        if not self.moves_left:  # the tower is complete: send it to the other side
            self.target = START_TOWER if self.target == GOAL_TOWER else GOAL_TOWER
            self.moves_left = solve_from(self.towers, self.target)
        self._play(self.moves_left.pop(0))
        self.wait = config.MENU_DEMO_PAUSE if self.moves_left else config.MENU_DEMO_REST

    def _play(self, move: Move) -> None:
        disk = self.towers.top_disk(move.source)
        start = resting_center(self.towers.position(), disk, config.MENU_DEMO_DISKS)
        self.towers.move(move)
        self.motion.fly(disk, start, self.towers.position(), config.MENU_DEMO_SPEED)

    def draw(self, surface: pygame.Surface) -> None:
        position = self.towers.position()
        draw_board(surface, position, config.MENU_DEMO_DISKS, hidden_disk=self.motion.disk)
        self.motion.draw(surface, position)


class MenuScreen(Screen):
    def __init__(self, app: AppServices) -> None:
        super().__init__(app)
        self.demo = DemoBoard()
        disk_counts = range(config.MIN_DISKS, config.MAX_DISKS + 1)
        first_x = CENTER_X - BUTTON_SPACING * (len(disk_counts) - 1) / 2
        # Each button also answers to its number key: press 5 to play with 5 disks.
        self.buttons = {
            disk_count: Button(
                str(disk_count),
                (first_x + index * BUTTON_SPACING, BUTTON_ROW_Y),
                width=100,
                key=pygame.K_0 + disk_count,
            )
            for index, disk_count in enumerate(disk_counts)
        }

    def handle_event(self, event: pygame.event.Event) -> None:
        for disk_count, button in self.buttons.items():
            if button.is_pressed(event):
                self.app.start_game(disk_count)
                return

    def update(self, dt: float) -> None:
        self.demo.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        fonts = self.app.fonts
        draw_background(surface)
        self.demo.draw(surface)
        draw_dark_overlay(surface, config.MENU_OVERLAY_ALPHA)

        draw_text(surface, config.WINDOW_TITLE, fonts.title, (CENTER_X, 110))
        rules = "Move every disk to the right tower. A disk never sits on a smaller one."
        draw_text(surface, rules, fonts.small, (CENTER_X, 170), config.MUTED_TEXT_COLOR)
        draw_text(surface, "How many disks?", fonts.normal, (CENTER_X, 240))

        for disk_count, button in self.buttons.items():
            button.draw(surface, fonts.large)
            below_button = (button.rect.centerx, button.rect.bottom + 22)
            best = self._best_text(disk_count)
            draw_text(surface, best, fonts.small, below_button, config.MUTED_TEXT_COLOR)

        controls = (
            "Drag or click the disks  ·  keys 1 2 3  ·  H hint  ·  S solve  ·  U undo  ·  "
            "R restart  ·  M sound"
        )
        draw_text(surface, controls, fonts.small, (CENTER_X, 480), config.MUTED_TEXT_COLOR)

    def _best_text(self, disk_count: int) -> str:
        record = self.app.save.best_record(disk_count)
        if record is None:
            return "-"
        return f"{record.moves} · {format_time(record.seconds)}"
