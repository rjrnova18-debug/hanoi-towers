"""Entry point of the game. pygbag (the web build tool) requires this exact file name."""

import asyncio

from hanoi.game.app import run

asyncio.run(run())
