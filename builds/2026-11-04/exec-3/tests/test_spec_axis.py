from forgejury.spec_axis import grade_spec_axis


def test_all_pass():
    observed = {
        "files": {"app.py": True},
        "symbols": {"app.py::main": True},
        "test_cmd_exit": 0,
        "tests_passed": 3,
    }
    result, ok = grade_spec_axis(observed, {"runner": "pytest", "expected_tests_pass": 3})
    assert ok is True
    assert all(v == "PASS" for v in result.values())


def test_missing_file_fails():
    observed = {
        "files": {"app.py": False},
        "symbols": {},
        "test_cmd_exit": 0,
        "tests_passed": None,
    }
    result, ok = grade_spec_axis(observed, {})
    assert ok is False
    assert result["requires_file:app.py"] == "FAIL"


def test_nonzero_exit_fails_the_unkillable_gate():
    observed = {"files": {}, "symbols": {}, "test_cmd_exit": 1, "tests_passed": None}
    result, ok = grade_spec_axis(observed, {})
    assert ok is False
    assert result["test_cmd_exit_0"] == "FAIL"
