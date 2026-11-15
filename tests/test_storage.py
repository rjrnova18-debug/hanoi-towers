"""Tests for saving records (storage.py)."""

import pytest

from hanoi.logic.session import GameResult
from hanoi.storage import FileBackend, Record, SaveData


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
