"""The main loop: read input, update, draw, repeat.

For now it only opens the window, to check that the setup works.
The menu, the board and the win screen arrive in phase F4.
"""

import asyncio

import pygame

from hanoi import config


async def run() -> None:
    """Open the window and keep it alive until the player closes it."""
    pygame.init()
    screen = pygame.display.set_mode(
        (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SCALED | pygame.RESIZABLE
    )
    pygame.display.set_caption(config.WINDOW_TITLE)
    font = pygame.font.Font(None, 64)
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(config.BACKGROUND_COLOR)
        title = font.render(config.WINDOW_TITLE, True, config.TEXT_COLOR)
        screen.blit(title, title.get_rect(center=screen.get_rect().center))
        pygame.display.flip()

        clock.tick(config.FPS)
        # In the browser the game shares a single thread with the page.
        # Yielding here once per frame lets the page breathe instead of freezing.
        await asyncio.sleep(0)

    pygame.quit()
