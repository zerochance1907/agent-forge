import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from buildoracle import core  # noqa: E402

CASES = ROOT / "buildoracle" / "cases"


def test_canonicalize_dict_key_order_insensitivity():
    a = {"b": 1, "a": 2}
    b = {"a": 2, "b": 1}
    assert core.canonicalize(a) == core.canonicalize(b)
    assert list(core.canonicalize(a).keys()) == ["a", "b"]


def test_canonicalize_float_precision():
    assert core.canonicalize(1.00000000001) == core.canonicalize(1.00000000002)
    assert core.canonicalize(1.234567890123) == round(1.234567890123, 9)


def test_canonicalize_string_whitespace_normalization():
    assert core.canonicalize("  hello   world  ") == "hello world"
    assert core.canonicalize("hello world") == core.canonicalize("  hello   world  ")


def test_canonicalize_nested_structures():
    a = {"scores": {"b": 1.0000000001, "a": 2}, "tag": "  x  y "}
    b = {"tag": "x y", "scores": {"a": 2, "b": 1.0000000002}}
    assert core.canonicalize(a) == core.canonicalize(b)


def test_static_scan_flags_time_import():
    case = CASES / "nondeterministic"
    findings = core.static_scan(str(case / "original.py"))
    assert findings
    assert "time" in findings[0][0]
    assert findings[0][1] == 1


def test_classify_refuses_nondeterministic_module():
    case = CASES / "nondeterministic"
    result = core.classify(str(case / "original.py"), str(case / "exercise.py"))
    assert result["verdict"] == "REFUSE"
    assert "time" in result["reason"]
    assert result["line"] == 1


def test_classify_gateable_for_deterministic_module():
    case = CASES / "identity"
    result = core.classify(str(case / "original.py"), str(case / "exercise.py"))
    assert result["verdict"] == "GATEABLE"


def test_classify_refuses_transitive_nondeterminism_via_double_run(tmp_path):
    # timeit isn't in NONDET_MODULES, so the static scan can't see this --
    # only the empirical double-run catches it. timeit.default_timer() is
    # time.perf_counter() under the hood, so it strictly increases every call.
    module_path = tmp_path / "transitive.py"
    module_path.write_text(
        "import timeit\n\n\ndef stamp():\n    return timeit.default_timer()\n"
    )
    exercise_path = tmp_path / "exercise.py"
    exercise_path.write_text('INPUTS = [("stamp", (), {})]\n')

    static_findings = core.static_scan(str(module_path))
    assert static_findings == []  # proves this case needs the double-run, not the static scan

    result = core.classify(str(module_path), str(exercise_path))
    assert result["verdict"] == "REFUSE"
    assert "double-run divergence" in result["reason"]


def test_verify_pass_on_identity_case():
    case = CASES / "identity"
    trace = core.record(str(case / "original.py"), str(case / "exercise.py"))
    result = core.verify(trace, str(case / "refactored.py"))
    assert result["verdict"] == "PASS"


def test_verify_fail_on_offbyone_case_names_diverging_input():
    case = CASES / "offbyone"
    trace = core.record(str(case / "original.py"), str(case / "exercise.py"))
    result = core.verify(trace, str(case / "refactored.py"))
    assert result["verdict"] == "FAIL"
    assert result["func"] == "clamp"
    assert result["args"] == [15, 0, 10]


def test_verify_pass_on_keyorder_case_via_canonicalization():
    case = CASES / "keyorder"
    trace = core.record(str(case / "original.py"), str(case / "exercise.py"))
    original_keys = list(trace[0]["result"]["value"].keys())

    module = core.load_module(str(case / "refactored.py"))
    actual_value = module.build_profile(*trace[0]["args"], **trace[0]["kwargs"])
    refactored_keys = list(actual_value.keys())

    # Prove the raw dict orders genuinely differ -- the PASS below must
    # happen *because* verify canonicalizes, not by accident.
    assert original_keys != refactored_keys
    assert sorted(original_keys) == sorted(refactored_keys)

    result = core.verify(trace, str(case / "refactored.py"))
    assert result["verdict"] == "PASS"
