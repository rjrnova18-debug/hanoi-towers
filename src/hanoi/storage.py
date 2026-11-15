"""Saves the player's best records between games.

Two layers, so the game never cares WHERE the data lives:
- SaveData: what is saved (best record per disk count) and how it becomes JSON text.
- A backend: where that text is kept. FileBackend writes a file on the PC;
  the browser version (phase F7) will keep it in localStorage instead.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from hanoi.logic.session import GameResult

DEFAULT_SAVE_FILE = Path.home() / ".hanoi_towers" / "save.json"


class TextBackend(Protocol):
    """Anything that can keep one piece of text. SaveData only needs these two methods."""

    def load_text(self) -> str | None: ...

    def save_text(self, text: str) -> None: ...


class FileBackend:
    """Keeps the save data in a JSON file on this computer."""

    def __init__(self, path: Path = DEFAULT_SAVE_FILE) -> None:
        self.path = path

    def load_text(self) -> str | None:
        if not self.path.exists():
            return None
        return self.path.read_text(encoding="utf-8")

    def save_text(self, text: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(text, encoding="utf-8")


@dataclass(frozen=True)
class Record:
    """The best game for one disk count."""

    moves: int
    seconds: float

    def is_better_than(self, other: "Record | None") -> bool:
        """Fewer moves wins; with the same moves, the faster game wins."""
        if other is None:
            return True
        return (self.moves, self.seconds) < (other.moves, other.seconds)


class SaveData:
    """The player's best records, loaded once and saved after every new record."""

    def __init__(self, backend: TextBackend) -> None:
        self._backend = backend
        self._records: dict[int, Record] = _read_records(backend.load_text())

    def best_record(self, disk_count: int) -> Record | None:
        return self._records.get(disk_count)

    def submit(self, result: GameResult) -> bool:
        """Keep the result if it beats the record. Returns True for a new record.

        Assisted games never count.
        """
        if result.assisted:
            return False
        candidate = Record(moves=result.moves, seconds=round(result.seconds, 1))
        if not candidate.is_better_than(self.best_record(result.disk_count)):
            return False
        self._records[result.disk_count] = candidate
        self._backend.save_text(_write_records(self._records))
        return True


def _read_records(text: str | None) -> dict[int, Record]:
    """Turn saved JSON text into records. A missing or damaged save starts fresh."""
    if not text:
        return {}
    try:
        data = json.loads(text)
        return {
            int(disk_count): Record(moves=int(saved["moves"]), seconds=float(saved["seconds"]))
            for disk_count, saved in data["records"].items()
        }
    except (ValueError, KeyError, TypeError, AttributeError):
        # A broken save file must never stop the game from starting.
        return {}


def _write_records(records: dict[int, Record]) -> str:
    # JSON keys are always text, so the disk count is saved as "3", "4", ...
    data = {
        "records": {
            str(disk_count): {"moves": record.moves, "seconds": record.seconds}
            for disk_count, record in sorted(records.items())
        }
    }
    return json.dumps(data, indent=2)
