"""Entry point of the game. pygbag (the web build tool) requires this exact file name."""

import asyncio

# Not used here, but needed for the browser version: before starting, pygbag reads the
# imports of THIS file to know which packages to download. pygame is only imported deeper
# (in hanoi/game/), so without this line the browser would start without it.
import pygame  # noqa: F401

from hanoi.game.app import run

asyncio.run(run())
