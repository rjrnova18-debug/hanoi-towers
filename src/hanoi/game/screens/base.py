"""What every screen has in common, and what a screen may ask the app to do.

Screens never import each other or the app. To change screen they call the app
(for example `self.app.start_game(4)`), and the app decides what to build.
That keeps the imports flowing in one direction: app -> screens.
"""

from typing import Protocol

import pygame

from hanoi.game.widgets import Fonts
from hanoi.storage import SaveData


class AppServices(Protocol):
    """The part of the app that screens are allowed to use."""

    fonts: Fonts
    save: SaveData

    def show_menu(self) -> None: ...

    def start_game(self, disk_count: int) -> None: ...


class Screen:
    """Base class for every screen. The app calls these three methods once per frame."""

    def __init__(self, app: AppServices) -> None:
        self.app = app

    def handle_event(self, event: pygame.event.Event) -> None:
        """React to one input event (mouse, finger or keyboard)."""

    def update(self, dt: float) -> None:
        """Move animations and timers forward by `dt` seconds."""

    def draw(self, surface: pygame.Surface) -> None:
        """Paint the whole screen."""
