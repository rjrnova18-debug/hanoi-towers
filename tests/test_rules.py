"""Tests for the game rules (logic/rules.py)."""

import pytest

from hanoi.logic.rules import IllegalMoveError, Move, Towers, minimum_moves

A, B, C = 0, 1, 2


# --- A new game -------------------------------------------------------------


def test_new_game_puts_every_disk_on_tower_a_largest_at_bottom():
    towers = Towers.new_game(3)

    assert towers.position() == ((3, 2, 1), (), ())
    assert towers.disk_count == 3


def test_new_game_needs_at_least_one_disk():
    with pytest.raises(ValueError):
        Towers.new_game(0)


@pytest.mark.parametrize(("disk_count", "expected"), [(1, 1), (3, 7), (8, 255)])
def test_minimum_moves_is_two_to_the_n_minus_one(disk_count, expected):
    assert minimum_moves(disk_count) == expected


# --- Which moves are legal ---------------------------------------------------


def test_can_move_a_disk_onto_an_empty_tower():
    towers = Towers.new_game(3)

    assert towers.can_move(Move(A, C))


def test_can_move_a_smaller_disk_onto_a_bigger_one():
    towers = Towers([[3, 2], [], [1]])

    assert towers.can_move(Move(C, A))


def test_cannot_move_a_bigger_disk_onto_a_smaller_one():
    towers = Towers([[3, 2], [], [1]])

    assert not towers.can_move(Move(A, C))


def test_cannot_move_from_an_empty_tower():
    towers = Towers.new_game(3)

    assert not towers.can_move(Move(B, C))


def test_cannot_move_a_disk_onto_its_own_tower():
    # This is exactly what the original script did ("Move disk 2 from B to B").
    towers = Towers.new_game(3)

    assert not towers.can_move(Move(A, A))


def test_cannot_use_a_tower_that_does_not_exist():
    towers = Towers.new_game(3)

    assert not towers.can_move(Move(A, 3))


# --- Applying moves ------------------------------------------------------------


def test_move_takes_the_top_disk_and_returns_it():
    towers = Towers.new_game(3)

    moved_disk = towers.move(Move(A, C))

    assert moved_disk == 1
    assert towers.position() == ((3, 2), (), (1,))


def test_illegal_move_raises_and_leaves_the_board_untouched():
    towers = Towers([[3, 2], [], [1]])
    before = towers.position()

    with pytest.raises(IllegalMoveError):
        towers.move(Move(A, C))

    assert towers.position() == before


def test_reversed_move_undoes_the_move():
    towers = Towers.new_game(3)
    move = Move(A, B)

    towers.move(move)
    towers.move(move.reversed())

    assert towers.position() == Towers.new_game(3).position()


def test_move_prints_with_tower_letters():
    assert str(Move(A, C)) == "A -> C"


# --- Winning -------------------------------------------------------------------


def test_new_game_is_not_solved():
    assert not Towers.new_game(3).is_solved()


def test_all_disks_on_tower_c_is_solved():
    assert Towers([[], [], [3, 2, 1]]).is_solved()


def test_all_disks_on_tower_b_is_not_solved():
    assert not Towers([[], [3, 2, 1], []]).is_solved()


# --- Board helpers -------------------------------------------------------------


def test_top_disk_and_tower_of():
    towers = Towers([[3], [2, 1], []])

    assert towers.top_disk(B) == 1
    assert towers.top_disk(C) is None
    assert towers.tower_of(3) == A


def test_copy_is_independent_from_the_original():
    original = Towers.new_game(3)
    clone = original.copy()

    clone.move(Move(A, C))

    assert original.position() == ((3, 2, 1), (), ())


def test_board_cannot_be_changed_from_outside():
    stacks = [[3, 2, 1], [], []]
    towers = Towers(stacks)

    stacks[0].clear()  # editing the list we passed in must not touch the board

    assert towers.position() == ((3, 2, 1), (), ())


# --- Impossible boards are rejected ---------------------------------------------


@pytest.mark.parametrize(
    "stacks",
    [
        [[2, 1], []],  # only two towers
        [[3, 1], [], []],  # disk 2 is missing
        [[2, 1], [1], []],  # disk 1 appears twice
        [[1, 2], [], []],  # bigger disk on top of a smaller one
    ],
)
def test_impossible_boards_are_rejected(stacks):
    with pytest.raises(ValueError):
        Towers(stacks)
