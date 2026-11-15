"""Guards the main design rule: logic/ never depends on pygame or on game/.

If this test fails, someone mixed drawing code into the game's brain.
"""

import ast
from pathlib import Path

LOGIC_DIR = Path(__file__).parent.parent / "src" / "hanoi" / "logic"
FORBIDDEN_PREFIXES = ("pygame", "hanoi.game")


def imported_modules(path: Path) -> set[str]:
    """Return the full name of every module imported by a Python file."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_logic_does_not_import_pygame_or_game():
    logic_files = list(LOGIC_DIR.glob("*.py"))
    assert logic_files, "logic/ folder not found"

    for file in logic_files:
        for module in imported_modules(file):
            assert not module.startswith(FORBIDDEN_PREFIXES), (
                f"{file.name} imports {module}; logic/ must stay pure Python"
            )
