"""Tests for the screens (game/screens/). They send fake input events, with no window."""

import pygame
import pytest

from hanoi import config
from hanoi.game.app import App
from hanoi.game.board_view import tower_center_x
from hanoi.game.screens.menu import MenuScreen
from hanoi.game.screens.play import PlayScreen
from hanoi.game.screens.win import WinScreen
from hanoi.game.widgets import format_time, load_fonts
from hanoi.logic.rules import Move
from hanoi.logic.session import GameResult, GameSession
from hanoi.logic.solver import recursive_solution
from hanoi.storage import FileBackend, SaveData

A, B, C = 0, 1, 2
BOARD_Y = 300  # any height inside the board area


class FakeApp:
    """Stands in for the real App: records which screen the game asked for."""

    def __init__(self, save: SaveData) -> None:
        pygame.init()  # with the dummy drivers from conftest.py: no real window opens
        self.fonts = load_fonts()
        self.save = save
        self.menu_shown = False
        self.started_with: int | None = None
        self.wins_announced = 0

    def show_menu(self) -> None:
        self.menu_shown = True

    def start_game(self, disk_count: int) -> None:
        self.started_with = disk_count

    def show_win(self, session: GameSession) -> None:
        self.wins_announced += 1


@pytest.fixture
def app(tmp_path):
    return FakeApp(SaveData(FileBackend(tmp_path / "save.json")))


# --- Fake input --------------------------------------------------------------------------


def key(screen, key_code):
    screen.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key_code))


def mouse_down(screen, x, y=BOARD_Y):
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(x, y), button=1))


def mouse_move(screen, x, y=BOARD_Y):
    screen.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(x, y), buttons=(1, 0, 0)))


def mouse_up(screen, x, y=BOARD_Y):
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=(x, y), button=1))


def click_tower(screen, tower):
    x = tower_center_x(tower)
    mouse_down(screen, x)
    mouse_up(screen, x)


def let_animations_finish(screen):
    for _ in range(300):
        screen.update(1 / 60)


def board(screen):
    return screen.session.towers.position()


# --- Menu ----------------------------------------------------------------------------------


def test_menu_number_key_starts_a_game(app):
    key(MenuScreen(app), pygame.K_5)

    assert app.started_with == 5


def test_menu_button_click_starts_a_game(app):
    menu = MenuScreen(app)
    button = menu.buttons[config.MAX_DISKS]

    mouse_down(menu, *button.rect.center)

    assert app.started_with == config.MAX_DISKS


# --- Three ways to make the same move ------------------------------------------------------


def test_click_one_tower_then_another_moves_the_disk(app):
    screen = PlayScreen(app, 3)

    click_tower(screen, A)
    click_tower(screen, C)
    let_animations_finish(screen)

    assert board(screen) == ((3, 2), (), (1,))
    assert screen.session.move_count == 1


def test_number_keys_move_the_disk(app):
    screen = PlayScreen(app, 3)

    key(screen, pygame.K_1)
    key(screen, pygame.K_3)

    assert board(screen) == ((3, 2), (), (1,))


def test_drag_and_drop_moves_the_disk(app):
    screen = PlayScreen(app, 3)

    mouse_down(screen, tower_center_x(A))
    mouse_move(screen, 600)
    mouse_move(screen, tower_center_x(C))
    mouse_up(screen, tower_center_x(C))

    assert board(screen) == ((3, 2), (), (1,))


def test_a_tiny_mouse_wobble_is_still_a_click(app):
    screen = PlayScreen(app, 3)

    mouse_down(screen, tower_center_x(A))
    mouse_move(screen, tower_center_x(A) + 2)
    mouse_up(screen, tower_center_x(A) + 2)

    assert screen.held is not None  # still holding, waiting for the second click
    assert screen.session.move_count == 0


# --- Moves that do not happen ----------------------------------------------------------


def test_illegal_drop_is_refused_and_the_disk_shakes(app):
    screen = PlayScreen(app, 3)
    screen.session.make_move(Move(A, C))  # disk 1 is now on C

    click_tower(screen, A)  # pick disk 2
    click_tower(screen, C)  # disk 2 can't go on disk 1

    assert board(screen) == ((3, 2), (), (1,))
    assert screen.session.move_count == 1
    assert screen.shake is not None


def test_dropping_on_its_own_tower_puts_the_disk_back(app):
    screen = PlayScreen(app, 3)

    click_tower(screen, A)
    click_tower(screen, A)

    assert screen.held is None
    assert screen.session.move_count == 0


