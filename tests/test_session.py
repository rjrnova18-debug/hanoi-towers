"""Tests for a game in progress (logic/session.py)."""

import pytest

from hanoi.logic.rules import Move
from hanoi.logic.session import GameSession, stars_for
from hanoi.logic.solver import recursive_solution

A, B, C = 0, 1, 2


class FakeClock:
    """A clock the test moves by hand, so time-based tests are exact and instant."""

    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def play_perfect_game(session: GameSession) -> None:
    for move in recursive_solution(session.disk_count):
        session.make_move(move)


# --- Moves and undo ----------------------------------------------------------------


def test_legal_move_counts_and_changes_the_board():
    session = GameSession(3)

    assert session.make_move(Move(A, C))
    assert session.move_count == 1
    assert session.towers.position() == ((3, 2), (), (1,))


def test_illegal_move_is_refused_and_not_counted():
    session = GameSession(3)
    session.make_move(Move(A, C))

    assert not session.make_move(Move(A, C))  # disk 2 can't go on top of disk 1
    assert session.move_count == 1


def test_undo_puts_the_disk_back_and_counts_as_a_move():
    session = GameSession(3)
    session.make_move(Move(A, C))

    undo_move = session.undo()

    assert undo_move == Move(C, A)
    assert session.towers.position() == ((3, 2, 1), (), ())
    assert session.move_count == 2


def test_undo_goes_back_several_moves():
    session = GameSession(3)
    session.make_move(Move(A, C))
    session.make_move(Move(A, B))

    session.undo()
    session.undo()

    assert session.towers.position() == ((3, 2, 1), (), ())


def test_undo_with_no_moves_does_nothing():
    session = GameSession(3)

    assert session.undo() is None
    assert session.move_count == 0


def test_no_moves_or_undo_after_winning():
    session = GameSession(3)
    play_perfect_game(session)

    assert not session.make_move(Move(C, A))
    assert session.undo() is None


# --- Timer -------------------------------------------------------------------------


def test_timer_starts_on_the_first_move_and_stops_on_the_win():
    clock = FakeClock()
    session = GameSession(1, clock=clock)
    clock.advance(30)  # looking at the board does not count

    assert session.elapsed_seconds() == 0.0

    session.make_move(Move(A, B))
    clock.advance(4)
    assert session.elapsed_seconds() == 4

    session.make_move(Move(B, C))  # 1 disk: now it's solved
    clock.advance(60)
    assert session.elapsed_seconds() == 4


# --- Score -------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("moves", "expected_stars"),
    [(7, 3), (8, 2), (10, 2), (11, 1), (40, 1)],  # 3 disks: minimum 7, 2 stars up to 10.5
)
def test_stars_for_three_disks(moves, expected_stars):
    assert stars_for(moves, 3) == expected_stars


def test_perfect_game_result():
    clock = FakeClock()
    session = GameSession(3, clock=clock)

    play_perfect_game(session)
    result = session.result()

    assert result is not None
    assert result.moves == 7
    assert result.stars == 3
    assert not result.assisted


def test_no_result_while_playing():
    assert GameSession(3).result() is None


# --- Help --------------------------------------------------------------------------


def test_hint_gives_the_best_move_and_marks_the_game_as_assisted():
    session = GameSession(3)

    assert session.hint() == Move(A, C)
    assert session.assisted


def test_hint_does_not_move_anything():
    session = GameSession(3)

    session.hint()

    assert session.move_count == 0


def test_solution_finishes_the_game_from_a_messy_position():
    session = GameSession(3)
    session.make_move(Move(A, B))  # a poor first move

    for move in session.solution():
        assert session.make_move(move)

    assert session.is_solved()


def test_assisted_win_has_no_stars():
    session = GameSession(3)
    session.hint()
    play_perfect_game(session)

    result = session.result()

    assert result.assisted
    assert result.stars == 0
