"""The win screen: stars, moves, time and records, over the solved board.

Earned stars pop in one by one, and an unassisted win throws confetti.
"""

import math
import random

import pygame

from hanoi import config
from hanoi.game.animations import ConfettiPiece, confetti_burst, pop_scale
from hanoi.game.board_view import draw_board
from hanoi.game.screens.base import AppServices, Screen
from hanoi.game.widgets import (
    Button,
    button_row_centers,
    draw_background,
    draw_dark_overlay,
    draw_star,
    draw_text,
    format_time,
)
from hanoi.logic.rules import Position, minimum_moves
from hanoi.logic.session import GameResult

CENTER_X = config.SCREEN_WIDTH / 2
PANEL = pygame.Rect(0, 0, 540, 360)
PANEL.center = (round(CENTER_X), config.SCREEN_HEIGHT // 2)
BUTTON_ROW_Y = PANEL.bottom - 45


class WinScreen(Screen):
    def __init__(
        self, app: AppServices, result: GameResult, final_position: Position, is_new_record: bool
    ) -> None:
        super().__init__(app)
        self.result = result
        self.final_position = final_position
        self.is_new_record = is_new_record
        self.has_next_level = result.disk_count < config.MAX_DISKS
        self.buttons = self._make_buttons()
        self.elapsed = 0.0  # seconds since the screen appeared: drives the star animation
        # Confetti celebrates a win earned without help.
        self.confetti: list[ConfettiPiece] = (
            [] if result.assisted else confetti_burst(random.Random(), config.DISK_COLORS)
        )

    def _make_buttons(self) -> dict[str, Button]:
        # (name, label, key). "next" only exists below the maximum number of disks.
        choices = [("again", "Again (Enter)", pygame.K_RETURN)]
        if self.has_next_level:
            choices.append(("next", f"{self.result.disk_count + 1} disks (N)", pygame.K_n))
        choices.append(("menu", "Menu (Esc)", pygame.K_ESCAPE))

        centers = button_row_centers(len(choices), BUTTON_ROW_Y)
        buttons = {}
        for (name, label, key), center in zip(choices, centers, strict=True):
            buttons[name] = Button(label, center, key=key)
        return buttons

    def handle_event(self, event: pygame.event.Event) -> None:
        disk_count = self.result.disk_count
        if self.buttons["again"].is_pressed(event):
            self.app.start_game(disk_count)
        elif "next" in self.buttons and self.buttons["next"].is_pressed(event):
            self.app.start_game(disk_count + 1)
        elif self.buttons["menu"].is_pressed(event):
            self.app.show_menu()

    def update(self, dt: float) -> None:
        self.elapsed += dt
        for piece in self.confetti:
            piece.update(dt)
        # Forget the pieces that already fell below the screen.
        self.confetti = [piece for piece in self.confetti if piece.y < config.SCREEN_HEIGHT + 20]

    def draw(self, surface: pygame.Surface) -> None:
        draw_background(surface)
        draw_board(surface, self.final_position, self.result.disk_count)
        draw_dark_overlay(surface, config.WIN_OVERLAY_ALPHA)
        pygame.draw.rect(surface, config.PANEL_COLOR, PANEL, border_radius=20)

        fonts = self.app.fonts
        draw_text(surface, "Solved!", fonts.title, (CENTER_X, PANEL.top + 50))
        self._draw_stars_or_assisted(surface)
        minimum = minimum_moves(self.result.disk_count)
        moves = f"{self.result.moves} moves  ·  minimum {minimum}"
        draw_text(surface, moves, fonts.normal, (CENTER_X, PANEL.top + 175))
        time = f"time {format_time(self.result.seconds)}"
        draw_text(surface, time, fonts.normal, (CENTER_X, PANEL.top + 210))
        text, color = self._record_line()
        draw_text(surface, text, fonts.small, (CENTER_X, PANEL.top + 250), color)

        for button in self.buttons.values():
            button.draw(surface, fonts.small)
        self._draw_confetti(surface)

    def _draw_stars_or_assisted(self, surface: pygame.Surface) -> None:
        y = PANEL.top + 115
        if self.result.assisted:
            draw_text(
                surface,
                "Assisted game",
                self.app.fonts.large,
                (CENTER_X, y),
                config.MUTED_TEXT_COLOR,
            )
            return
        for index in range(3):
            center = (CENTER_X + (index - 1) * 70, y)
            draw_star(surface, center, 28, filled=False)  # the empty slot is always there
            if index < self.result.stars:
                scale = pop_scale(self.elapsed, start=config.STAR_POP_DELAY * (index + 1))
                if scale > 0:
                    draw_star(surface, center, 28 * scale, filled=True)

    def _draw_confetti(self, surface: pygame.Surface) -> None:
        for piece in self.confetti:
            # Width follows the flip angle, so the paper looks like it turns in the air.
            width = max(1, round(piece.size * abs(math.cos(piece.angle))))
            rect = pygame.Rect(0, 0, width, round(piece.size * 0.6))
            rect.center = (round(piece.x), round(piece.y))
            pygame.draw.rect(surface, piece.color, rect)

    def _record_line(self) -> tuple[str, tuple[int, int, int]]:
        if self.result.assisted:
            return "Hint or Solve was used: no stars or record", config.MUTED_TEXT_COLOR
        if self.is_new_record:
            return "New record!", config.STAR_ON_COLOR
        best = self.app.save.best_record(self.result.disk_count)
        return f"best: {best.moves} moves · {format_time(best.seconds)}", config.MUTED_TEXT_COLOR
