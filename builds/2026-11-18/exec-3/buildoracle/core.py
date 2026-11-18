"""Core engine: record, classify-then-refuse, canonicalize, verify.

Pure stdlib. Loads target modules by file path (importlib), never by import
statement, so BuildOracle can gate arbitrary agent-written files without them
being on sys.path or part of any package.
"""

import ast
import importlib.util
import itertools
from pathlib import Path

_NONDETERMINISTIC_MODULES = {
    "time", "random", "datetime", "socket", "os", "uuid", "secrets",
}

_module_counter = itertools.count()

CASES_DIR = Path(__file__).parent / "cases"


# ---------------------------------------------------------------------------
# canonicalize — mandatory core, every comparison in the tool runs through it
# ---------------------------------------------------------------------------

def canonicalize(value, float_precision=9):
    """Normalize a value so structurally-equal-but-differently-shaped data compares equal.

    - dict: recursively canonicalized, then represented as a key-sorted tuple
      of pairs (NOT a dict) — this is the part that actually matters, because
      Python's own dict == already ignores insertion order, but repr()/json
      dumps without sort_keys do not, and a careless gate that compares those
      would wrongly FAIL on a pure key-reorder refactor. Converting to a
      sorted tuple makes order-insensitivity structural rather than borrowed
      from dict.__eq__.
    - set/frozenset: canonicalized then sorted by repr (sets have no order).
    - list/tuple: order preserved (it is semantically significant), elements
      canonicalized.
    - float: rounded to `float_precision` so refactors that merely reorder
      floating point arithmetic (e.g. (x*3)/3 vs x*1.0) don't register as
      divergence.
    - str: internal whitespace runs collapsed to single spaces, stripped.
    - everything else: returned as-is.
    """
    if isinstance(value, float):
        return round(value, float_precision)
    if isinstance(value, dict):
        pairs = tuple(
            sorted(
                ((k, canonicalize(v, float_precision)) for k, v in value.items()),
                key=lambda kv: repr(kv[0]),
            )
        )
        return ("__canon_dict__", pairs)
    if isinstance(value, (set, frozenset)):
        items = sorted((canonicalize(v, float_precision) for v in value), key=repr)
        return ("__canon_set__", tuple(items))
    if isinstance(value, (list, tuple)):
        return [canonicalize(v, float_precision) for v in value]
    if isinstance(value, str):
        return " ".join(value.split())
    return value


# ---------------------------------------------------------------------------
# module loading
# ---------------------------------------------------------------------------

def load_module(path):
    path = Path(path)
    name = f"_buildoracle_target_{next(_module_counter)}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_exercise(path):
    return load_module(path)


# ---------------------------------------------------------------------------
# record — capture (input, return_value, raised_exception) events
# ---------------------------------------------------------------------------

def _call(func, inp):
    try:
        return {"output": func(inp), "exception": None}
    except Exception as e:  # noqa: BLE001 - we deliberately capture any exception as data
        return {"output": None, "exception": {"type": type(e).__name__, "msg": str(e)}}


def record(module_path, exercise_path):
    module = load_module(module_path)
    exercise = load_exercise(exercise_path)
    func = getattr(module, exercise.FUNC)
    events = []
    for inp in exercise.INPUTS:
        result = _call(func, inp)
        events.append({"input": inp, **result})
    return {"func": exercise.FUNC, "events": events}


# ---------------------------------------------------------------------------
# classify-then-refuse — static AST scan + empirical double-run
# ---------------------------------------------------------------------------

