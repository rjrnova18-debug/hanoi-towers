"""The first screen: the title and one button per disk count, with the best record under each."""

import pygame

from hanoi import config
from hanoi.game.screens.base import AppServices, Screen
from hanoi.game.widgets import Button, draw_background, draw_text, format_time

BUTTON_ROW_Y = 300
BUTTON_SPACING = 130
CENTER_X = config.SCREEN_WIDTH / 2


class MenuScreen(Screen):
    def __init__(self, app: AppServices) -> None:
        super().__init__(app)
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

    def draw(self, surface: pygame.Surface) -> None:
        fonts = self.app.fonts
        draw_background(surface)

        draw_text(surface, config.WINDOW_TITLE, fonts.title, (CENTER_X, 110))
        rules = "Move every disk to the right tower. A disk never sits on a smaller one."
        draw_text(surface, rules, fonts.small, (CENTER_X, 170), config.MUTED_TEXT_COLOR)
        draw_text(surface, "How many disks?", fonts.normal, (CENTER_X, 240))

        for disk_count, button in self.buttons.items():
            button.draw(surface, fonts.large)
            below_button = (button.rect.centerx, button.rect.bottom + 22)
            draw_text(
                surface,
                self._best_text(disk_count),
                fonts.small,
                below_button,
                config.MUTED_TEXT_COLOR,
            )

        controls = (
            "Drag or click the disks  ·  keys 1 2 3  ·  H hint  ·  S solve  ·  U undo  ·  R restart"
        )
        draw_text(surface, controls, fonts.small, (CENTER_X, 480), config.MUTED_TEXT_COLOR)

    def _best_text(self, disk_count: int) -> str:
        record = self.app.save.best_record(disk_count)
        if record is None:
            return "-"
        return f"{record.moves} · {format_time(record.seconds)}"
