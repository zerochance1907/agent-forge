"""Core engine: record, classify-then-refuse, canonicalize, verify.

Target-module contract: any Python module passed to this tool must expose a
top-level callable ``run(x)``. An exercise script is any Python module that
exposes a top-level ``INPUTS`` list — each element is passed to ``run`` in
order.

Everything here is stdlib-only, offline, and does not shell out to the
network. The only "untrusted" code executed is the target module/exercise the
caller points us at, which is the whole point of the tool.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import uuid
from pathlib import Path
from typing import Any

# Modules whose mere import signals nondeterminism (direct clock, randomness,
# I/O, identity sources). Transitively-nondeterministic modules that don't
# import any of these are still caught by the empirical double-run in
# classify().
NONDETERMINISTIC_IMPORTS = {
    "time",
    "random",
    "datetime",
    "socket",
    "os",
    "uuid",
    "secrets",
}

COVERAGE_LINE = (
    "coverage: recorded trace + existing tests only — "
    "unexercised paths not gated"
)


class LoadError(RuntimeError):
    """Raised when a target module or exercise script can't be loaded."""


def _import_fresh(path: str | Path):
    """Import a Python file as a throwaway module.

    Each call gets a unique module name so re-importing the same path twice
    (as classify's double-run does implicitly via two calls against one
    loaded instance, or gate's record-then-verify does across two distinct
    files) never hits a stale ``sys.modules`` entry.
    """
    path = Path(path)
    if not path.is_file():
        raise LoadError(f"no such file: {path}")
    name = f"_buildoracle_dyn_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise LoadError(f"could not build an import spec for: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "run"):
        raise LoadError(f"{path} does not define a top-level run(x) function")
    return module


def _load_inputs(exercise_path: str | Path) -> list[Any]:
    path = Path(exercise_path)
    if not path.is_file():
        raise LoadError(f"no such file: {path}")
    name = f"_buildoracle_exercise_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise LoadError(f"could not build an import spec for: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "INPUTS"):
        raise LoadError(f"{path} does not define a top-level INPUTS list")
    return list(module.INPUTS)


# ---------------------------------------------------------------------------
# canonicalize — mandatory core, every comparison runs through this.
# ---------------------------------------------------------------------------

FLOAT_PRECISION = 6


