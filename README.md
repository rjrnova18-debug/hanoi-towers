# Tower of Hanoi

[![CI](https://github.com/rjrnova18-debug/hanoi-towers/actions/workflows/ci.yml/badge.svg)](https://github.com/rjrnova18-debug/hanoi-towers/actions/workflows/ci.yml)

> 🚧 Work in progress.

A Tower of Hanoi game made with **pygame-ce**. It gives hints and solves the puzzle from **any** position, and it will be playable in the browser.

It started as one of my first Python scripts, which had a bug. This repo rewrites it into a tested, playable game. The original script is kept untouched in [`legacy/`](legacy/hanoi_og_code.py).

## Run it

```bash
python -m venv venv
source venv/Scripts/activate      # Windows (Git Bash). On macOS/Linux: source venv/bin/activate
pip install -r requirements-dev.txt
python src/main.py
```

Tests and lint:

```bash
pytest
ruff check . && ruff format --check .
```

## Credits

- **Font:** [Fredoka](https://fonts.google.com/specimen/Fredoka) by The Fredoka Project Authors, under the [SIL Open Font License](src/assets/fonts/OFL.txt).
- **Sound effects:** from [Pixabay](https://pixabay.com/sound-effects/), under the [Pixabay Content License](https://pixabay.com/service/license-summary/). Trimmed and converted to OGG for this game.

## License

The code is [MIT](LICENSE). The font and the sound effects keep their own licenses (see Credits).
