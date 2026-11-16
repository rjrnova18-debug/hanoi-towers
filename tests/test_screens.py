"""Tests for the screens (game/screens/). They send fake input events, with no window."""

import pygame
import pytest

from hanoi import config
from hanoi.game.app import App
from hanoi.game.audio import Sound
from hanoi.game.board_view import tower_center_x
from hanoi.game.screens.base import Screen
from hanoi.game.screens.menu import DemoBoard, MenuScreen
from hanoi.game.screens.play import PlayScreen
from hanoi.game.screens.win import WinScreen
from hanoi.game.widgets import format_time, load_fonts
from hanoi.logic.rules import Move
from hanoi.logic.session import GameResult, GameSession
from hanoi.logic.solver import recursive_solution
from hanoi.storage import FileBackend, SaveData

A, B, C = 0, 1, 2
BOARD_Y = 300  # any height inside the board area


class FakeAudio:
    """Stands in for the real Audio: writes down the sounds instead of playing them."""

    def __init__(self) -> None:
        self.played: list[Sound] = []

    def play(self, sound: Sound) -> None:
        self.played.append(sound)


class FakeApp:
    """Stands in for the real App: records which screen the game asked for."""

    def __init__(self, save: SaveData) -> None:
        pygame.init()  # with the dummy drivers from conftest.py: no real window opens
        self.fonts = load_fonts()
        self.save = save
        self.audio = FakeAudio()
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


def test_menu_demo_solves_back_and_forth_forever():
    demo = DemoBoard()
    disk_count = config.MENU_DEMO_DISKS
    full_tower = tuple(range(disk_count, 0, -1))
    seen = []

    for _ in range(60 * 120):  # two minutes of frames (about 20 s per trip)
        demo.update(1 / 60)
        position = demo.towers.position()
        if position[C] == full_tower and (not seen or seen[-1] != "C"):
            seen.append("C")
        if position[A] == full_tower and seen and seen[-1] != "A":
            seen.append("A")

    assert seen[:3] == ["C", "A", "C"]


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
    assert screen.motion.disk == 2  # back on its tower, shaking


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


# --- Feel --------------------------------------------------------------------------------


def test_legal_towers_light_up_while_holding_a_disk(app):
    screen = PlayScreen(app, 3)
    assert screen.legal_targets() == []  # holding nothing

    key(screen, pygame.K_1)  # hold disk 1: it fits anywhere

    assert screen.legal_targets() == [B, C]


def test_only_towers_with_room_light_up(app):
    screen = PlayScreen(app, 3)
    screen.session.make_move(Move(A, C))  # disk 1 on C

    key(screen, pygame.K_1)  # hold disk 2

    assert screen.legal_targets() == [B]
    assert not screen.session.assisted  # showing the rules is not help


# --- Sounds --------------------------------------------------------------------------------


def test_a_move_sounds_like_pick_then_drop_on_landing(app):
    screen = PlayScreen(app, 3)

    key(screen, pygame.K_1)
    assert app.audio.played == [Sound.PICK]

    key(screen, pygame.K_3)
    assert app.audio.played == [Sound.PICK]  # still flying: no drop yet
    let_animations_finish(screen)
    assert app.audio.played == [Sound.PICK, Sound.DROP]


def test_an_illegal_move_sounds_the_error(app):
    screen = PlayScreen(app, 3)
    screen.session.make_move(Move(A, C))

    click_tower(screen, A)
    click_tower(screen, C)  # disk 2 can't go on disk 1

    assert app.audio.played == [Sound.PICK, Sound.ERROR]


def test_every_solver_move_lands_with_a_drop(app):
    screen = PlayScreen(app, 3)

    key(screen, pygame.K_s)
    run_frames(screen, seconds=10)

    assert app.audio.played == [Sound.DROP] * 7


# --- Hint --------------------------------------------------------------------------------


def test_hint_suggests_the_best_move_without_moving(app):
    screen = PlayScreen(app, 3)

    key(screen, pygame.K_h)

    assert screen.hint == Move(A, C)
    assert screen.session.move_count == 0
    assert screen.session.assisted


def test_hint_disappears_once_the_board_changes(app):
    screen = PlayScreen(app, 3)
    key(screen, pygame.K_h)

    key(screen, pygame.K_1)
    key(screen, pygame.K_3)

    assert screen.hint is None


def test_hint_after_a_mistake_points_to_the_recovery(app):
    screen = PlayScreen(app, 3)
    key(screen, pygame.K_1)
    key(screen, pygame.K_2)  # disk 1 to B: not the best first move
    let_animations_finish(screen)

    key(screen, pygame.K_h)

    assert screen.hint == Move(B, C)


# --- Solve -------------------------------------------------------------------------------


def run_frames(screen, seconds):
    for _ in range(round(seconds * 60)):
        screen.update(1 / 60)


