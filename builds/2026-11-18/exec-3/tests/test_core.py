import json
import subprocess
import sys
from pathlib import Path

from buildoracle import core

FIXTURES = Path(__file__).parent / "fixtures"
CASES = core.CASES_DIR


# ---------------------------------------------------------------------------
# canonicalize
# ---------------------------------------------------------------------------

def test_canonicalize_dict_key_order_insensitive():
    a = {"x": 1, "y": 2, "z": {"inner": 1, "other": 2}}
    b = {"z": {"other": 2, "inner": 1}, "y": 2, "x": 1}
    assert core.canonicalize(a) == core.canonicalize(b)
    # prove the point isn't accidental: raw repr DOES differ by key order
    assert repr(a) != repr(b)


def test_canonicalize_float_precision():
    a = 0.1 * 1.0
    b = (0.1 * 3) / 3
    assert a != b  # raw floats genuinely diverge
    assert core.canonicalize(a) == core.canonicalize(b)


def test_canonicalize_string_whitespace():
    a = "hello   world\n\tfoo"
    b = "hello world foo"
    assert a != b
    assert core.canonicalize(a) == core.canonicalize(b)


def test_canonicalize_set_order_insensitive():
    a = {3, 1, 2}
    b = {2, 3, 1}
    assert core.canonicalize(a) == core.canonicalize(b)


def test_canonicalize_list_order_is_significant():
    assert core.canonicalize([1, 2, 3]) != core.canonicalize([3, 2, 1])


# ---------------------------------------------------------------------------
# classify-then-refuse
# ---------------------------------------------------------------------------

def test_classify_refuses_on_static_import():
    result = core.classify(CASES / "nondeterministic" / "original.py", CASES / "nondeterministic" / "exercise.py")
    assert result["verdict"] == "REFUSE"
    assert result["signal"] == "static"
    assert "time" in result["reason"]
    assert result["line"] == 1


def test_classify_refuses_on_static_global_state():
    result = core.classify(FIXTURES / "global_state.py", FIXTURES / "global_state_exercise.py")
    assert result["verdict"] == "REFUSE"
    assert result["signal"] == "static"
    assert "global" in result["reason"]


def test_classify_refuses_on_empirical_double_run_only():
    # no suspicious import, no `global` statement -- static scan alone would
    # wrongly call this GATEABLE. The empirical double-run must catch it.
    reason, line = core.static_scan(FIXTURES / "hidden_nondeterminism.py")
    assert reason is None

    result = core.classify(FIXTURES / "hidden_nondeterminism.py", FIXTURES / "hidden_nondeterminism_exercise.py")
    assert result["verdict"] == "REFUSE"
    assert result["signal"] == "empirical"


def test_classify_gateable_for_pure_module():
    result = core.classify(CASES / "identity" / "original.py", CASES / "identity" / "exercise.py")
    assert result["verdict"] == "GATEABLE"


# ---------------------------------------------------------------------------
# verify: pass and fail paths
# ---------------------------------------------------------------------------

def test_verify_pass_on_behavior_preserving_refactor():
    trace = core.record(CASES / "identity" / "original.py", CASES / "identity" / "exercise.py")
    result = core.verify(trace, CASES / "identity" / "refactored.py")
    assert result["verdict"] == "PASS"


def test_verify_fail_on_divergent_refactor():
    trace = core.record(CASES / "offbyone" / "original.py", CASES / "offbyone" / "exercise.py")
    result = core.verify(trace, CASES / "offbyone" / "refactored.py")
    assert result["verdict"] == "FAIL"
    assert result["input"] == [50, 50]


def test_verify_pass_through_canonicalization_on_keyorder():
    trace = core.record(CASES / "keyorder" / "original.py", CASES / "keyorder" / "exercise.py")
    result = core.verify(trace, CASES / "keyorder" / "refactored.py")
    assert result["verdict"] == "PASS"
    # and prove it's not an accident of dict.__eq__: the raw outputs really
    # do differ in key order and float value.
    refactored_trace = core.record(CASES / "keyorder" / "refactored.py", CASES / "keyorder" / "exercise.py")
    original_first = trace["events"][0]["output"]
    refactored_first = refactored_trace["events"][0]["output"]
    assert repr(original_first) != repr(refactored_first)
    assert core.canonicalize(original_first) == core.canonicalize(refactored_first)


def test_verify_refuses_when_refactor_itself_is_nondeterministic_static():
    trace = core.record(FIXTURES / "deterministic_original.py", FIXTURES / "deterministic_original_exercise.py")
    result = core.verify(trace, FIXTURES / "refactor_introduces_nondeterminism.py")
    assert result["verdict"] == "REFUSE"
    assert "time" in result["reason"]


