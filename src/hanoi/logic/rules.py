"""Game rules: the three towers and which moves are allowed.

Pure Python. Knows nothing about drawing, sound or time.
Disks are numbers: 1 is the smallest disk, n the largest.
"""

from dataclasses import dataclass
from itertools import pairwise

TOWER_NAMES = "ABC"
START_TOWER = 0  # A: where every game begins
GOAL_TOWER = 2  # C: where every disk must end

# A position is a snapshot of the board: one tuple per tower, disks from bottom to top.
# Tuples can't change and can be compared and used as dict keys (the solver tests need that).
Position = tuple[tuple[int, ...], ...]


class IllegalMoveError(ValueError):
    """Raised when someone tries a move that breaks the rules."""


@dataclass(frozen=True)
class Move:
    """Take the top disk of `source` and put it on `target` (tower indexes 0, 1, 2)."""

    source: int
    target: int

    def reversed(self) -> "Move":
        """The move that undoes this one."""
        return Move(self.target, self.source)

    def __str__(self) -> str:
        return f"{TOWER_NAMES[self.source]} -> {TOWER_NAMES[self.target]}"


def minimum_moves(disk_count: int) -> int:
    """Fewest moves needed to solve a new game: 2^n - 1."""
    return 2**disk_count - 1


class Towers:
    """The board: three stacks of disks.

    Each stack is a list from bottom to top, so the top disk is always the last item.
    """

    def __init__(self, stacks: list[list[int]]) -> None:
        _check_is_valid(stacks)
        self._stacks = [list(stack) for stack in stacks]  # private copy: nobody else can edit it

    @classmethod
    def new_game(cls, disk_count: int) -> "Towers":
        """All disks on the start tower, largest at the bottom."""
        if disk_count < 1:
            raise ValueError("a game needs at least 1 disk")
        start_stack = list(range(disk_count, 0, -1))  # e.g. 3 disks -> [3, 2, 1]
        stacks = [[] for _ in TOWER_NAMES]
        stacks[START_TOWER] = start_stack
        return cls(stacks)

    @property
    def disk_count(self) -> int:
        return sum(len(stack) for stack in self._stacks)

    def position(self) -> Position:
        """A read-only snapshot of the board."""
        return tuple(tuple(stack) for stack in self._stacks)

    def top_disk(self, tower: int) -> int | None:
        """The disk on top of a tower, or None if the tower is empty."""
        stack = self._stacks[tower]
        return stack[-1] if stack else None

    def tower_of(self, disk: int) -> int:
        """Which tower a disk is on."""
        for tower, stack in enumerate(self._stacks):
            if disk in stack:
                return tower
        raise ValueError(f"disk {disk} is not on the board")

    def can_move(self, move: Move) -> bool:
        """True if the move follows the rules of the puzzle."""
        valid_towers = range(len(self._stacks))
        if move.source not in valid_towers or move.target not in valid_towers:
            return False
        if move.source == move.target:
            return False  # the bug of the original script: moving a disk onto its own tower
        moving_disk = self.top_disk(move.source)
        if moving_disk is None:
            return False  # nothing to move
        target_top = self.top_disk(move.target)
        return target_top is None or moving_disk < target_top

    def move(self, move: Move) -> int:
        """Apply a move and return the disk that was moved.

        Raises IllegalMoveError (and leaves the board untouched) if the move is not allowed.
        """
        if not self.can_move(move):
            raise IllegalMoveError(f"illegal move {move} on {self.position()}")
        disk = self._stacks[move.source].pop()
        self._stacks[move.target].append(disk)
        return disk

    def is_solved(self) -> bool:
        """True when every disk is on the goal tower."""
        return len(self._stacks[GOAL_TOWER]) == self.disk_count

    def copy(self) -> "Towers":
        """An independent board with the same disks (the solver plays on copies)."""
        return Towers(self._stacks)


def _check_is_valid(stacks: list[list[int]]) -> None:
    """Reject boards that can't exist: wrong number of towers, missing disks, big on small."""
    if len(stacks) != len(TOWER_NAMES):
        raise ValueError(f"expected {len(TOWER_NAMES)} towers, got {len(stacks)}")

    all_disks = sorted(disk for stack in stacks for disk in stack)
    if all_disks != list(range(1, len(all_disks) + 1)):
        raise ValueError(f"disks must be 1..n, each exactly once, got {all_disks}")

    for stack in stacks:
        # pairwise([3, 2, 1]) -> (3, 2), (2, 1): each disk next to the one above it
        is_largest_at_bottom = all(lower > upper for lower, upper in pairwise(stack))
        if not is_largest_at_bottom:
            raise ValueError(f"a bigger disk sits on a smaller one: {stack}")
