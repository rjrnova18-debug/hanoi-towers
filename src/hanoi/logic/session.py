"""One game in progress: the board, the move counter, undo, the timer and the score.

The screen asks the session what to do; the session asks the rules what is allowed.
Pure Python: the clock is passed in, so tests can control time.
"""

import time
from collections.abc import Callable
from dataclasses import dataclass

from hanoi.logic.rules import Move, Towers, minimum_moves
from hanoi.logic.solver import next_best_move, solve_from

# A win earns 2 stars if it took at most 1.5 times the minimum number of moves.
TWO_STAR_LIMIT = 1.5


@dataclass(frozen=True)
class GameResult:
    """What is shown on the win screen and offered to the records."""

    disk_count: int
    moves: int
    seconds: float
    assisted: bool
    stars: int  # 0 for an assisted game


def stars_for(moves: int, disk_count: int) -> int:
    """3 stars for a perfect game, 2 for a close one, 1 for any other win."""
    optimal = minimum_moves(disk_count)
    if moves <= optimal:
        return 3
    if moves <= optimal * TWO_STAR_LIMIT:
        return 2
    return 1


class GameSession:
    """A single game, from the first move to the win.

    Rules of the session:
    - The timer starts on the first move, not when the board appears.
    - Undo puts the disk back, and it counts as a move (like on the real toy).
    - Using Hint or Solve marks the game as assisted: no stars, no record.
    """

    def __init__(self, disk_count: int, clock: Callable[[], float] = time.monotonic) -> None:
        self.disk_count = disk_count
        self.towers = Towers.new_game(disk_count)
        self.move_count = 0
        self.assisted = False
        self._history: list[Move] = []
        self._clock = clock
        self._started_at: float | None = None
        self._finished_at: float | None = None

    # --- Playing -----------------------------------------------------------------

    def make_move(self, move: Move) -> bool:
        """Try a move. Returns False (and changes nothing) if it is not allowed."""
        if self.is_solved() or not self.towers.can_move(move):
            return False
        self._apply(move)
        self._history.append(move)
        return True

    def undo(self) -> Move | None:
        """Take back the last move. Returns the move that puts the disk back, or None."""
        if self.is_solved() or not self._history:
            return None
        undo_move = self._history.pop().reversed()
        self._apply(undo_move)
        return undo_move

    def _apply(self, move: Move) -> None:
        if self._started_at is None:
            self._started_at = self._clock()
        self.towers.move(move)
        self.move_count += 1
        if self.towers.is_solved():
            self._finished_at = self._clock()

    # --- Help (marks the game as assisted) -----------------------------------------

    def hint(self) -> Move | None:
        """The best next move, or None if the game is over."""
        if self.is_solved():
            return None
        self.assisted = True
        return next_best_move(self.towers)

    def solution(self) -> list[Move]:
        """Every move needed to finish from here. The screen plays them one by one."""
        if self.is_solved():
            return []
        self.assisted = True
        return solve_from(self.towers)

    # --- State -------------------------------------------------------------------

    def is_solved(self) -> bool:
        return self.towers.is_solved()

    def elapsed_seconds(self) -> float:
        """Time since the first move; it stops when the game is won."""
        if self._started_at is None:
            return 0.0
        end = self._finished_at if self._finished_at is not None else self._clock()
        return end - self._started_at

    def result(self) -> GameResult | None:
        """The final score, or None while the game is still going."""
        if not self.is_solved():
            return None
        stars = 0 if self.assisted else stars_for(self.move_count, self.disk_count)
        return GameResult(
            disk_count=self.disk_count,
            moves=self.move_count,
            seconds=self.elapsed_seconds(),
            assisted=self.assisted,
            stars=stars,
        )
