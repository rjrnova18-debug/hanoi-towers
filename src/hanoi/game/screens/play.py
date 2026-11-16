"""The game itself: score bar, board, buttons and the controls.

Every way of playing ends in the same two actions, pick_up(tower) and drop_on(tower):
- click a tower, then another one (or press 1/2/3 twice);
- drag a disk with the mouse or a finger and release it over a tower.
"""

import math
from dataclasses import dataclass

import pygame

from hanoi import config
from hanoi.game.animations import Point
from hanoi.game.audio import Sound
from hanoi.game.board_view import (
    draw_board,
    draw_disk,
    draw_hint,
    draw_target_glow,
    lifted_center,
    resting_center,
    tower_at,
)
from hanoi.game.disk_motion import DiskMotion
from hanoi.game.screens.base import AppServices, Screen
from hanoi.game.widgets import (
    WHITE,
    Button,
    blend,
    button_row_centers,
    draw_background,
    draw_text,
    format_time,
)
from hanoi.logic.rules import TOWER_NAMES, Move, minimum_moves
from hanoi.logic.session import GameSession

TOWER_KEYS = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2}
BUTTON_ROW_Y = 500
SCORE_BAR_HEIGHT = 76


@dataclass
class HeldDisk:
    """The disk the player picked up and has not dropped yet."""

    disk: int
    from_tower: int
    press_point: Point | None = None  # where the mouse went down (None once released)
    pointer: Point | None = None  # where the disk is being dragged (None = floating)


