"""Unit tests for buildoracle.core.

Covers: canonicalize (dict key-order, float precision, whitespace), the
classify refuse path (both static and empirical signals), and a pass-and-a-
fail through verify. Also exercises the four bundled gate cases end-to-end.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from buildoracle import core

ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# canonicalize
# ---------------------------------------------------------------------------


def test_canonicalize_dict_key_order_insensitive():
    a = {"x": 1, "y": 2, "z": 3}
    b = {"z": 3, "x": 1, "y": 2}
    assert core.canonicalize(a) == core.canonicalize(b)


def test_canonicalize_float_precision_rounding():
    a = 1.0000001
    b = 1.0000002
    assert core.canonicalize(a) == core.canonicalize(b)
    assert core.canonicalize(1.0) != core.canonicalize(1.1)


def test_canonicalize_string_whitespace_normalization():
    a = "hello   world"
    b = "hello world"
    assert core.canonicalize(a) == core.canonicalize(b)
    assert core.canonicalize("  leading and trailing  ") == core.canonicalize("leading and trailing")


def test_canonicalize_nested_structure():
    a = {"items": [{"k": 1, "v": " a  b "}], "n": 2.0000001}
    b = {"n": 2.0000002, "items": [{"v": "a b", "k": 1}]}
    assert core.canonicalize(a) == core.canonicalize(b)


# ---------------------------------------------------------------------------
# classify: refuse path (static signal)
# ---------------------------------------------------------------------------


def test_classify_refuses_on_static_import(tmp_path):
    module = tmp_path / "mod.py"
    module.write_text("import time\n\n\ndef run(x):\n    return time.time() + x\n")
    exercise = tmp_path / "ex.py"
    exercise.write_text("INPUTS = [1, 2, 3]\n")

    verdict = core.classify(module, exercise)
    assert verdict["verdict"] == "REFUSE"
    assert verdict["signal"] == "static"
    assert "time" in verdict["reason"]
    assert verdict["line"] == 1


def test_classify_gateable_for_pure_function(tmp_path):
    module = tmp_path / "mod.py"
    module.write_text("def run(x):\n    return {'y': x * 2}\n")
    exercise = tmp_path / "ex.py"
    exercise.write_text("INPUTS = [1, 2, 3]\n")

    verdict = core.classify(module, exercise)
    assert verdict["verdict"] == "GATEABLE"


# ---------------------------------------------------------------------------
# classify: refuse path (empirical double-run signal) -- nondeterminism that
# enters through module-level mutable state, with NO blocklisted import.
# ---------------------------------------------------------------------------


def test_classify_refuses_on_empirical_divergence(tmp_path):
    module = tmp_path / "mod.py"
    module.write_text(
        "import itertools\n\n"
        "_counter = itertools.count()\n\n\n"
        "def run(x):\n"
        "    return {'x': x, 'call_number': next(_counter)}\n"
    )
    exercise = tmp_path / "ex.py"
    exercise.write_text("INPUTS = [1, 2, 3]\n")

    # Sanity: itertools is not in the static blocklist, so this must slip
    # past static_scan and only be caught by the double-run.
    reason, _ = core.static_scan(module)
    assert reason is None

    verdict = core.classify(module, exercise)
    assert verdict["verdict"] == "REFUSE"
    assert verdict["signal"] == "empirical"


# ---------------------------------------------------------------------------
# verify: pass, fail, refuse
# ---------------------------------------------------------------------------


def test_verify_pass_on_identical_module(tmp_path):
    module = tmp_path / "mod.py"
    module.write_text("def run(x):\n    return {'y': x * 2}\n")
    exercise = tmp_path / "ex.py"
    exercise.write_text("INPUTS = [1, 2, 3]\n")

    trace = core.record(module, exercise)
    result = core.verify(trace, module)
    assert result["verdict"] == "PASS"


def test_verify_fail_names_diverging_input(tmp_path):
    original = tmp_path / "orig.py"
    original.write_text("def run(x):\n    return {'y': x * 2}\n")
    refactored = tmp_path / "refac.py"
    refactored.write_text("def run(x):\n    return {'y': x * 2 + 1}\n")
    exercise = tmp_path / "ex.py"
    exercise.write_text("INPUTS = [1, 2, 3]\n")

    trace = core.record(original, exercise)
    result = core.verify(trace, refactored)
    assert result["verdict"] == "FAIL"
    assert result["input"] == 1  # first input, diverges immediately


def test_verify_refuses_on_nondeterministic_module(tmp_path):
    module = tmp_path / "mod.py"
    module.write_text("import random\n\n\ndef run(x):\n    return random.random() + x\n")
    exercise = tmp_path / "ex.py"
    exercise.write_text("INPUTS = [1]\n")

    trace = core.record(module, exercise)
    result = core.verify(trace, module)
    assert result["verdict"] == "REFUSE"


def test_verify_pass_because_canonicalization_ran(tmp_path):
    """Without canonicalize(), this would FAIL on key order AND whitespace."""
    original = tmp_path / "orig.py"
    original.write_text("def run(x):\n    return {'a': x, 'label': f'item {x}'}\n")
    refactored = tmp_path / "refac.py"
    refactored.write_text(
        "def run(x):\n"
        "    out = {}\n"
        "    out['label'] = f'item  {x}'\n"
        "    out['a'] = x\n"
        "    return out\n"
    )
    exercise = tmp_path / "ex.py"
    exercise.write_text("INPUTS = [1, 2]\n")

    trace = core.record(original, exercise)

    # Prove the raw values actually differ (no canonicalization applied) --
    # otherwise this "PASS because of canonicalization" case would be an
    # accidental pass, which the spec explicitly forbids.
    for event in trace:
        import importlib.util

        spec = importlib.util.spec_from_file_location("refac_check", refactored)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        actual = mod.run(event["input"])
        assert actual != event["output"]  # cosmetically different, raw compare fails

    result = core.verify(trace, refactored)
    assert result["verdict"] == "PASS"  # but canonicalize() makes it pass


# ---------------------------------------------------------------------------
# the four bundled, pinned cases -- same contract the Forgejury consensus
# surface (gate --case <name>) depends on.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "case_name,expected",
    [
        ("identity", "PASS"),
        ("offbyone", "FAIL"),
        ("nondeterministic", "REFUSE"),
        ("keyorder", "PASS"),
    ],
)
def test_bundled_case_verdicts(case_name, expected):
    outcome = core.run_case(case_name)
    assert outcome["verdict"] == expected


@pytest.mark.parametrize(
    "case_name,expected_json",
    [
        ("identity", '{"verdict": "PASS"}'),
        ("offbyone", '{"verdict": "FAIL"}'),
        ("nondeterministic", '{"verdict": "REFUSE"}'),
        ("keyorder", '{"verdict": "PASS"}'),
    ],
)
def test_gate_cli_stdout_is_exactly_one_pinned_json_line(case_name, expected_json):
    proc = subprocess.run(
        [sys.executable, "-m", "buildoracle", "gate", "--case", case_name],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert proc.returncode == 0
    lines = proc.stdout.strip().splitlines()
    assert len(lines) == 1
    assert lines[0] == expected_json
    assert json.loads(lines[0]) == {"verdict": expected_json.split('"')[-2]}


def test_demo_cli_runs_all_cases():
    proc = subprocess.run(
        [sys.executable, "-m", "buildoracle", "demo"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert proc.returncode == 0
    assert "identity" in proc.stdout
    assert "offbyone" in proc.stdout
    assert "nondeterministic" in proc.stdout
    assert "keyorder" in proc.stdout
    assert core.COVERAGE_LINE in proc.stdout


def test_verify_cli_exit_codes(tmp_path):
    original = tmp_path / "orig.py"
    original.write_text("def run(x):\n    return {'y': x * 2}\n")
    refactored_ok = tmp_path / "ok.py"
    refactored_ok.write_text("def run(x):\n    return {'y': x * 2}\n")
    refactored_bad = tmp_path / "bad.py"
    refactored_bad.write_text("def run(x):\n    return {'y': x * 2 + 1}\n")
    exercise = tmp_path / "ex.py"
    exercise.write_text("INPUTS = [1, 2, 3]\n")
    trace_path = tmp_path / "trace.json"

    rec = subprocess.run(
        [
            sys.executable, "-m", "buildoracle", "record",
            "--module", str(original), "--exercise", str(exercise), "--out", str(trace_path),
        ],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False,
    )
    assert rec.returncode == 0

    ok = subprocess.run(
        [sys.executable, "-m", "buildoracle", "verify", "--trace", str(trace_path), "--module", str(refactored_ok)],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False,
    )
    assert ok.returncode == 0
    assert "PASS" in ok.stdout

    bad = subprocess.run(
        [sys.executable, "-m", "buildoracle", "verify", "--trace", str(trace_path), "--module", str(refactored_bad)],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False,
    )
    assert bad.returncode == 10
    assert "FAIL" in bad.stdout
