"""Algorithms that solve the puzzle. They return moves; they never draw anything.

- recursive_solution: the classic textbook solution, from a new game.
- iterative_solution: the loop-based idea from the original script, with its bug fixed.
- solve_from / next_best_move: the shortest way to finish from ANY position
  (this is what powers the Hint and Solve buttons).
"""

from hanoi.logic.rules import GOAL_TOWER, START_TOWER, Move, Towers, minimum_moves

A, B, C = 0, 1, 2


def spare_tower(first: int, second: int) -> int:
    """The tower that is neither `first` nor `second`.

    Towers are 0, 1 and 2, which add up to 3, so the missing one is 3 minus the other two.
    """
    return 3 - first - second


def recursive_solution(
    disk_count: int, source: int = START_TOWER, target: int = GOAL_TOWER
) -> list[Move]:
    """Moves that carry disks 1..disk_count from `source` to `target`.

    To move n disks: move the n-1 smaller ones out of the way (to the spare tower),
    move the largest disk, then bring the n-1 smaller ones back on top of it.
    """
    if disk_count == 0:
        return []
    spare = spare_tower(source, target)
    return [
        *recursive_solution(disk_count - 1, source, spare),
        Move(source, target),
        *recursive_solution(disk_count - 1, spare, target),
    ]


def iterative_solution(disk_count: int) -> list[Move]:
    """The same optimal moves, found with a loop instead of recursion.

    The moves cycle through three pairs of towers. In each pair only one direction is
    legal (the smaller top disk goes onto the other tower), so the board decides it.
    The order of the pairs depends on whether the number of disks is odd or even.
    """
    towers = Towers.new_game(disk_count)
    pairs = _tower_pairs_in_order(disk_count)
    moves = []
    for step in range(minimum_moves(disk_count)):
        first, second = pairs[step % 3]
        move = _legal_move_between(towers, first, second)
        towers.move(move)
        moves.append(move)
    return moves


def _tower_pairs_in_order(disk_count: int) -> list[tuple[int, int]]:
    # The original script always used the odd order, so it failed for an even number of disks.
    if disk_count % 2 == 1:
        return [(A, C), (A, B), (B, C)]
    return [(A, B), (A, C), (B, C)]


def _legal_move_between(towers: Towers, first: int, second: int) -> Move:
    """Between two towers, return the direction that the rules allow."""
    # The original script tried to pick this direction by hand and sometimes chose the
    # same tower twice ("move disk 2 from B to B"). Asking the rules can't go wrong.
    forward = Move(first, second)
    return forward if towers.can_move(forward) else forward.reversed()


# --- Solving from any position (Hint and Solve buttons) -----------------------------


def solve_from(towers: Towers, target: int = GOAL_TOWER) -> list[Move]:
    """Shortest list of moves from the current position to every disk on `target`.

    Works from any legal position, not only from a new game. The board passed in is
    not changed: the solver plays on a copy.
    """
    board = towers.copy()
    moves: list[Move] = []
    _gather(board, board.disk_count, target, moves)
    return moves


def next_best_move(towers: Towers, target: int = GOAL_TOWER) -> Move | None:
    """The first move of the shortest solution, or None if the game is already solved."""
    moves = solve_from(towers, target)
    return moves[0] if moves else None


def _gather(board: Towers, largest: int, target: int, moves: list[Move]) -> None:
    """Bring disks 1..largest onto `target`, wherever they are now.

    Look only at the largest disk: if it is not on the target yet, the smaller disks must
    first get out of the way (onto the spare tower), then the largest disk moves.
    Either way, the smaller disks end by gathering on top of it.
    """
    if largest == 0:
        return
    current = board.tower_of(largest)
    if current != target:
        spare = spare_tower(current, target)
        _gather(board, largest - 1, spare, moves)  # clear the way
        _play(board, Move(current, target), moves)  # move the largest disk
    _gather(board, largest - 1, target, moves)  # smaller disks on top of it


def _play(board: Towers, move: Move, moves: list[Move]) -> None:
    board.move(move)
    moves.append(move)
