"""Layers 1-2: observe each build independently, diff against the spec and
against its own claims.json, then triangulate consensus across builds.

Claims axis = self-delusion detector, not a security boundary: it catches a
report that drifted from a fresh run, not an executioner who tunes
claims.json to match. Consensus = attention router, not a correctness
oracle: a 2-1 majority can be two builds sharing the same wrong assumption.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .canonical import canonicalize
from .runner import parse_pytest_passed, run_command
from .spec_parser import parse_acceptance_block
from .symbols import has_symbol

PASS = "PASS"
FAIL = "FAIL"
UNVERIFIABLE = "UNVERIFIABLE"


@dataclass
class BuildResult:
    build: str
    spec_axis: dict = field(default_factory=dict)
    claims_axis: dict = field(default_factory=dict)
    verdict: str = FAIL

    def to_json(self) -> dict:
        return {
            "build": self.build,
            "spec_axis": self.spec_axis,
            "claims_axis": self.claims_axis,
            "verdict": self.verdict,
        }


def _observe_spec_axis(build_dir: Path, spec_checks: dict):
    axis = {}

    for rel in spec_checks.get("requires_file", []):
        axis[f"file:{rel}"] = PASS if (build_dir / rel).is_file() else FAIL

    for sym in spec_checks.get("requires_symbol", []):
        axis[f"symbol:{sym}"] = PASS if has_symbol(build_dir, sym) else FAIL

    exit_code, stdout, stderr = run_command(spec_checks["test_cmd"], cwd=build_dir)
    axis["test_cmd"] = PASS if exit_code == 0 else FAIL
    return axis, exit_code, stdout, stderr


def _observed_tests_passed(spec_checks: dict, exit_code: int, stdout: str, stderr: str):
    """Return the observed pass count, or None if unverifiable (no runner declared)."""
    runner = spec_checks.get("runner")
    if runner == "pytest":
        return parse_pytest_passed(stdout, stderr)
    if runner == "exit-code":
        return 1 if exit_code == 0 else 0
    return None


def _load_claims(build_dir: Path):
    claims_path = build_dir / "claims.json"
    if not claims_path.is_file():
        return None
    try:
        return json.loads(claims_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _observe_claims_axis(build_dir: Path, spec_checks: dict, claims, exit_code, stdout, stderr):
    if claims is None:
        return {
            "files": UNVERIFIABLE,
            "symbols": UNVERIFIABLE,
            "test_cmd_exit": UNVERIFIABLE,
            "tests_passed": UNVERIFIABLE,
        }

    axis = {}

    claimed_files = claims.get("files")
    if not isinstance(claimed_files, list):
        axis["files"] = UNVERIFIABLE
    else:
        missing = [f for f in claimed_files if not (build_dir / f).is_file()]
        axis["files"] = FAIL if missing else PASS
        if missing:
            axis["files_detail"] = f"claimed but missing: {', '.join(missing)}"

    claimed_symbols = claims.get("symbols")
    if not isinstance(claimed_symbols, list):
        axis["symbols"] = UNVERIFIABLE
    else:
        missing = [s for s in claimed_symbols if not has_symbol(build_dir, s)]
        axis["symbols"] = FAIL if missing else PASS
        if missing:
            axis["symbols_detail"] = f"claimed but missing: {', '.join(missing)}"

    claimed_exit = claims.get("test_cmd_exit")
    if not isinstance(claimed_exit, int):
        axis["test_cmd_exit"] = UNVERIFIABLE
    else:
        axis["test_cmd_exit"] = PASS if claimed_exit == exit_code else FAIL
        if claimed_exit != exit_code:
            axis["test_cmd_exit_detail"] = f"claimed {claimed_exit}, observed {exit_code}"

    observed_tests_passed = _observed_tests_passed(spec_checks, exit_code, stdout, stderr)
    claimed_tests_passed = claims.get("tests_passed")
    if observed_tests_passed is None or not isinstance(claimed_tests_passed, int):
        axis["tests_passed"] = UNVERIFIABLE
    else:
        axis["tests_passed"] = PASS if claimed_tests_passed == observed_tests_passed else FAIL
        if claimed_tests_passed != observed_tests_passed:
            axis["tests_passed_detail"] = (
                f"claimed {claimed_tests_passed}, observed {observed_tests_passed}"
            )

    return axis


def grade_spec_and_claims(build_dir, spec_checks: dict) -> BuildResult:
    # Keep the caller's original path string as the build label — converting
    # through Path and back would silently rewrite "a/b" to "a\\b" on Windows,
    # which would then fail to match the identifier the caller passed in.
    label = str(build_dir)
    path = Path(build_dir)
    spec_axis, exit_code, stdout, stderr = _observe_spec_axis(path, spec_checks)
    claims = _load_claims(path)
    claims_axis = _observe_claims_axis(path, spec_checks, claims, exit_code, stdout, stderr)
    verdict = PASS if all(v == PASS for v in spec_axis.values()) else FAIL
    return BuildResult(build=label, spec_axis=spec_axis, claims_axis=claims_axis, verdict=verdict)


def run_fixture(build_dir: Path, invoke_template: str, fixture_input: str, timeout: int = 60):
    command = invoke_template.replace("{input}", fixture_input)
    exit_code, stdout, stderr = run_command(command, cwd=build_dir, timeout=timeout)
    return exit_code, canonicalize(stdout), stderr


def classify_consensus(outputs: dict):
    """outputs: {build_dir: canonical_stdout}. Returns (label, diverging_build)."""
    n = len(outputs)
    groups = {}
    for build, output in outputs.items():
        groups.setdefault(output, []).append(build)
    sizes = sorted((len(members) for members in groups.values()), reverse=True)

    if len(groups) == 1:
        return f"{n}-0", None
    if n == 3 and sizes == [2, 1]:
        minority = next(members for members in groups.values() if len(members) == 1)
        return "2-1", minority[0]
    if n == 3 and len(groups) == 3:
        return "3-way", None

    # Generic fallback for N != 3 — the 3-0/2-1/3-way vocabulary is specific
    # to triangulating exactly three parallel builds (this pipeline's N).
    label = "-".join(str(s) for s in sizes)
    diverging = None
    if len(groups) == 2 and sizes.count(1) == 1:
        diverging = next(members[0] for members in groups.values() if len(members) == 1)
    return label, diverging


def grade_consensus(build_dirs, consensus_block: dict) -> dict:
    invoke = consensus_block["invoke"]
    results = {}

    for fixture in consensus_block["fixtures"]:
        name = fixture["name"]
        fixture_input = fixture.get("input", "")
        outputs = {}
        errors = {}

        for build_dir in build_dirs:
            label = str(build_dir)
            exit_code, canon, stderr = run_fixture(Path(build_dir), invoke, fixture_input)
            outputs[label] = canon
            if exit_code != 0:
                last_line = stderr.strip().splitlines()[-1] if stderr.strip() else ""
                errors[label] = f"exit {exit_code}" + (f": {last_line}" if last_line else "")

        label, diverging = classify_consensus(outputs)

        expected_match = None
        expected = fixture.get("expected")
        if isinstance(expected, str):
            expected_canon = canonicalize(expected)
            expected_match = {
                build: (PASS if output == expected_canon else FAIL)
                for build, output in outputs.items()
            }

        results[name] = {
            "label": label,
            "diverging_build": diverging,
            "outputs": outputs,
            "expected_match": expected_match,
            "errors": errors or None,
        }

    return results


def grade(spec_path, build_dirs) -> dict:
    """Run layers 1+2 for every build dir against the acceptance block in `spec_path`."""
    block = parse_acceptance_block(spec_path)
    spec_checks = block.get("spec_checks")
    consensus_block = block.get("consensus")
    if not isinstance(spec_checks, dict) or not isinstance(consensus_block, dict):
        from .spec_parser import SpecError

        raise SpecError("acceptance block must contain 'spec_checks' and 'consensus' objects")

    builds = [grade_spec_and_claims(d, spec_checks) for d in build_dirs]
    consensus = grade_consensus(build_dirs, consensus_block)

    return {
        "builds": [b.to_json() for b in builds],
        "consensus": consensus,
    }
