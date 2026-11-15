"""The game itself: score bar, board, buttons and the controls.

Every way of playing ends in the same two actions, pick_up(tower) and drop_on(tower):
- click a tower, then another one (or press 1/2/3 twice);
- drag a disk with the mouse or a finger and release it over a tower.
"""

import math
from dataclasses import dataclass

import pygame

from hanoi import config
from hanoi.game.animations import Flight, Point, Shake
from hanoi.game.board_view import draw_board, draw_disk, lifted_center, resting_center, tower_at
from hanoi.game.screens.base import AppServices, Screen
from hanoi.game.widgets import Button, draw_text, format_time
from hanoi.logic.rules import Move, minimum_moves
from hanoi.logic.session import GameSession

TOWER_KEYS = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2}
BUTTON_ROW_Y = 500


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
        self.flight: Flight | None = None
        self.shake: Shake | None = None
        self.win_countdown = config.WIN_DELAY  # a short pause to see the solved board
        self.undo_button = Button("Undo (U)", (300, BUTTON_ROW_Y), key=pygame.K_u)
        self.restart_button = Button("Restart (R)", (480, BUTTON_ROW_Y), key=pygame.K_r)
        self.menu_button = Button("Menu (Esc)", (660, BUTTON_ROW_Y), key=pygame.K_ESCAPE)

    @property
    def disk_count(self) -> int:
        return self.session.disk_count

    # --- Input -------------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and self.held:
            self.held = None  # Esc first puts the disk down; a second Esc opens the menu
        elif self.menu_button.is_pressed(event):
            self.app.show_menu()
        elif self.restart_button.is_pressed(event):
            self.app.start_game(self.disk_count)
        elif self.flight is not None:
            return  # wait until the flying disk lands
        elif self.undo_button.is_pressed(event):
            self._undo()
        elif event.type == pygame.KEYDOWN and event.key in TOWER_KEYS:
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
            self._fly(held.disk, start)  # to its new tower
        else:
            self.shake = Shake(held.disk)  # illegal: it snaps back and shakes

    def _undo(self) -> None:
        self.held = None
        before = self.session.towers.position()
        undo_move = self.session.undo()
        if undo_move is not None:
            disk = self.session.towers.top_disk(undo_move.target)
            self._fly(disk, resting_center(before, disk, self.disk_count))

    def _fly(self, disk: int, start: Point) -> None:
        """Animate `disk` from `start` to wherever it rests on the board now."""
        end = resting_center(self.session.towers.position(), disk, self.disk_count)
        self.flight = Flight.between(disk, start, end)

    # --- Time ----------------------------------------------------------------------------

    def update(self, dt: float) -> None:
        if self.flight is not None:
            self.flight.update(dt)
            if self.flight.done:
                self.flight = None
        if self.shake is not None:
            self.shake.update(dt)
            if self.shake.done:
                self.shake = None
        if self.session.is_solved() and self.flight is None:
            self._count_down_to_win_screen(dt)

    def _count_down_to_win_screen(self, dt: float) -> None:
        was_waiting = self.win_countdown > 0
        self.win_countdown -= dt
        if was_waiting and self.win_countdown <= 0:  # only once
            self.app.show_win(self.session)

    # --- Drawing -------------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(config.BACKGROUND_COLOR)
        self._draw_score_bar(surface)
        draw_board(
            surface,
            self.session.towers.position(),
            self.disk_count,
            hidden_disk=self._moving_disk(),
            label_font=self.app.fonts.small,
        )
        self._draw_moving_disk(surface)
        for button in (self.undo_button, self.restart_button, self.menu_button):
            button.draw(surface, self.app.fonts.normal)

    def _moving_disk(self) -> int | None:
        """The disk that is not resting in its stack right now (the board skips it)."""
        if self.flight is not None:
            return self.flight.disk
        if self.held is not None:
            return self.held.disk
        if self.shake is not None:
            return self.shake.disk
        return None

    def _draw_moving_disk(self, surface: pygame.Surface) -> None:
        if self.flight is not None:
            draw_disk(surface, self.flight.disk, self.disk_count, self.flight.position())
        elif self.held is not None:
            center = self.held.pointer or lifted_center(self.held.from_tower)
            draw_disk(surface, self.held.disk, self.disk_count, center)
        elif self.shake is not None:
            x, y = resting_center(self.session.towers.position(), self.shake.disk, self.disk_count)
            center = (x + self.shake.offset_x(), y)
            draw_disk(surface, self.shake.disk, self.disk_count, center, config.ERROR_COLOR)

    def _draw_score_bar(self, surface: pygame.Surface) -> None:
        fonts = self.app.fonts
        muted = config.MUTED_TEXT_COLOR
        pygame.draw.rect(surface, config.PANEL_COLOR, (0, 0, config.SCREEN_WIDTH, 76))

        draw_text(surface, f"{self.disk_count} disks", fonts.normal, (110, 28))
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