def static_scan(module_path):
    """AST-inspect a module for known nondeterminism sources.

    Returns (reason, lineno) or (None, None) if nothing suspicious was found.
    Catches: imports of time/random/datetime/socket/os/uuid/secrets, and any
    function that declares `global` (reads or writes module-level mutable
    state across calls).
    """
    source = Path(module_path).read_text()
    tree = ast.parse(source, filename=str(module_path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top in _NONDETERMINISTIC_MODULES:
                    return f"imports {alias.name}", node.lineno
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                top = node.module.split(".")[0]
                if top in _NONDETERMINISTIC_MODULES:
                    return f"imports from {node.module}", node.lineno
        elif isinstance(node, ast.Global):
            names = ", ".join(node.names)
            return f"reads/writes module-level global state ({names})", node.lineno
    return None, None


def double_run(module_path, exercise_path, first_trace=None):
    """Run the exercise twice against the module and compare canonicalized traces.

    Catches nondeterminism that enters transitively through a called library
    (or through plain Python builtins like id()/object identity) which the
    static scan has no way to see. Returns True if the two runs agree.
    """
    trace1 = first_trace if first_trace is not None else record(module_path, exercise_path)
    trace2 = record(module_path, exercise_path)
    return canonicalize(trace1) == canonicalize(trace2), trace1, trace2


def classify(module_path, exercise_path, first_trace=None):
    """Decide whether `module_path` is safely gateable. Refuses honestly if not."""
    reason, line = static_scan(module_path)
    if reason:
        return {"verdict": "REFUSE", "reason": reason, "line": line, "signal": "static"}
    agree, trace1, trace2 = double_run(module_path, exercise_path, first_trace=first_trace)
    if not agree:
        return {
            "verdict": "REFUSE",
            "reason": "empirical double-run produced divergent traces — nondeterministic via transitive behavior, no static import caught it",
            "line": None,
            "signal": "empirical",
            "trace1": trace1,
            "trace2": trace2,
        }
    return {"verdict": "GATEABLE", "reason": None, "line": None, "signal": None}


# ---------------------------------------------------------------------------
# verify — replay a recorded trace against a (possibly refactored) module
# ---------------------------------------------------------------------------

def verify(trace, module_path):
    """Replay a recorded trace against (the possibly-refactored) module_path.

    Before trusting the replay, verify refuses to gate a module that turns
    out to be nondeterministic itself: a static scan, then a double-replay
    of the exact same recorded inputs (if the refactor's own output isn't
    stable across two replays of identical inputs, a PASS/FAIL verdict would
    be a coin flip). This is what makes the REFUSE exit code (20) real rather
    than theoretical — a refactor that introduces e.g. `time.time()` is
    caught here even though the *original* module was perfectly deterministic.
    """
    reason, line = static_scan(module_path)
    if reason:
        return {"verdict": "REFUSE", "reason": reason, "line": line}

    module = load_module(module_path)
    func = getattr(module, trace["func"])

    def replay_once():
        return [_call(func, entry["input"]) for entry in trace["events"]]

    replay1 = replay_once()
    replay2 = replay_once()
    if canonicalize(replay1) != canonicalize(replay2):
        return {
            "verdict": "REFUSE",
            "reason": "empirical: replaying the refactored module against the same recorded inputs twice produced divergent results",
            "line": None,
        }

    for entry, got in zip(trace["events"], replay1):
        expected_canon = canonicalize({"output": entry["output"], "exception": entry["exception"]})
        got_canon = canonicalize({"output": got["output"], "exception": got["exception"]})
        if expected_canon != got_canon:
            return {
                "verdict": "FAIL",
                "input": entry["input"],
                "expected": {"output": entry["output"], "exception": entry["exception"]},
                "got": {"output": got["output"], "exception": got["exception"]},
            }
    return {"verdict": "PASS"}


# ---------------------------------------------------------------------------
# Head A — the end-to-end refactor gate run by `gate` and `demo`
# ---------------------------------------------------------------------------

COVERAGE_LINE = "coverage: recorded trace + existing tests only — unexercised paths not gated"


def run_case(case_name):
    """record the case's original -> classify -> verify its refactor.

    Returns a dict with at least {"verdict": ...} plus whatever diagnostic
    detail was produced along the way, for the CLI/demo to render.
    """
    case_dir = CASES_DIR / case_name
    if not case_dir.is_dir():
        raise ValueError(f"unknown case: {case_name}")

    original = case_dir / "original.py"
    refactored = case_dir / "refactored.py"
    exercise = case_dir / "exercise.py"

    trace = record(original, exercise)
    classification = classify(original, exercise, first_trace=trace)

    if classification["verdict"] == "REFUSE":
        return {
            "verdict": "REFUSE",
            "classification": classification,
            "coverage": COVERAGE_LINE,
        }

    verify_result = verify(trace, refactored)
    if verify_result["verdict"] == "REFUSE":
        return {
            "verdict": "REFUSE",
            "classification": classification,
            "verify_refuse": verify_result,
            "coverage": COVERAGE_LINE,
        }
    return {
        "verdict": verify_result["verdict"],
        "classification": classification,
        "verify": verify_result,
        "trace": trace,
        "coverage": COVERAGE_LINE,
    }


BUNDLED_CASES = ["identity", "offbyone", "nondeterministic", "keyorder"]
