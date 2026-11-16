"""The win screen: stars, moves, time and records, over the solved board."""

import pygame

from hanoi import config
from hanoi.game.board_view import draw_board
from hanoi.game.screens.base import AppServices, Screen
from hanoi.game.widgets import (
    Button,
    button_row_centers,
    draw_background,
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

    def draw(self, surface: pygame.Surface) -> None:
        draw_background(surface)
        draw_board(surface, self.final_position, self.result.disk_count)
        self._dim(surface)
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

    def _dim(self, surface: pygame.Surface) -> None:
        # A see-through black layer (alpha 160 of 255) pushes the board into the background.
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 160))
        surface.blit(shade, (0, 0))

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
            draw_star(surface, (CENTER_X + (index - 1) * 70, y), 28, index < self.result.stars)

    def _record_line(self) -> tuple[str, tuple[int, int, int]]:
        if self.result.assisted:
            return "Hint or Solve was used: no stars or record", config.MUTED_TEXT_COLOR
        if self.is_new_record:
            return "New record!", config.STAR_ON_COLOR
        best = self.app.save.best_record(self.result.disk_count)
        return f"best: {best.moves} moves · {format_time(best.seconds)}", config.MUTED_TEXT_COLOR
