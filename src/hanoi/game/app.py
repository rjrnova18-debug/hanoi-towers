"""The app: opens the window, owns what screens share, and runs the main loop.

Every frame: read input -> update -> draw -> repeat. The current screen does the real work.
"""

import asyncio

import pygame

from hanoi import config
from hanoi.game.screens.base import Screen
from hanoi.game.screens.menu import MenuScreen
from hanoi.game.screens.play import PlayScreen
from hanoi.game.widgets import load_fonts
from hanoi.storage import FileBackend, SaveData


class App:
    def __init__(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode(
            (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SCALED | pygame.RESIZABLE
        )
        pygame.display.set_caption(config.WINDOW_TITLE)
        self.fonts = load_fonts()
        self.save = SaveData(FileBackend())
        self.screen: Screen = MenuScreen(self)

    # --- Switching screens (the screens call these) -----------------------------------

    def show_menu(self) -> None:
        self.screen = MenuScreen(self)

    def start_game(self, disk_count: int) -> None:
        self.screen = PlayScreen(self, disk_count)

    # --- Main loop ---------------------------------------------------------------------

    async def run(self) -> None:
        clock = pygame.time.Clock()
        running = True
        while running:
            dt = clock.tick(config.FPS) / 1000  # seconds since the last frame

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.screen.handle_event(event)

            self.screen.update(dt)
            self.screen.draw(self.surface)
            pygame.display.flip()

            # In the browser the game shares a single thread with the page.
            # Yielding here once per frame lets the page breathe instead of freezing.
            await asyncio.sleep(0)

        pygame.quit()


async def run() -> None:
    await App().run()