def test_solve_finishes_the_game_from_a_messy_position(app):
    screen = PlayScreen(app, 4)
    key(screen, pygame.K_1)
    key(screen, pygame.K_2)  # a poor first move
    let_animations_finish(screen)

    key(screen, pygame.K_s)
    run_frames(screen, 30)

    assert screen.session.is_solved()
    assert screen.session.assisted
    assert app.wins_announced == 1


def test_solve_ignores_the_board_while_playing(app):
    screen = PlayScreen(app, 3)
    key(screen, pygame.K_s)
    run_frames(screen, 0.1)

    key(screen, pygame.K_1)

    assert screen.held is None


def test_pressing_s_again_stops_the_solver(app):
    screen = PlayScreen(app, 5)
    key(screen, pygame.K_s)
    run_frames(screen, 0.5)

    key(screen, pygame.K_s)  # Stop
    run_frames(screen, 5)

    assert not screen.is_solving
    assert not screen.session.is_solved()
    assert screen.session.move_count > 0


def test_restart_works_while_solving(app):
    screen = PlayScreen(app, 3)
    key(screen, pygame.K_s)
    run_frames(screen, 0.1)

    key(screen, pygame.K_r)

    assert app.started_with == 3


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
    key(screen, pygame.K_h)
    screen.draw(surface)  # showing a hint
    key(screen, pygame.K_s)
    run_frames(screen, 0.1)
    screen.draw(surface)  # solving by itself
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

    win = WinScreen(app, result, solved_board(3), is_new_record=False)
    win.draw(surface)  # first frame: no stars yet
    for _ in range(30):
        win.update(1 / 60)
    win.draw(surface)  # stars popping, confetti flying


def test_only_a_win_without_help_throws_confetti(app):
    earned = WinScreen(app, a_win(), solved_board(3), is_new_record=True)
    helped = WinScreen(app, a_win(assisted=True, stars=0), solved_board(3), is_new_record=False)

    assert earned.confetti
    assert not helped.confetti


def test_only_a_win_without_help_plays_the_jingle(app):
    WinScreen(app, a_win(assisted=True, stars=0), solved_board(3), is_new_record=False)
    assert app.audio.played == []

    WinScreen(app, a_win(), solved_board(3), is_new_record=True)
    assert app.audio.played == [Sound.WIN]


def test_confetti_is_cleaned_up_once_it_falls_off_screen(app):
    win = WinScreen(app, a_win(), solved_board(3), is_new_record=True)

    for _ in range(60 * 10):
        win.update(1 / 60)

    assert win.confetti == []


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


def test_changing_screen_fades_out_the_old_one(tmp_path):
    real_app = App(save=SaveData(FileBackend(tmp_path / "save.json")))
    real_app.step([], 1 / 60)  # draw the menu once

    real_app.step([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_3)], 1 / 60)

    assert isinstance(real_app.screen, PlayScreen)
    assert real_app.fading_frame is not None  # the menu is fading out
    for _ in range(30):  # half a second
        real_app.step([], 1 / 60)
    assert real_app.fading_frame is None


def test_closing_the_window_stops_the_loop(tmp_path):
    real_app = App(save=SaveData(FileBackend(tmp_path / "save.json")))

    real_app.step([pygame.event.Event(pygame.QUIT)], 1 / 60)

    assert not real_app.running


# --- Sound button (owned by the app, on every screen) -------------------------------------


def press_m(real_app):
    real_app.step([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m)], 1 / 60)


def test_m_mutes_and_the_choice_is_remembered_next_time(tmp_path):
    save_file = tmp_path / "save.json"
    real_app = App(save=SaveData(FileBackend(save_file)))

    press_m(real_app)
    assert real_app.audio.muted

    next_time = App(save=SaveData(FileBackend(save_file)))
    assert next_time.audio.muted


def test_m_again_turns_the_sound_back_on(tmp_path):
    real_app = App(save=SaveData(FileBackend(tmp_path / "save.json")))

    press_m(real_app)
    press_m(real_app)

    assert not real_app.audio.muted
    assert not real_app.save.muted


class EventRecorder(Screen):
    """A screen that only writes down the events it receives."""

    def __init__(self, app) -> None:
        super().__init__(app)
        self.events: list[pygame.event.Event] = []

    def handle_event(self, event: pygame.event.Event) -> None:
        self.events.append(event)


def test_the_sound_button_click_and_key_never_reach_the_screen(tmp_path):
    real_app = App(save=SaveData(FileBackend(tmp_path / "save.json")))
    recorder = EventRecorder(real_app)
    real_app.screen = recorder
    speaker_click = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, pos=real_app.sound_button.rect.center, button=1
    )
    other_key = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_h)

    real_app.step([speaker_click, other_key], 1 / 60)
    press_m(real_app)

    assert recorder.events == [other_key]
    assert not real_app.audio.muted  # muted by the click, unmuted by M