def canonicalize(value: Any) -> Any:
    """Normalize a value so structurally-equal-but-cosmetically-different
    values compare equal: dict key order, float rounding noise, string
    whitespace, and set/dict ordering all collapse here.
    """
    if isinstance(value, float):
        return round(value, FLOAT_PRECISION)
    if isinstance(value, dict):
        return {k: canonicalize(v) for k, v in sorted(value.items(), key=lambda kv: kv[0])}
    if isinstance(value, (list, tuple)):
        return [canonicalize(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return sorted((canonicalize(v) for v in value), key=repr)
    if isinstance(value, str):
        return " ".join(value.split())
    return value


def _canon_key(value: Any) -> str:
    """A deterministic string key for a canonicalized value, used to compare
    two events (and to make the double-run / verify comparisons order- and
    type-noise free).
    """
    return json.dumps(canonicalize(value), sort_keys=True, default=repr)


# ---------------------------------------------------------------------------
# record — capture (input, output, exception) triples.
# ---------------------------------------------------------------------------


def _run_one(module, x: Any) -> dict:
    try:
        result = module.run(x)
        return {"input": x, "output": result, "exception": None}
    except Exception as exc:  # noqa: BLE001 - we must capture *any* raise
        return {"input": x, "output": None, "exception": f"{type(exc).__name__}: {exc}"}


def run_exercise(module, inputs: list[Any]) -> list[dict]:
    return [_run_one(module, x) for x in inputs]


def record(module_path: str | Path, exercise_path: str | Path) -> list[dict]:
    """Drive ``module`` with every input in ``exercise`` and return the
    ordered list of (input, output, exception) events.
    """
    module = _import_fresh(module_path)
    inputs = _load_inputs(exercise_path)
    return run_exercise(module, inputs)


def record_to_file(module_path: str | Path, exercise_path: str | Path, out_path: str | Path) -> list[dict]:
    events = record(module_path, exercise_path)
    Path(out_path).write_text(json.dumps(events, indent=2, default=repr))
    return events


# ---------------------------------------------------------------------------
# classify-then-refuse — static AST scan + empirical double-run.
# ---------------------------------------------------------------------------


def static_scan(module_path: str | Path) -> tuple[str | None, int | None]:
    """AST-inspect the module for known nondeterminism sources.

    Returns (reason, line_number) or (None, None) if nothing was found. This
    only catches nondeterminism that is lexically visible in the module
    itself (direct imports, reassigning a module-level global) — nothing
    transitive. That's what the empirical double-run in classify() is for.
    """
    path = Path(module_path)
    source = path.read_text()
    tree = ast.parse(source, filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top in NONDETERMINISTIC_IMPORTS:
                    return f"imports '{top}'", node.lineno
        elif isinstance(node, ast.ImportFrom):
            top = (node.module or "").split(".")[0]
            if top in NONDETERMINISTIC_IMPORTS:
                return f"imports from '{node.module}'", node.lineno
        elif isinstance(node, ast.Global):
            names = ", ".join(node.names)
            return f"reassigns module-level global(s) ({names})", node.lineno
    return None, None


def _events_match(events_a: list[dict], events_b: list[dict]) -> bool:
    if len(events_a) != len(events_b):
        return False
    for a, b in zip(events_a, events_b):
        if _canon_key(a["input"]) != _canon_key(b["input"]):
            return False
        if _canon_key(a["output"]) != _canon_key(b["output"]):
            return False
        if a["exception"] != b["exception"]:
            return False
    return True


def classify(module_path: str | Path, exercise_path: str | Path) -> dict:
    """Decide whether ``module`` is safely gateable.

    Fires on EITHER signal:
      1. static_scan finds a lexical nondeterminism source, or
      2. running the exercise twice against one loaded module instance
         produces two different traces (catches nondeterminism that enters
         transitively through a called library, or through module-level
         mutable state the static scan can't see).
    """
    reason, line = static_scan(module_path)
    if reason is not None:
        return {"verdict": "REFUSE", "reason": reason, "line": line, "signal": "static"}

    module = _import_fresh(module_path)
    inputs = _load_inputs(exercise_path)
    first_pass = run_exercise(module, inputs)
    second_pass = run_exercise(module, inputs)
    if not _events_match(first_pass, second_pass):
        return {
            "verdict": "REFUSE",
            "reason": "empirical double-run divergence: module produced different results "
            "for identical inputs across two runs",
            "line": None,
            "signal": "empirical",
        }
    return {"verdict": "GATEABLE", "reason": None, "line": None, "signal": None}


# ---------------------------------------------------------------------------
# verify — the agent-facing gate: replay trace against a (refactored) module.
# ---------------------------------------------------------------------------


def verify(trace_events: list[dict], module_path: str | Path) -> dict:
    """Replay ``trace_events`` against ``module`` and veto any divergence.

    Runs its own static_scan on the module being verified first — if *that*
    module is itself not safely gateable, REFUSE rather than emit a
    pass/fail nobody should trust.
    """
    reason, line = static_scan(module_path)
    if reason is not None:
        return {"verdict": "REFUSE", "reason": reason, "line": line, "input": None}

    module = _import_fresh(module_path)
    for event in trace_events:
        actual = _run_one(module, event["input"])
        if _canon_key(actual["output"]) != _canon_key(event["output"]) or (
            actual["exception"] != event["exception"]
        ):
            return {"verdict": "FAIL", "input": event["input"], "reason": None, "line": None}
    return {"verdict": "PASS", "input": None, "reason": None, "line": None}


def verify_trace_file(trace_path: str | Path, module_path: str | Path) -> dict:
    events = json.loads(Path(trace_path).read_text())
    return verify(events, module_path)


# ---------------------------------------------------------------------------
# gate — bundled, pinned end-to-end cases.
# ---------------------------------------------------------------------------

CASES_DIR = Path(__file__).parent / "cases"
KNOWN_CASES = ("identity", "offbyone", "nondeterministic", "keyorder")


def run_case(case_name: str) -> dict:
    """record the case's original -> classify -> verify its refactor."""
    if case_name not in KNOWN_CASES:
        raise LoadError(f"unknown case: {case_name}")

    case_dir = CASES_DIR / case_name
    original = case_dir / "original.py"
    refactored = case_dir / "refactored.py"
    exercise = case_dir / "exercise.py"

    trace = record(original, exercise)
    verdict = classify(original, exercise)
    if verdict["verdict"] == "REFUSE":
        return {
            "verdict": "REFUSE",
            "reason": verdict["reason"],
            "line": verdict["line"],
            "coverage": COVERAGE_LINE,
        }

    result = verify(trace, refactored)
    return {
        "verdict": result["verdict"],
        "reason": result.get("reason"),
        "line": result.get("line"),
        "diverged_on": result.get("input") if result["verdict"] == "FAIL" else None,
        "coverage": COVERAGE_LINE,
    }
