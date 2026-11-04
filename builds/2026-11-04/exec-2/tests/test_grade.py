import json

from forgejury.grade import (
    classify_consensus,
    grade,
    grade_consensus,
    grade_spec_and_claims,
)

SPEC_CHECKS = {
    "requires_file": ["app.py"],
    "requires_symbol": ["app.py::add"],
    "test_cmd": "python app.py 2 3",
    "runner": "exit-code",
}

APP_SRC = "import sys\n\ndef add(a, b):\n    return a + b\n\nprint(add(int(sys.argv[1]), int(sys.argv[2])))\n"


def _make_build(tmp_path, name, app_src=APP_SRC, claims=None):
    build_dir = tmp_path / name
    build_dir.mkdir()
    (build_dir / "app.py").write_text(app_src)
    if claims is not None:
        (build_dir / "claims.json").write_text(json.dumps(claims))
    return build_dir


def test_spec_axis_all_pass_for_correct_build(tmp_path):
    build_dir = _make_build(tmp_path, "b1")
    result = grade_spec_and_claims(build_dir, SPEC_CHECKS)
    assert result.verdict == "PASS"
    assert all(v == "PASS" for v in result.spec_axis.values())


def test_spec_axis_fails_on_missing_file(tmp_path):
    build_dir = tmp_path / "b1"
    build_dir.mkdir()
    result = grade_spec_and_claims(build_dir, SPEC_CHECKS)
    assert result.verdict == "FAIL"
    assert result.spec_axis["file:app.py"] == "FAIL"


def test_claims_axis_unverifiable_without_claims_json(tmp_path):
    build_dir = _make_build(tmp_path, "b1")
    result = grade_spec_and_claims(build_dir, SPEC_CHECKS)
    assert all(v == "UNVERIFIABLE" for v in result.claims_axis.values())


def test_claims_axis_catches_overstated_files(tmp_path):
    build_dir = _make_build(
        tmp_path,
        "b1",
        claims={"files": ["app.py", "ghost.md"], "symbols": ["app.py::add"], "test_cmd_exit": 0, "tests_passed": 1},
    )
    result = grade_spec_and_claims(build_dir, SPEC_CHECKS)
    assert result.claims_axis["files"] == "FAIL"
    assert "ghost.md" in result.claims_axis["files_detail"]


def test_claims_axis_catches_overstated_tests_passed(tmp_path):
    build_dir = _make_build(
        tmp_path,
        "b1",
        claims={"files": ["app.py"], "symbols": ["app.py::add"], "test_cmd_exit": 0, "tests_passed": 99},
    )
    result = grade_spec_and_claims(build_dir, SPEC_CHECKS)
    assert result.claims_axis["tests_passed"] == "FAIL"
    assert "99" in result.claims_axis["tests_passed_detail"]


def test_classify_consensus_unanimous():
    label, diverging = classify_consensus({"a": "5", "b": "5", "c": "5"})
    assert label == "3-0"
    assert diverging is None


def test_classify_consensus_two_one_split():
    label, diverging = classify_consensus({"a": "5", "b": "5", "c": "9"})
    assert label == "2-1"
    assert diverging == "c"


def test_classify_consensus_three_way_split():
    label, diverging = classify_consensus({"a": "5", "b": "6", "c": "7"})
    assert label == "3-way"
    assert diverging is None


def test_grade_consensus_detects_divergence(tmp_path):
    honest_1 = _make_build(tmp_path, "honest-1")
    honest_2 = _make_build(tmp_path, "honest-2")
    buggy_src = APP_SRC.replace("def add(a, b):\n    return a + b",
                                 "def add(a, b):\n    return abs(a) + abs(b)")
    buggy = _make_build(tmp_path, "buggy", app_src=buggy_src)

    consensus_block = {
        "invoke": "python app.py {input}",
        "fixtures": [
            {"name": "positive", "input": "2 3", "expected": "5"},
            {"name": "negative", "input": "-1 4", "expected": "3"},
        ],
    }
    result = grade_consensus([honest_1, honest_2, buggy], consensus_block)
    assert result["positive"]["label"] == "3-0"
    assert result["negative"]["label"] == "2-1"
    assert result["negative"]["diverging_build"] == str(buggy)
    assert result["negative"]["expected_match"][str(buggy)] == "FAIL"


def test_grade_end_to_end_on_bundled_examples():
    report = grade(
        "examples/SPEC.md",
        ["examples/build-a", "examples/build-b", "examples/build-c"],
    )
    by_name = {b["build"]: b for b in report["builds"]}
    assert by_name["examples/build-a"]["verdict"] == "PASS"
    assert by_name["examples/build-b"]["claims_axis"]["files"] == "FAIL"
    assert by_name["examples/build-b"]["claims_axis"]["tests_passed"] == "FAIL"
    assert report["consensus"]["add-negative"]["label"] == "2-1"
    assert report["consensus"]["add-negative"]["diverging_build"] == "examples/build-c"

    # json.dumps must round-trip the whole report (the --json CLI contract).
    json.dumps(report)
