import json

from forgejury import claims_axis, observe


def _make_build(tmp_path, classify_body, test_body):
    d = tmp_path / "b"
    d.mkdir()
    (d / "app.py").write_text(classify_body)
    tests_dir = d / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_app.py").write_text(test_body)
    return d


CLASSIFY = "def classify(n):\n    return 'small' if n < 100 else 'large'\n"
HONEST_TEST = (
    "import sys\nfrom pathlib import Path\n"
    "sys.path.insert(0, str(Path(__file__).resolve().parent.parent))\n"
    "from app import classify\n\n"
    "def test_small():\n    assert classify(1) == 'small'\n"
)


def test_claims_missing_file_marked_unverifiable(tmp_path):
    d = _make_build(tmp_path, CLASSIFY, HONEST_TEST)
    result, _ = claims_axis.grade_claims_axis(
        str(d), None, {"files": {}, "symbols": {}, "test_cmd_exit": 0, "tests_passed": 1},
        {"runner": "pytest"},
    )
    assert all(v == "UNVERIFIABLE" for v in result.values())


def test_claims_lying_about_files(tmp_path):
    d = _make_build(tmp_path, CLASSIFY, HONEST_TEST)
    claims = {"files": ["app.py", "ghost.py"]}
    result, details = claims_axis.grade_claims_axis(
        str(d), claims, {"test_cmd_exit": 0, "tests_passed": 1}, {"runner": "pytest"}
    )
    assert result["files"] == "FAIL"
    assert "ghost.py" in details["files"]


def test_claims_lying_about_tests_passed(tmp_path):
    d = _make_build(tmp_path, CLASSIFY, HONEST_TEST)
    claims = {"test_cmd_exit": 0, "tests_passed": 99}
    observed = {"test_cmd_exit": 0, "tests_passed": 1}
    result, details = claims_axis.grade_claims_axis(
        str(d), claims, observed, {"runner": "pytest"}
    )
    assert result["tests_passed"] == "FAIL"
    assert "99" in details["tests_passed"]


def test_claims_tests_passed_unverifiable_without_runner(tmp_path):
    d = _make_build(tmp_path, CLASSIFY, HONEST_TEST)
    claims = {"test_cmd_exit": 0, "tests_passed": 99}
    observed = {"test_cmd_exit": 0, "tests_passed": None}
    result, _ = claims_axis.grade_claims_axis(str(d), claims, observed, {})
    assert result["tests_passed"] == "UNVERIFIABLE"


def test_claims_honest_build_all_pass(tmp_path):
    d = _make_build(tmp_path, CLASSIFY, HONEST_TEST)
    (d / "claims.json").write_text(
        json.dumps(
            {
                "files": ["app.py", "tests/test_app.py"],
                "symbols": ["app.py::classify"],
                "test_cmd_exit": 0,
                "tests_passed": 1,
            }
        )
    )
    spec_checks = {
        "requires_file": ["app.py", "tests/test_app.py"],
        "requires_symbol": ["app.py::classify"],
        "test_cmd": "python -m pytest -q",
        "runner": "pytest",
    }
    observed = observe.observe_build(str(d), spec_checks)
    claims = claims_axis.load_claims(str(d))
    result, _ = claims_axis.grade_claims_axis(str(d), claims, observed, spec_checks)
    assert result == {
        "files": "PASS",
        "symbols": "PASS",
        "test_cmd_exit": "PASS",
        "tests_passed": "PASS",
    }
