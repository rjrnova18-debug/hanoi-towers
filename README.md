# Tower of Hanoi

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

## License

[MIT](LICENSE)
