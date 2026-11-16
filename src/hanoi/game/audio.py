"""Sound effects: loaded once, played by name, and muted all at once.

Sound is a nice extra, never a reason to crash: if the device has no sound card,
or a file is missing, the game simply stays quiet.
"""

from enum import StrEnum
from pathlib import Path

import pygame

from hanoi import config


class Sound(StrEnum):
    """The game's sound effects. Each value is also the file name in assets/sounds/."""

    PICK = "pick"  # a disk is lifted
    DROP = "drop"  # a disk lands on a tower
    ERROR = "error"  # an illegal move
    WIN = "win"  # the puzzle is solved without help


class Audio:
    """Plays the sound effects, unless the player muted them."""

    def __init__(self, folder: Path = config.SOUNDS_DIR, muted: bool = False) -> None:
        self.muted = muted
        self.sounds = _load_sounds(folder)

    def play(self, sound: Sound) -> None:
        if not self.muted and sound in self.sounds:
            self.sounds[sound].play()

    def toggle_mute(self) -> None:
        self.muted = not self.muted
        if self.muted and pygame.mixer.get_init():
            pygame.mixer.stop()  # also silence the sounds that are already playing


def _load_sounds(folder: Path) -> dict[Sound, pygame.mixer.Sound]:
    """Every sound that could be loaded, at its volume from config.SOUND_VOLUMES."""
    if not _sound_system_ready():
        return {}
    sounds = {}
    for sound in Sound:
        try:
            loaded = pygame.mixer.Sound(folder / f"{sound}.ogg")
        except (pygame.error, OSError):
            continue  # this one stays silent; the others still work
        loaded.set_volume(config.SOUND_VOLUMES[sound])
        sounds[sound] = loaded
    return sounds


def _sound_system_ready() -> bool:
    """pygame.init() starts the sound system when it can. False if this device has none."""
    if pygame.mixer.get_init() is None:
        try:
            pygame.mixer.init()
        except pygame.error:
            return False
    return True
