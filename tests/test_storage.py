"""Tests for saving records (storage.py)."""

import platform
import sys

import pytest

from hanoi.logic.session import GameResult
from hanoi.storage import (
    SAVE_KEY,
    BrowserBackend,
    FileBackend,
    Record,
    SaveData,
    default_backend,
)


class MemoryBackend:
    """Keeps the text in a variable: lets most tests run without touching the disk."""

    def __init__(self, text: str | None = None) -> None:
        self.text = text

    def load_text(self) -> str | None:
        return self.text

    def save_text(self, text: str) -> None:
        self.text = text


def win(disk_count: int = 3, moves: int = 7, seconds: float = 20.0, assisted: bool = False):
    return GameResult(
        disk_count=disk_count, moves=moves, seconds=seconds, assisted=assisted, stars=3
    )


# --- Which result is a record ---------------------------------------------------------


def test_first_win_is_a_record():
    save = SaveData(MemoryBackend())

    assert save.submit(win(moves=9, seconds=30))
    assert save.best_record(3) == Record(moves=9, seconds=30)


def test_fewer_moves_beats_the_record():
    save = SaveData(MemoryBackend())
    save.submit(win(moves=9, seconds=10))

    assert save.submit(win(moves=7, seconds=50))
    assert save.best_record(3).moves == 7


def test_same_moves_but_faster_beats_the_record():
    save = SaveData(MemoryBackend())
    save.submit(win(moves=7, seconds=30))

    assert save.submit(win(moves=7, seconds=20))


def test_worse_game_keeps_the_old_record():
    save = SaveData(MemoryBackend())
    save.submit(win(moves=7, seconds=20))

    assert not save.submit(win(moves=9, seconds=5))
    assert save.best_record(3) == Record(moves=7, seconds=20)


def test_assisted_game_is_never_a_record():
    save = SaveData(MemoryBackend())

    assert not save.submit(win(assisted=True))
    assert save.best_record(3) is None


def test_each_disk_count_has_its_own_record():
    save = SaveData(MemoryBackend())
    save.submit(win(disk_count=3, moves=7))
    save.submit(win(disk_count=4, moves=15))

    assert save.best_record(3).moves == 7
    assert save.best_record(4).moves == 15
    assert save.best_record(5) is None


# --- Saving and loading ------------------------------------------------------------


def test_records_survive_closing_the_game():
    backend = MemoryBackend()
    SaveData(backend).submit(win(moves=8, seconds=12.34))

    reopened = SaveData(backend)

    assert reopened.best_record(3) == Record(moves=8, seconds=12.3)


@pytest.mark.parametrize(
    "damaged_text",
    ["", "not json", "[]", '{"records": 5}', '{"records": {"3": {"moves": "x"}}}'],
)
def test_damaged_save_starts_fresh_instead_of_crashing(damaged_text):
    save = SaveData(MemoryBackend(damaged_text))

    assert save.best_record(3) is None


def test_file_backend_writes_and_reads_a_real_file(tmp_path):
    path = tmp_path / "folder_that_does_not_exist_yet" / "save.json"
    SaveData(FileBackend(path)).submit(win(moves=7, seconds=20))

    reopened = SaveData(FileBackend(path))

    assert path.exists()
    assert reopened.best_record(3) == Record(moves=7, seconds=20)


def test_file_backend_with_no_file_yet_has_no_records(tmp_path):
    save = SaveData(FileBackend(tmp_path / "save.json"))

    assert save.best_record(3) is None


# --- Settings: sound on or off ------------------------------------------------------


def test_sound_is_on_by_default():
    assert not SaveData(MemoryBackend()).muted


def test_muting_survives_closing_the_game():
    backend = MemoryBackend()
    SaveData(backend).set_muted(True)

    assert SaveData(backend).muted


def test_a_save_from_before_settings_existed_still_loads():
    old_save = '{"records": {"3": {"moves": 7, "seconds": 20.0}}}'

    save = SaveData(MemoryBackend(old_save))

    assert save.best_record(3) == Record(moves=7, seconds=20)
    assert not save.muted


def test_records_and_settings_never_overwrite_each_other():
    backend = MemoryBackend()
    save = SaveData(backend)
    save.set_muted(True)
    save.submit(win(moves=7))

    reopened = SaveData(backend)

    assert reopened.muted
    assert reopened.best_record(3).moves == 7


@pytest.mark.parametrize("settings", ['"loud"', '{"muted": "yes"}', "[]"])
def test_damaged_settings_keep_the_sound_on_and_the_records(settings):
    text = '{"records": {"3": {"moves": 7, "seconds": 20.0}}, "settings": ' + settings + "}"

    save = SaveData(MemoryBackend(text))

    assert not save.muted
    assert save.best_record(3).moves == 7


# --- The browser version: localStorage ------------------------------------------------


class FakeLocalStorage:
    """Behaves like the browser's localStorage: a dict with JavaScript method names."""

    def __init__(self) -> None:
        self.items: dict[str, str] = {}

    def getItem(self, key: str) -> str | None:
        return self.items.get(key)  # the real one gives null (None) for a missing key

    def setItem(self, key: str, value: str) -> None:
        self.items[key] = value


def test_browser_backend_keeps_records_in_local_storage():
    storage = FakeLocalStorage()
    SaveData(BrowserBackend(storage)).submit(win(moves=7, seconds=20))

    reopened = SaveData(BrowserBackend(storage))  # like reloading the page

    assert SAVE_KEY in storage.items
    assert reopened.best_record(3) == Record(moves=7, seconds=20)


def test_browser_backend_with_nothing_saved_yet_starts_fresh():
    save = SaveData(BrowserBackend(FakeLocalStorage()))

    assert save.best_record(3) is None
    assert not save.muted


def test_on_the_pc_the_game_saves_to_a_file():
    assert isinstance(default_backend(), FileBackend)


def test_in_the_browser_the_game_saves_to_local_storage(monkeypatch):
    storage = FakeLocalStorage()

    class FakeWindow:
        localStorage = storage

    monkeypatch.setattr(sys, "platform", "emscripten")  # pretend to run inside pygbag
    monkeypatch.setattr(platform, "window", FakeWindow, raising=False)

    backend = default_backend()
    backend.save_text("hello")

    assert isinstance(backend, BrowserBackend)
    assert storage.items[SAVE_KEY] == "hello"