def test_verify_refuses_when_refactor_itself_is_nondeterministic_empirical():
    trace = core.record(FIXTURES / "deterministic_original.py", FIXTURES / "deterministic_original_exercise.py")
    result = core.verify(trace, FIXTURES / "refactor_introduces_hidden_nondeterminism.py")
    assert result["verdict"] == "REFUSE"
    assert "empirical" in result["reason"]


# ---------------------------------------------------------------------------
# run_case / gate end-to-end, matching the pinned table in SPEC.md
# ---------------------------------------------------------------------------

def test_run_case_pinned_verdicts():
    assert core.run_case("identity")["verdict"] == "PASS"
    assert core.run_case("offbyone")["verdict"] == "FAIL"
    assert core.run_case("nondeterministic")["verdict"] == "REFUSE"
    assert core.run_case("keyorder")["verdict"] == "PASS"


def test_gate_cli_emits_single_json_line_on_stdout():
    for case_name, expected in [
        ("identity", "PASS"),
        ("offbyone", "FAIL"),
        ("nondeterministic", "REFUSE"),
        ("keyorder", "PASS"),
    ]:
        proc = subprocess.run(
            [sys.executable, "-m", "buildoracle", "gate", "--case", case_name],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0
        stdout_lines = [line for line in proc.stdout.splitlines() if line.strip()]
        assert len(stdout_lines) == 1
        assert json.loads(stdout_lines[0]) == {"verdict": expected}


# ---------------------------------------------------------------------------
# verify CLI exit codes
# ---------------------------------------------------------------------------

def test_verify_cli_exit_codes(tmp_path):
    identity_trace_path = tmp_path / "identity_trace.json"
    subprocess.run(
        [
            sys.executable, "-m", "buildoracle", "record",
            "--module", str(CASES / "identity" / "original.py"),
            "--exercise", str(CASES / "identity" / "exercise.py"),
            "--out", str(identity_trace_path),
        ],
        cwd=Path(__file__).parent.parent,
        check=True,
        capture_output=True,
    )

    pass_proc = subprocess.run(
        [
            sys.executable, "-m", "buildoracle", "verify",
            "--trace", str(identity_trace_path),
            "--module", str(CASES / "identity" / "refactored.py"),
        ],
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        text=True,
    )
    assert pass_proc.returncode == 0
    assert pass_proc.stdout.strip() == "PASS"

    offbyone_trace_path = tmp_path / "offbyone_trace.json"
    subprocess.run(
        [
            sys.executable, "-m", "buildoracle", "record",
            "--module", str(CASES / "offbyone" / "original.py"),
            "--exercise", str(CASES / "offbyone" / "exercise.py"),
            "--out", str(offbyone_trace_path),
        ],
        cwd=Path(__file__).parent.parent,
        check=True,
        capture_output=True,
    )

    fail_proc = subprocess.run(
        [
            sys.executable, "-m", "buildoracle", "verify",
            "--trace", str(offbyone_trace_path),
            "--module", str(CASES / "offbyone" / "refactored.py"),
        ],
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        text=True,
    )
    assert fail_proc.returncode == 10
    assert fail_proc.stdout.startswith("FAIL: diverged on input")


def test_verify_cli_exit_code_20_on_refuse(tmp_path):
    trace_path = tmp_path / "deterministic_trace.json"
    subprocess.run(
        [
            sys.executable, "-m", "buildoracle", "record",
            "--module", str(FIXTURES / "deterministic_original.py"),
            "--exercise", str(FIXTURES / "deterministic_original_exercise.py"),
            "--out", str(trace_path),
        ],
        cwd=Path(__file__).parent.parent,
        check=True,
        capture_output=True,
    )

    refuse_proc = subprocess.run(
        [
            sys.executable, "-m", "buildoracle", "verify",
            "--trace", str(trace_path),
            "--module", str(FIXTURES / "refactor_introduces_nondeterminism.py"),
        ],
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        text=True,
    )
    assert refuse_proc.returncode == 20
    assert refuse_proc.stdout.startswith("REFUSE:")


def test_classify_cli_exit_code_on_refuse():
    proc = subprocess.run(
        [
            sys.executable, "-m", "buildoracle", "classify",
            "--module", str(CASES / "nondeterministic" / "original.py"),
            "--exercise", str(CASES / "nondeterministic" / "exercise.py"),
        ],
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert proc.stdout.startswith("REFUSE:")
    assert "imports time" in proc.stdout
