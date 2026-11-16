"""The app: opens the window, owns what screens share, and runs the main loop.

Every frame: read input -> update -> draw -> repeat. The current screen does the real work.
Two things belong to no single screen, so the app does them for all of them:
- when the screen changes, the last frame of the old one fades out on top of the new one;
- the sound button in the top-right corner (or the M key) mutes the game.
"""

import asyncio

import pygame

from hanoi import config
from hanoi.game.audio import Audio, Sound
from hanoi.game.screens.base import Screen
from hanoi.game.screens.menu import MenuScreen
from hanoi.game.screens.play import PlayScreen
from hanoi.game.screens.win import WinScreen
from hanoi.game.widgets import Button, draw_speaker, load_fonts
from hanoi.logic.session import GameSession
from hanoi.storage import FileBackend, SaveData

SOUND_BUTTON_CENTER = (config.SCREEN_WIDTH - 28, 26)  # the top-right corner


class App:
    def __init__(self, save: SaveData | None = None) -> None:
        """`save` can be passed in (tests use a temporary file); by default it is the real one."""
        pygame.init()
        self.surface = pygame.display.set_mode(
            (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SCALED | pygame.RESIZABLE
        )
        pygame.display.set_caption(config.WINDOW_TITLE)
        self.fonts = load_fonts()
        self.save = save or SaveData(FileBackend())
        self.audio = Audio(muted=self.save.muted)  # starts the way the player left it
        self.sound_button = Button("", SOUND_BUTTON_CENTER, width=40, height=34, key=pygame.K_m)
        self.screen: Screen = MenuScreen(self)
        self.running = True
        self.fading_frame: pygame.Surface | None = None  # last frame of the previous screen
        self.fade_left = 0.0  # seconds until the fade is over

    # --- Switching screens (the screens call these) -----------------------------------

    def show_menu(self) -> None:
        self._switch_to(MenuScreen(self))

    def start_game(self, disk_count: int) -> None:
        self._switch_to(PlayScreen(self, disk_count))

    def show_win(self, session: GameSession) -> None:
        """Save the result if it is a record, then show the win screen."""
        result = session.result()
        if result is None:
            return  # the game is not won: nothing to show
        is_new_record = self.save.submit(result)
        self._switch_to(WinScreen(self, result, session.towers.position(), is_new_record))

    def _switch_to(self, screen: Screen) -> None:
        """Show a new screen, keeping a picture of the old one to fade it out."""
        self.fading_frame = self.surface.copy()
        self.fade_left = config.FADE_DURATION
        self.screen = screen

    # --- Main loop ---------------------------------------------------------------------

    async def run(self) -> None:
        clock = pygame.time.Clock()
        while self.running:
            dt = clock.tick(config.FPS) / 1000  # seconds since the last frame
            self.step(pygame.event.get(), dt)
            pygame.display.flip()

            # In the browser the game shares a single thread with the page.
            # Yielding here once per frame lets the page breathe instead of freezing.
            await asyncio.sleep(0)

        pygame.quit()

    def step(self, events: list[pygame.event.Event], dt: float) -> None:
        """One frame: input, update, draw. Kept apart from run() so tests can drive frames."""
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            elif self.sound_button.is_pressed(event):
                self._toggle_sound()  # the screen never sees this click or key
            else:
                self.screen.handle_event(event)
        self.screen.update(dt)
        self.screen.draw(self.surface)
        self._draw_sound_button()
        self._draw_fade(dt)

    def _toggle_sound(self) -> None:
        """Mute or unmute, and save the choice so the next game starts the same way."""
        self.audio.toggle_mute()
        self.save.set_muted(self.audio.muted)
        self.audio.play(Sound.PICK)  # a click you can hear says "the sound is back"

    def _draw_sound_button(self) -> None:
        top = self.sound_button.draw_key(self.surface)
        draw_speaker(self.surface, top.center, muted=self.audio.muted)

    def _draw_fade(self, dt: float) -> None:
        """Draw the old screen's last frame over the new one, more transparent every frame."""
        if self.fading_frame is None:
            return
        self.fade_left -= dt
        if self.fade_left <= 0:
            self.fading_frame = None
            return
        opacity = self.fade_left / config.FADE_DURATION  # 1 = fully visible, 0 = gone
        self.fading_frame.set_alpha(round(255 * opacity))
        self.surface.blit(self.fading_frame, (0, 0))


async def run() -> None:
    await App().run()
