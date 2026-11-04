"""stdlib-ast symbol lookup — a deterministic walk, not grep-guessing."""
from __future__ import annotations

import ast
from pathlib import Path


def defined_symbols(file_path) -> set:
    """Return every function/class/module-level-variable name defined in `file_path`.

    Nested defs are qualified with their enclosing class, e.g. 'Foo.bar'.
    Functions nested inside other functions are not surfaced since they are
    not part of the module's importable public surface.
    Returns an empty set if the file is missing or does not parse.
    """
    path = Path(file_path)
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, OSError, UnicodeDecodeError):
        return set()

    names = set()

    def visit(node, prefix=""):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                qualified = f"{prefix}{child.name}"
                names.add(qualified)
                if isinstance(child, ast.ClassDef):
                    visit(child, prefix=f"{qualified}.")
            elif isinstance(child, (ast.Assign, ast.AnnAssign)) and prefix == "":
                targets = child.targets if isinstance(child, ast.Assign) else [child.target]
                for target in targets:
                    if isinstance(target, ast.Name):
                        names.add(target.id)

    visit(tree)
    return names


def has_symbol(build_dir, spec: str) -> bool:
    """`spec` is 'relative/path.py::symbol_name', relative to `build_dir`."""
    rel_path, sep, symbol = spec.partition("::")
    if not sep:
        return False
    full_path = Path(build_dir) / rel_path
    if not full_path.is_file():
        return False
    return symbol in defined_symbols(full_path)
