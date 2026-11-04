import json
import subprocess
import sys


def _run(*args):
    return subprocess.run(
        [sys.executable, "-m", "forgejury", *args],
        capture_output=True,
        text=True,
    )


def test_lint_cli_warns_but_exits_zero():
    proc = _run("lint", "examples/SPEC.md")
    assert proc.returncode == 0
    assert "WARNING" in proc.stdout
    assert "volatile" in proc.stdout


def test_lint_cli_errors_on_missing_spec():
    proc = _run("lint", "examples/does-not-exist.md")
    assert proc.returncode == 2
    assert "ERROR" in proc.stderr


def test_grade_cli_table_exits_zero_and_shows_divergence():
    proc = _run("grade", "examples/SPEC.md", "examples/build-a", "examples/build-b", "examples/build-c")
    assert proc.returncode == 0
    assert "2-1" in proc.stdout
    assert "build-c" in proc.stdout


def test_grade_cli_json_is_valid_and_matches_schema():
    proc = _run(
        "grade", "examples/SPEC.md",
        "examples/build-a", "examples/build-b", "examples/build-c", "--json",
    )
    assert proc.returncode == 0
    report = json.loads(proc.stdout)
    assert "builds" in report and "consensus" in report
    for build in report["builds"]:
        assert set(build) >= {"build", "spec_axis", "claims_axis", "verdict"}
        assert build["verdict"] in {"PASS", "FAIL"}
    for fixture in report["consensus"].values():
        assert "diverging_build" in fixture
        assert fixture["label"] in {"3-0", "2-1", "3-way"}


def test_grade_cli_no_args_shows_usage():
    proc = _run()
    assert proc.returncode != 0
    assert "usage" in proc.stderr.lower()