def test_clicking_an_empty_tower_picks_up_nothing(app):
    screen = PlayScreen(app, 3)

    click_tower(screen, B)

    assert screen.held is None


def test_drag_released_outside_the_board_puts_the_disk_back(app):
    screen = PlayScreen(app, 3)

    mouse_down(screen, tower_center_x(A))
    mouse_move(screen, 500, 20)  # up into the score bar
    mouse_up(screen, 500, 20)

    assert screen.held is None
    assert screen.session.move_count == 0


def test_input_waits_while_a_disk_is_flying(app):
    screen = PlayScreen(app, 3)
    key(screen, pygame.K_1)
    key(screen, pygame.K_3)  # disk 1 starts flying to C

    key(screen, pygame.K_1)  # too early: ignored

    assert screen.held is None


# --- Buttons -----------------------------------------------------------------------------


def test_undo_key_takes_the_move_back(app):
    screen = PlayScreen(app, 3)
    key(screen, pygame.K_1)
    key(screen, pygame.K_3)
    let_animations_finish(screen)

    key(screen, pygame.K_u)

    assert board(screen) == ((3, 2, 1), (), ())


def test_restart_key_asks_for_a_new_game_with_the_same_disks(app):
    key(PlayScreen(app, 5), pygame.K_r)

    assert app.started_with == 5


def test_escape_puts_the_disk_down_first_then_opens_the_menu(app):
    screen = PlayScreen(app, 3)
    key(screen, pygame.K_1)

    key(screen, pygame.K_ESCAPE)
    assert screen.held is None
    assert not app.menu_shown

    key(screen, pygame.K_ESCAPE)
    assert app.menu_shown


# --- Drawing does not crash in any state --------------------------------------------------


def test_every_screen_state_can_be_drawn(app):
    surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    screen = PlayScreen(app, 4)

    screen.draw(surface)  # resting
    key(screen, pygame.K_1)
    screen.draw(surface)  # holding a disk
    key(screen, pygame.K_2)
    screen.draw(surface)  # disk flying
    let_animations_finish(screen)
    key(screen, pygame.K_1)
    key(screen, pygame.K_2)
    screen.draw(surface)  # shaking after an illegal move
    MenuScreen(app).draw(surface)


def test_format_time():
    assert format_time(0) == "0:00"
    assert format_time(75.9) == "1:15"


# --- Winning -------------------------------------------------------------------------------


def win_by_keys(screen):
    """Solve the game by pressing the tower keys, letting each disk land."""
    keys = [pygame.K_1, pygame.K_2, pygame.K_3]
    for move in recursive_solution(screen.disk_count):
        key(screen, keys[move.source])
        key(screen, keys[move.target])
        let_animations_finish(screen)


def test_winning_announces_the_win_once_after_a_short_pause(app):
    screen = PlayScreen(app, 3)

    win_by_keys(screen)
    for _ in range(120):
        screen.update(1 / 60)

    assert app.wins_announced == 1


def a_win(disk_count=3, moves=7, assisted=False, stars=3):
    return GameResult(disk_count, moves, seconds=20, assisted=assisted, stars=stars)


def solved_board(disk_count):
    return ((), (), tuple(range(disk_count, 0, -1)))


def test_win_screen_buttons(app):
    win = WinScreen(app, a_win(disk_count=4), solved_board(4), is_new_record=True)

    key(win, pygame.K_n)
    assert app.started_with == 5
    key(win, pygame.K_RETURN)
    assert app.started_with == 4
    key(win, pygame.K_ESCAPE)
    assert app.menu_shown


def test_no_next_level_after_the_largest_game(app):
    win = WinScreen(app, a_win(disk_count=config.MAX_DISKS), solved_board(8), is_new_record=True)

    key(win, pygame.K_n)

    assert "next" not in win.buttons
    assert app.started_with is None


@pytest.mark.parametrize(
    "result",
    [a_win(), a_win(moves=9, stars=2), a_win(assisted=True, stars=0)],
)
def test_win_screen_can_be_drawn(app, result):
    app.save.submit(a_win())  # so a "best" line exists
    surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

    WinScreen(app, result, solved_board(3), is_new_record=False).draw(surface)


def test_real_app_saves_the_record_and_opens_the_win_screen(tmp_path):
    real_app = App(save=SaveData(FileBackend(tmp_path / "save.json")))
    real_app.start_game(3)
    session = real_app.screen.session
    for move in recursive_solution(3):
        session.make_move(move)

    real_app.show_win(session)

    assert isinstance(real_app.screen, WinScreen)
    assert real_app.screen.is_new_record
    assert real_app.save.best_record(3).moves == 7
