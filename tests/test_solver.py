"""Tests for the solving algorithms (logic/solver.py)."""

import importlib.util
import re
from pathlib import Path

import pytest

from hanoi.logic.rules import Move, Towers, minimum_moves
from hanoi.logic.solver import iterative_solution, recursive_solution, spare_tower

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
    # The solver for "any position" (next step) needs to move small towers around.
    assert recursive_solution(2, source=B, target=A) == [Move(B, C), Move(B, A), Move(C, A)]


@pytest.mark.parametrize(("first", "second", "spare"), [(A, B, C), (A, C, B), (C, B, A)])
def test_spare_tower_is_the_third_one(first, second, spare):
    assert spare_tower(first, second) == spare
