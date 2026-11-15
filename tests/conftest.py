"""Shared test setup.

The tests of game/ use pygame, but they must run where there is no screen or sound card
(like the GitHub Actions runner). SDL's "dummy" drivers make pygame work without either.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
