"""Tests for the solving algorithms (logic/solver.py)."""

import importlib.util
import itertools
import re
from collections import deque
from pathlib import Path

import pytest

from hanoi.logic.rules import GOAL_TOWER, Move, Position, Towers, minimum_moves
from hanoi.logic.solver import (
    iterative_solution,
    next_best_move,
    recursive_solution,
    solve_from,
    spare_tower,
)

A, B, C = 0, 1, 2
DISK_COUNTS = range(1, 9)  # the game offers 3 to 8 disks; 1 and 2 are cheap edge cases

LEGACY_SCRIPT = Path(__file__).parent.parent / "legacy" / "hanoi_og_code.py"


def play(moves: list[Move], disk_count: int) -> Towers:
    """Play the moves on a new board. Raises IllegalMoveError if any move breaks the rules."""
    towers = Towers.new_game(disk_count)
    for move in moves:
        towers.move(move)
    return towers


# --- The bug in the original script -----------------------------------------------


def run_legacy_iterative(disk_count: int, capsys) -> list[tuple[str, str]]:
    """Run the untouched original script and collect the (source, target) it printed."""
    spec = importlib.util.spec_from_file_location("hanoi_og_code", LEGACY_SCRIPT)
    legacy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy)  # the script also runs a demo when loaded
    capsys.readouterr()  # throw away the demo output

    legacy.hanoi_iterativo(disk_count, "A", "C", "B")
    printed = capsys.readouterr().out
    # Each line looks like: "Mover disco 2 de B a B"
    return re.findall(r"de (\w) a (\w)", printed)


def test_original_script_moved_disks_onto_their_own_tower(capsys):
    """Documents the bug that this project fixes. The legacy file is never edited."""
    legacy_moves = run_legacy_iterative(3, capsys)

    moves_to_same_tower = [pair for pair in legacy_moves if pair[0] == pair[1]]
    assert len(legacy_moves) == 7
    assert len(moves_to_same_tower) == 5  # e.g. "Mover disco 2 de B a B"


# --- Both solutions are correct and optimal ------------------------------------------


@pytest.mark.parametrize("solution", [recursive_solution, iterative_solution])
@pytest.mark.parametrize("disk_count", DISK_COUNTS)
def test_solution_is_legal_solves_the_game_and_uses_minimum_moves(solution, disk_count):
    moves = solution(disk_count)

    towers = play(moves, disk_count)  # fails here if any move is illegal

    assert towers.is_solved()
    assert len(moves) == minimum_moves(disk_count)


@pytest.mark.parametrize("disk_count", DISK_COUNTS)
def test_iterative_and_recursive_give_the_same_moves(disk_count):
    # The optimal solution is unique, so two correct algorithms must agree move by move.
    assert iterative_solution(disk_count) == recursive_solution(disk_count)


def test_fixed_iterative_never_moves_a_disk_onto_its_own_tower():
    for disk_count in DISK_COUNTS:
        assert all(move.source != move.target for move in iterative_solution(disk_count))


def test_three_disks_known_sequence():
    assert recursive_solution(3) == [
        Move(A, C),
        Move(A, B),
        Move(C, B),
        Move(A, C),
        Move(B, A),
        Move(B, C),
        Move(A, C),
    ]


def test_recursive_solution_between_any_two_towers():
    # A tower can be moved between any two pegs, not only from A to C.
    assert recursive_solution(2, source=B, target=A) == [Move(B, C), Move(B, A), Move(C, A)]


@pytest.mark.parametrize(("first", "second", "spare"), [(A, B, C), (A, C, B), (C, B, A)])
def test_spare_tower_is_the_third_one(first, second, spare):
    assert spare_tower(first, second) == spare


# --- Solving from any position -------------------------------------------------------
#
# The judge: a breadth-first search (BFS) that explores EVERY legal position and measures
# its true distance to the goal. It is slow (3^n positions) but obviously correct, so it
# is a good referee for the fast solver on small boards.


def every_legal_position(disk_count: int) -> list[Towers]:
    """All 3^n boards: each disk can sit on any tower, always largest at the bottom."""
    boards = []
    for towers_of_disks in itertools.product(range(3), repeat=disk_count):
        stacks = [[], [], []]
        for disk in range(disk_count, 0, -1):  # place the largest disks first
            stacks[towers_of_disks[disk - 1]].append(disk)
        boards.append(Towers(stacks))
    return boards


def legal_moves(towers: Towers) -> list[Move]:
    all_moves = [Move(source, target) for source in range(3) for target in range(3)]
    return [move for move in all_moves if towers.can_move(move)]


def distances_to_goal(disk_count: int) -> dict[Position, int]:
    """BFS from the solved board. Every move can be undone, so distances work both ways."""
    goal = Towers([[], [], list(range(disk_count, 0, -1))])
    distances = {goal.position(): 0}
    queue = deque([goal])
    while queue:
        board = queue.popleft()
        for move in legal_moves(board):
            neighbour = board.copy()
            neighbour.move(move)
            if neighbour.position() not in distances:
                distances[neighbour.position()] = distances[board.position()] + 1
                queue.append(neighbour)
    return distances


@pytest.mark.parametrize("disk_count", range(1, 6))
def test_solve_from_is_shortest_from_every_position(disk_count):
    distances = distances_to_goal(disk_count)

    for board in every_legal_position(disk_count):
        moves = solve_from(board)

        finished = board.copy()
        for move in moves:
            finished.move(move)  # fails here if any move is illegal
        assert finished.is_solved()
        assert len(moves) == distances[board.position()], f"not shortest from {board.position()}"


def test_solve_from_a_new_game_is_the_classic_solution():
    assert solve_from(Towers.new_game(4)) == recursive_solution(4)


def test_solve_from_does_not_change_the_board_it_receives():
    board = Towers([[3], [2], [1]])

    solve_from(board)

    assert board.position() == ((3,), (2,), (1,))


def test_solve_from_a_solved_board_needs_no_moves():
    assert solve_from(Towers([[], [], [3, 2, 1]])) == []


def test_solve_from_can_aim_at_any_tower():
    assert solve_from(Towers.new_game(3), target=B) == recursive_solution(3, source=A, target=B)


def test_next_best_move_after_a_mistake():
    # The player moved disk 1 to B (the best first move for 3 disks is A -> C).
    board = Towers([[3, 2], [1], []])

    assert next_best_move(board) == Move(B, C)


def test_next_best_move_is_none_when_solved():
    assert next_best_move(Towers([[], [], [2, 1]]), target=GOAL_TOWER) is None
