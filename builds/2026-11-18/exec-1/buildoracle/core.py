"""Core engine: record, classify-then-refuse, canonicalize, verify.

Everything is stdlib. No network, no subprocess, no secrets.
"""

import ast
import importlib.util
import sys
from pathlib import Path

NONDET_MODULES = {"time", "random", "datetime", "socket", "os", "uuid", "secrets"}


def canonicalize(value):
    """Normalize a value before comparison: sorted dict keys, rounded
    floats, whitespace-normalized strings, order-insensitive sets."""
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        return round(value, 9)
    if isinstance(value, str):
        return " ".join(value.split())
    if isinstance(value, dict):
        return {k: canonicalize(value[k]) for k in sorted(value.keys(), key=str)}
    if isinstance(value, (list, tuple)):
        return [canonicalize(v) for v in value]
    if isinstance(value, set):
        return sorted((canonicalize(v) for v in value), key=str)
    return value


def load_module(path):
    """Import a target module fresh from a file path, bypassing sys.modules
    caching so repeated loads start from a clean global state."""
    resolved = str(Path(path).resolve())
    mod_name = f"_buildoracle_target_{abs(hash(resolved))}_{id(object())}"
    spec = importlib.util.spec_from_file_location(mod_name, resolved)
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        del sys.modules[mod_name]
    return module


def _call(module, func_name, args, kwargs):
    func = getattr(module, func_name)
    try:
        value = func(*args, **kwargs)
        return {"ok": True, "value": value}
    except Exception as e:  # the target's own exceptions are part of its behavior
        return {"ok": False, "exception": type(e).__name__, "message": str(e)}


def canonical_result(result):
    if result["ok"]:
        return {"ok": True, "value": canonicalize(result["value"])}
    return {"ok": False, "exception": result["exception"], "message": canonicalize(result["message"])}


def canonical_event(event):
    return {
        "func": event["func"],
        "args": canonicalize(event["args"]),
        "kwargs": canonicalize(event["kwargs"]),
        "result": canonical_result(event["result"]),
    }


def run_exercise(module_path, exercise_path):
    """Drive module_path through every (func, args, kwargs) in
    exercise_path's INPUTS list; return the raw (uncanonicalized) trace."""
    module = load_module(module_path)
    exercise = load_module(exercise_path)
    trace = []
    for func_name, args, kwargs in exercise.INPUTS:
        result = _call(module, func_name, list(args), dict(kwargs))
        trace.append({"func": func_name, "args": list(args), "kwargs": dict(kwargs), "result": result})
    return trace


def record(module_path, exercise_path, out_path=None):
    trace = run_exercise(module_path, exercise_path)
    if out_path:
        import json

        Path(out_path).write_text(json.dumps(trace, indent=2))
    return trace


def static_scan(module_path):
    """AST-inspect module_path for known nondeterminism sources: imports of
    time/random/datetime/socket/os/uuid/secrets, and function bodies that
    read a mutable module-level global. Returns a list of (reason, lineno)."""
    source = Path(module_path).read_text()
    tree = ast.parse(source, filename=str(module_path))
    findings = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top in NONDET_MODULES:
                    findings.append((f"imports '{alias.name}'", node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] in NONDET_MODULES:
                findings.append((f"imports from '{node.module}'", node.lineno))

    mutable_globals = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and isinstance(node.value, (ast.List, ast.Dict, ast.Set)):
                    mutable_globals.add(target.id)
    if mutable_globals:
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for inner in ast.walk(node):
                    if (
                        isinstance(inner, ast.Name)
                        and inner.id in mutable_globals
                        and isinstance(inner.ctx, ast.Load)
                    ):
                        findings.append((f"reads mutable module-level global '{inner.id}'", inner.lineno))

    return findings


def classify(module_path, exercise_path):
    """GATEABLE or REFUSE, using both the static scan and an empirical
    double-run trace comparison (catches nondeterminism that enters
    transitively through a called library, which the static scan misses)."""
    findings = static_scan(module_path)
    if findings:
        reason, line = findings[0]
        return {"verdict": "REFUSE", "reason": reason, "line": line}

    trace_a = [canonical_event(e) for e in run_exercise(module_path, exercise_path)]
    trace_b = [canonical_event(e) for e in run_exercise(module_path, exercise_path)]
    if trace_a != trace_b:
        return {
            "verdict": "REFUSE",
            "reason": "double-run divergence: two runs of the exercise produced different traces (empirical nondeterminism)",
            "line": None,
        }

    return {"verdict": "GATEABLE"}


def verify(trace, module_path):
    """Replay a recorded trace against module_path. Re-checks gateability
    of module_path itself (static scan + a double-run of the trace) before
    trusting the comparison, so verify can REFUSE on its own, not just PASS/FAIL."""
    findings = static_scan(module_path)
    if findings:
        reason, line = findings[0]
        return {"verdict": "REFUSE", "reason": reason, "line": line}

    module_a = load_module(module_path)
    actual_a = [_call(module_a, e["func"], e["args"], e["kwargs"]) for e in trace]

    module_b = load_module(module_path)
    actual_b = [_call(module_b, e["func"], e["args"], e["kwargs"]) for e in trace]

    canon_a = [canonical_result(r) for r in actual_a]
    canon_b = [canonical_result(r) for r in actual_b]
    if canon_a != canon_b:
        return {
            "verdict": "REFUSE",
            "reason": "double-run divergence: replaying the trace twice against this module produced different results (empirical nondeterminism)",
            "line": None,
        }

    for event, actual_canon in zip(trace, canon_a):
        expected_canon = canonical_result(event["result"])
        if actual_canon != expected_canon:
            return {
                "verdict": "FAIL",
                "func": event["func"],
                "args": event["args"],
                "kwargs": event["kwargs"],
                "expected": expected_canon,
                "actual": actual_canon,
            }

    return {"verdict": "PASS"}
