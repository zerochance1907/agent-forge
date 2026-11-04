"""Spec axis: build vs spec. The unkillable gate is exit code 0."""

PASS, FAIL, UNVERIFIABLE = "PASS", "FAIL", "UNVERIFIABLE"


def grade_spec_axis(observed, spec_checks):
    """Returns ({check_name: PASS|FAIL}, verdict_bool)."""
    result = {}

    for path, exists in observed["files"].items():
        result[f"requires_file:{path}"] = PASS if exists else FAIL

    for sym, present in observed["symbols"].items():
        result[f"requires_symbol:{sym}"] = PASS if present else FAIL

    result["test_cmd_exit_0"] = PASS if observed["test_cmd_exit"] == 0 else FAIL

    runner = spec_checks.get("runner")
    expected_pass = spec_checks.get("expected_tests_pass")
    if runner == "pytest" and expected_pass is not None:
        result["expected_tests_pass"] = (
            PASS if observed["tests_passed"] == expected_pass else FAIL
        )

    all_pass = all(v == PASS for v in result.values())
    return result, all_pass