class PlayScreen(Screen):
    def __init__(self, app: AppServices, disk_count: int) -> None:
        super().__init__(app)
        self.session = GameSession(disk_count)
        self.held: HeldDisk | None = None
        self.motion = DiskMotion(disk_count)  # the disk that flies, shakes or bounces
        self.hint: Move | None = None  # the suggested move, shown until the board changes
        self.moves_to_autoplay: list[Move] = []  # filled by Solve; played one per flight
        self.autoplay_pause = 0.0
        self.win_countdown = config.WIN_DELAY  # a short pause to see the solved board

        centers = button_row_centers(5, BUTTON_ROW_Y)
        self.hint_button = Button("Hint (H)", centers[0], key=pygame.K_h)
        self.solve_button = Button("Solve (S)", centers[1], key=pygame.K_s)
        self.undo_button = Button("Undo (U)", centers[2], key=pygame.K_u)
        self.restart_button = Button("Restart (R)", centers[3], key=pygame.K_r)
        self.menu_button = Button("Menu (Esc)", centers[4], key=pygame.K_ESCAPE)
        self.buttons = [
            self.hint_button,
            self.solve_button,
            self.undo_button,
            self.restart_button,
            self.menu_button,
        ]

    @property
    def disk_count(self) -> int:
        return self.session.disk_count

    @property
    def is_solving(self) -> bool:
        """True while the computer is playing the solution."""
        return bool(self.moves_to_autoplay)

    # --- Input -------------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._handle_always_available(event):
            return
        if self.motion.is_flying or self.is_solving:
            return  # wait: a disk is flying, or the computer is playing
        if self.hint_button.is_pressed(event):
            self._show_hint()
        elif self.solve_button.is_pressed(event):
            self._start_solving()
        elif self.undo_button.is_pressed(event):
            self._undo()
        else:
            self._handle_board_input(event)

    def _handle_always_available(self, event: pygame.event.Event) -> bool:
        """Esc, Menu, Restart and Stop work at any moment. Returns True if the event was used."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and self.held:
            self.held = None  # Esc first puts the disk down; a second Esc opens the menu
        elif self.menu_button.is_pressed(event):
            self.app.show_menu()
        elif self.restart_button.is_pressed(event):
            self.app.start_game(self.disk_count)
        elif self.is_solving and self.solve_button.is_pressed(event):
            self.moves_to_autoplay = []  # Stop: the player takes over from here
        else:
            return False
        return True

    def _handle_board_input(self, event: pygame.event.Event) -> None:
        """Keys 1/2/3 and the mouse (or a finger) on the towers."""
        if event.type == pygame.KEYDOWN and event.key in TOWER_KEYS:
            self._select(TOWER_KEYS[event.key])
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._press(event.pos)
        elif event.type == pygame.MOUSEMOTION:
            self._drag(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._release(event.pos)

    def _select(self, tower: int) -> None:
        """A click or a key on a tower: pick up from it, or drop onto it."""
        if self.held is None:
            self.pick_up(tower)
        else:
            self.drop_on(tower)

    def _press(self, point: Point) -> None:
        tower = tower_at(point)
        if tower is None:
            return
        self._select(tower)
        if self.held is not None:
            self.held.press_point = point  # this press may turn into a drag

    def _drag(self, point: Point) -> None:
        held = self.held
        if held is None or held.press_point is None:
            return  # the mouse button is not down: nothing is being dragged
        if held.pointer is not None or math.dist(point, held.press_point) > config.DRAG_THRESHOLD:
            held.pointer = point

    def _release(self, point: Point) -> None:
        held = self.held
        if held is None:
            return
        if held.pointer is not None:
            self.drop_on(tower_at(point))  # end of a drag
        else:
            held.press_point = None  # it was a simple click: wait for the second click

    # --- The two actions ---------------------------------------------------------------

    def pick_up(self, tower: int) -> None:
        disk = self.session.towers.top_disk(tower)
        if disk is not None and not self.session.is_solved():
            self.held = HeldDisk(disk, tower)
            self.app.audio.play(Sound.PICK)

    def drop_on(self, tower: int | None) -> None:
        """Try to move the held disk onto `tower`. None or its own tower puts it back."""
        held = self.held
        if held is None:
            return
        self.held = None
        start = held.pointer or lifted_center(held.from_tower)

        if tower is None or tower == held.from_tower:
            self._fly(held.disk, start)  # put it back where it was
        elif self.session.make_move(Move(held.from_tower, tower)):
            self.hint = None  # the board changed: the old hint no longer applies
            self._fly(held.disk, start)  # to its new tower
        else:
            self.motion.shake(held.disk)  # illegal: it snaps back and shakes
            self.app.audio.play(Sound.ERROR)

    def _undo(self) -> None:
        self.held = None
        before = self.session.towers.position()
        undo_move = self.session.undo()
        if undo_move is not None:
            self.hint = None
            disk = self.session.towers.top_disk(undo_move.target)
            self._fly(disk, resting_center(before, disk, self.disk_count))

    def _show_hint(self) -> None:
        """Ask the solver for the best move. The session marks the game as assisted."""
        self.held = None
        self.hint = self.session.hint()

    def legal_targets(self) -> list[int]:
        """Towers where the held disk is allowed to go (they glow while it is held)."""
        if self.held is None:
            return []
        moves = [Move(self.held.from_tower, tower) for tower in range(len(TOWER_NAMES))]
        return [move.target for move in moves if self.session.towers.can_move(move)]

    def _start_solving(self) -> None:
        """Ask the solver for every remaining move; update() plays them one by one."""
        self.held = None
        self.hint = None
        self.moves_to_autoplay = self.session.solution()

    def _play_next_autoplay_move(self, dt: float) -> None:
        self.autoplay_pause -= dt
        if self.autoplay_pause > 0:
            return
        move = self.moves_to_autoplay.pop(0)
        disk = self.session.towers.top_disk(move.source)
        start = resting_center(self.session.towers.position(), disk, self.disk_count)
        self.session.make_move(move)
        # The solver is fast: no hop on landing, to keep its rhythm.
        self._fly(disk, start, speed=self._autoplay_speed(), bounce=False)
        self.autoplay_pause = config.SOLVE_PAUSE

    def _autoplay_speed(self) -> float:
        extra_disks = self.disk_count - config.MIN_DISKS
        return config.FLIGHT_SPEED * (1 + config.SOLVE_SPEEDUP_PER_DISK * extra_disks)

    def _fly(
        self, disk: int, start: Point, speed: float = config.FLIGHT_SPEED, bounce: bool = True
    ) -> None:
        """Animate `disk` from `start` to wherever it rests on the board now."""
        self.motion.fly(disk, start, self.session.towers.position(), speed, bounce)

    # --- Time ----------------------------------------------------------------------------

    def update(self, dt: float) -> None:
        # Every flight lands here: a move, a disk put back, an undo or a solver move.
        if self.motion.update(dt) is not None:
            self.app.audio.play(Sound.DROP)
        if self.is_solving and not self.motion.is_flying:
            self._play_next_autoplay_move(dt)
        if self.session.is_solved() and not self.motion.is_flying:
            self._count_down_to_win_screen(dt)

    def _count_down_to_win_screen(self, dt: float) -> None:
        was_waiting = self.win_countdown > 0
        self.win_countdown -= dt
        if was_waiting and self.win_countdown <= 0:  # only once
            self.app.show_win(self.session)

    # --- Drawing -------------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        position = self.session.towers.position()
        draw_background(surface)
        self._draw_score_bar(surface)
        if self.held is not None:
            for tower in self.legal_targets():
                draw_target_glow(surface, tower)
        # At most one disk is out of its stack. The one in the player's hand wins over an
        # animation (e.g. picking a disk up while the last one still bounces).
        held = self.held
        moving_disk = held.disk if held is not None else self.motion.disk
        draw_board(
            surface,
            position,
            self.disk_count,
            hidden_disk=moving_disk,
            label_font=self.app.fonts.small,
        )
        if self.hint is not None and not self.motion.is_flying:
            draw_hint(surface, self.hint, position, self.disk_count)
        if held is not None:
            center = held.pointer or lifted_center(held.from_tower)
            draw_disk(surface, held.disk, self.disk_count, center)
        else:
            self.motion.draw(surface, position)
        # The label follows the state, so it can never be out of date.
        self.solve_button.label = "Stop (S)" if self.is_solving else "Solve (S)"
        for button in self.buttons:
            button.draw(surface, self.app.fonts.normal)

    def _draw_score_bar(self, surface: pygame.Surface) -> None:
        fonts = self.app.fonts
        muted = config.MUTED_TEXT_COLOR
        bar = pygame.Rect(0, 0, config.SCREEN_WIDTH, SCORE_BAR_HEIGHT)
        pygame.draw.rect(surface, config.PANEL_COLOR, bar)
        edge_color = blend(config.PANEL_COLOR, WHITE, 0.08)  # a thin line separates bar and board
        pygame.draw.line(surface, edge_color, bar.bottomleft, bar.bottomright)

        draw_text(surface, f"{self.disk_count} disks", fonts.normal, (110, 28))
        if self.session.assisted:
            draw_text(surface, "assisted: no record", fonts.small, (110, 54), config.ACCENT_COLOR)
        else:
            draw_text(surface, self._best_text(), fonts.small, (110, 54), muted)

        draw_text(surface, f"Moves {self.session.move_count}", fonts.large, (480, 28))
        minimum = f"minimum {minimum_moves(self.disk_count)}"
        draw_text(surface, minimum, fonts.small, (480, 58), muted)

        draw_text(surface, format_time(self.session.elapsed_seconds()), fonts.large, (850, 28))
        draw_text(surface, "time", fonts.small, (850, 58), muted)

    def _best_text(self) -> str:
        record = self.app.save.best_record(self.disk_count)
        if record is None:
            return "best: -"
        return f"best: {record.moves} · {format_time(record.seconds)}"
