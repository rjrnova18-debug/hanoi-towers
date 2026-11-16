"""Saves the player's best records and settings between games.

Two layers, so the game never cares WHERE the data lives:
- SaveData: what is saved (best record per disk count, sound on/off) and how it becomes
  JSON text.
- A backend: where that text is kept. FileBackend writes a file on the PC;
  BrowserBackend keeps it in the browser's localStorage.
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from hanoi.logic.session import GameResult

DEFAULT_SAVE_FILE = Path.home() / ".hanoi_towers" / "save.json"
SAVE_KEY = "hanoi-towers-save"  # the name of our entry in the browser's localStorage


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


class LocalStorage(Protocol):
    """The two methods of the browser's localStorage that we use (their JavaScript names)."""

    def getItem(self, key: str) -> str | None: ...

    def setItem(self, key: str, value: str) -> None: ...


class BrowserBackend:
    """Keeps the save data in the browser's localStorage.

    localStorage is a small "name -> text" store that the browser gives every web page.
    It survives closing the tab, like the file does on the PC. A web page cannot write
    files on your disk, so this is where the web version keeps its records.
    """

    def __init__(self, local_storage: LocalStorage) -> None:
        self._storage = local_storage  # passed in, so the tests can use a fake one

    def load_text(self) -> str | None:
        text = self._storage.getItem(SAVE_KEY)
        return text if isinstance(text, str) else None  # JavaScript's null when nothing saved

    def save_text(self, text: str) -> None:
        self._storage.setItem(SAVE_KEY, text)


def default_backend() -> TextBackend:
    """Where this copy of the game saves: in the browser, or in a file on the PC."""
    if sys.platform == "emscripten":  # Python compiled to run inside a web page (pygbag)
        import platform  # in the browser, pygbag adds `window`: the page's JavaScript window

        return BrowserBackend(platform.window.localStorage)
    return FileBackend()


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
    """The player's records and settings: loaded once, saved again after every change."""

    def __init__(self, backend: TextBackend) -> None:
        self._backend = backend
        data = _parse(backend.load_text())
        self._records: dict[int, Record] = _read_records(data)
        self._muted = _read_muted(data)

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
        self._save()
        return True

    @property
    def muted(self) -> bool:
        return self._muted

    def set_muted(self, muted: bool) -> None:
        self._muted = muted
        self._save()

    def _save(self) -> None:
        # Records and settings share one file, so every save writes both.
        self._backend.save_text(_to_json(self._records, self._muted))


# --- JSON <-> Python ------------------------------------------------------------------
#
# The saved text looks like this:
#   {"records": {"3": {"moves": 7, "seconds": 12.5}}, "settings": {"muted": false}}
# Saves from older versions have no "settings": the defaults are used.


def _parse(text: str | None) -> dict:
    """The saved JSON as a dict. A missing or damaged save gives an empty one."""
    if not text:
        return {}
    try:
        data = json.loads(text)
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _read_records(data: dict) -> dict[int, Record]:
    try:
        return {
            int(disk_count): Record(moves=int(saved["moves"]), seconds=float(saved["seconds"]))
            for disk_count, saved in data.get("records", {}).items()
        }
    except (ValueError, KeyError, TypeError, AttributeError):
        # A broken save file must never stop the game from starting.
        return {}


def _read_muted(data: dict) -> bool:
    settings = data.get("settings")
    return isinstance(settings, dict) and settings.get("muted") is True


def _to_json(records: dict[int, Record], muted: bool) -> str:
    # JSON keys are always text, so the disk count is saved as "3", "4", ...
    data = {
        "records": {
            str(disk_count): {"moves": record.moves, "seconds": record.seconds}
            for disk_count, record in sorted(records.items())
        },
        "settings": {"muted": muted},
    }
    return json.dumps(data, indent=2)
