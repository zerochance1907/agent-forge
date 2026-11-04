"""stdlib ast-based symbol presence checks. No grep-guessing."""

import ast
import os


def _collect_names(tree):
    """Collect every def/class/assignment name reachable in the module, at any depth."""
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def symbol_exists(build_dir, symbol_ref):
    """symbol_ref is 'relative/path.py::name'. Returns True/False/None (file missing)."""
    rel_path, _, name = symbol_ref.partition("::")
    full_path = os.path.join(build_dir, rel_path)
    if not os.path.isfile(full_path):
        return None
    try:
        with open(full_path, "r", encoding="utf-8") as fh:
            source = fh.read()
        tree = ast.parse(source, filename=full_path)
    except (SyntaxError, OSError):
        return False
    return name in _collect_names(tree)
