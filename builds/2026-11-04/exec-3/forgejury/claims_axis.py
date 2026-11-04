"""Claims axis: report vs reality. A self-delusion detector, not a security boundary."""

import json
import os

from . import symbols as symbols_mod

PASS, FAIL, UNVERIFIABLE = "PASS", "FAIL", "UNVERIFIABLE"


def load_claims(build_dir):
    claims_path = os.path.join(build_dir, "claims.json")
    if not os.path.isfile(claims_path):
        return None
    with open(claims_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def grade_claims_axis(build_dir, claims, observed, spec_checks):
    """Returns ({field: PASS|FAIL|UNVERIFIABLE}, details) comparing claims.json to reality."""
    result = {}
    details = {}

    if claims is None:
        return (
            {
                "files": UNVERIFIABLE,
                "symbols": UNVERIFIABLE,
                "test_cmd_exit": UNVERIFIABLE,
                "tests_passed": UNVERIFIABLE,
            },
            {"reason": "claims.json not found in build dir"},
        )

    # files: every claimed file must actually exist on disk.
    if "files" in claims and isinstance(claims["files"], list):
        missing = [f for f in claims["files"] if not os.path.isfile(os.path.join(build_dir, f))]
        if missing:
            result["files"] = FAIL
            details["files"] = f"claimed present but missing: {missing}"
        else:
            result["files"] = PASS
    else:
        result["files"] = UNVERIFIABLE

    # symbols: every claimed symbol must actually resolve via ast.
    if "symbols" in claims and isinstance(claims["symbols"], list):
        missing = [
            s for s in claims["symbols"] if not symbols_mod.symbol_exists(build_dir, s)
        ]
        if missing:
            result["symbols"] = FAIL
            details["symbols"] = f"claimed defined but not found: {missing}"
        else:
            result["symbols"] = PASS
    else:
        result["symbols"] = UNVERIFIABLE

    # test_cmd_exit: claimed exit code must match the exit code Forgejury itself observed.
    if "test_cmd_exit" in claims:
        if claims["test_cmd_exit"] == observed["test_cmd_exit"]:
            result["test_cmd_exit"] = PASS
        else:
            result["test_cmd_exit"] = FAIL
            details["test_cmd_exit"] = (
                f"claimed {claims['test_cmd_exit']}, observed {observed['test_cmd_exit']}"
            )
    else:
        result["test_cmd_exit"] = UNVERIFIABLE

    # tests_passed: only meaningful when the spec block declares a runner that counts tests.
    if spec_checks.get("runner") == "pytest":
        if "tests_passed" in claims:
            if claims["tests_passed"] == observed["tests_passed"]:
                result["tests_passed"] = PASS
            else:
                result["tests_passed"] = FAIL
                details["tests_passed"] = (
                    f"claimed {claims['tests_passed']}, observed {observed['tests_passed']}"
                )
        else:
            result["tests_passed"] = UNVERIFIABLE
    else:
        result["tests_passed"] = UNVERIFIABLE

    return result, details
