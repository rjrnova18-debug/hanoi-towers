"""Tests for the sound effects (game/audio.py), with SDL's dummy sound driver from conftest.py."""

import pygame
import pytest

from hanoi.game.audio import Audio, Sound


@pytest.fixture(autouse=True)
def sound_system():
    pygame.init()
    yield
    pygame.mixer.stop()  # no test leaves a sound playing for the next one


def test_every_sound_file_is_in_assets_and_loads():
    audio = Audio()

    assert set(audio.sounds) == set(Sound)


def test_missing_files_leave_the_game_quiet_instead_of_crashing(tmp_path):
    audio = Audio(folder=tmp_path)  # an empty folder: no sounds at all

    audio.play(Sound.PICK)  # must not raise

    assert audio.sounds == {}


def test_play_starts_the_sound():
    Audio().play(Sound.WIN)

    assert pygame.mixer.get_busy()


def test_muted_audio_plays_nothing():
    Audio(muted=True).play(Sound.WIN)

    assert not pygame.mixer.get_busy()


def test_muting_also_stops_the_sounds_already_playing():
    audio = Audio()
    audio.play(Sound.WIN)

    audio.toggle_mute()

    assert audio.muted
    assert not pygame.mixer.get_busy()


def test_toggling_twice_turns_the_sound_back_on():
    audio = Audio()

    audio.toggle_mute()
    audio.toggle_mute()

    assert not audio.muted
