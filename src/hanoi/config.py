"""All the game's constants in one place: window, board measures, colors and speeds.

To change how the game looks or feels, edit this file, not the drawing code.
Sizes are in "logical pixels": the drawing always assumes a 960 x 540 screen.
"""

WINDOW_TITLE = "Tower of Hanoi"

# Logical resolution. pygame.SCALED stretches it to fit any window or phone screen,
# so the drawing code can always assume this exact size.
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 540
FPS = 60

# --- Game options -----------------------------------------------------------------

MIN_DISKS = 3
MAX_DISKS = 8

# --- Board measures ------------------------------------------------------------------

BOARD_TOP = 90  # everything above is the score bar
BOARD_BOTTOM = 455  # everything below is the button bar
BASE_Y = 430  # the top edge of the base the towers stand on
BASE_HEIGHT = 12
PEG_WIDTH = 10
PEG_HEIGHT = 265
DISK_HEIGHT = 28
DISK_GAP = 3  # visible space between stacked disks
DISK_MIN_WIDTH = 64
DISK_MAX_WIDTH = 290
LIFT_Y = 140  # height where a picked-up disk floats
HINT_ARROW_Y = 112  # height of the hint arrow, between the score bar and a lifted disk

# --- Colors (R, G, B) ----------------------------------------------------------------

BACKGROUND_COLOR = (24, 26, 38)
PANEL_COLOR = (36, 39, 56)
PEG_COLOR = (70, 75, 100)
TEXT_COLOR = (230, 232, 240)
MUTED_TEXT_COLOR = (140, 145, 170)
ACCENT_COLOR = (84, 160, 255)
ERROR_COLOR = (235, 77, 75)
STAR_ON_COLOR = (254, 202, 87)
STAR_OFF_COLOR = (60, 64, 85)
BUTTON_COLOR = (50, 54, 76)
BUTTON_HOVER_COLOR = (66, 71, 99)
HINT_COLOR = (240, 242, 255)  # white: it must stand out from every disk color

# One color per disk size, smallest first: a rainbow from red to pink.
DISK_COLORS = [
    (255, 107, 107),  # red
    (255, 159, 67),  # orange
    (254, 202, 87),  # yellow
    (29, 209, 161),  # green
    (72, 219, 251),  # cyan
    (84, 160, 255),  # blue
    (162, 155, 254),  # violet
    (243, 104, 224),  # pink
]

# --- Animation ---------------------------------------------------------------------

FLIGHT_SPEED = 2200  # pixels per second for a disk flying to its tower
SHAKE_DURATION = 0.35  # seconds a disk shakes after an illegal move
SHAKE_AMPLITUDE = 9  # pixels
DRAG_THRESHOLD = 6  # pixels the pointer must travel before a click becomes a drag
WIN_DELAY = 0.5  # seconds to admire the solved board before the win screen
