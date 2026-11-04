"""End-to-end: run the real CLI against the bundled examples/ and lock in the
exact demo behavior the reviewer will check by hand."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _run(*args):
    return subprocess.run(
        [sys.executable, "-m", "forgejury", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def test_lint_warns_on_seeded_volatile_fixture():
    proc = _run("lint", "examples/SPEC.md")
    assert proc.returncode == 0
    assert "volatile" in proc.stdout
    assert "date" in proc.stdout


def test_grade_json_matches_expected_shape():
    proc = _run(
        "grade",
        "examples/SPEC.md",
        "examples/build-a",
        "examples/build-b",
        "examples/build-c",
        "--json",
    )
    assert proc.returncode == 0
    doc = json.loads(proc.stdout)

    by_dir = {b["build"]: b for b in doc["builds"]}
    assert by_dir["examples/build-a"]["verdict"] == "PASS"
    assert by_dir["examples/build-b"]["verdict"] == "FAIL"
    assert by_dir["examples/build-b"]["claims_axis"]["tests_passed"] == "FAIL"
    assert by_dir["examples/build-c"]["verdict"] == "PASS"

    assert doc["consensus"]["boundary-bug"] == "2-1"
    assert doc["consensus"]["diverging_build"] == "examples/build-c"
    assert doc["consensus"]["negative-triway"] == "3-way"
    assert doc["consensus"]["small-even"] == "3-0"


def test_grade_human_report_names_the_lie_and_the_diverging_build():
    proc = _run(
        "grade",
        "examples/SPEC.md",
        "examples/build-a",
        "examples/build-b",
        "examples/build-c",
    )
    assert proc.returncode == 0
    assert "claimed 3, observed 2" in proc.stdout
    assert "diverging build: examples/build-c" in proc.stdout
    assert "Triangulation" in proc.stdout
