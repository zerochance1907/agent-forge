"""Independently observe a build dir's real state: files, symbols, test_cmd exit code."""

import os
import re
import subprocess

from . import symbols as symbols_mod

_PYTEST_SUMMARY_RE = re.compile(
    r"(?P<passed>\d+) passed(?:, (?P<failed1>\d+) failed)?|"
    r"(?P<failed2>\d+) failed(?:, (?P<passed2>\d+) passed)?"
)


def observe_files(build_dir, requires_file):
    return {path: os.path.isfile(os.path.join(build_dir, path)) for path in requires_file}


def observe_symbols(build_dir, requires_symbol):
    return {sym: symbols_mod.symbol_exists(build_dir, sym) for sym in requires_symbol}


def run_test_cmd(build_dir, test_cmd, timeout=60):
    """Run the declared test_cmd with cwd=build_dir. Returns (exit_code, stdout, stderr)."""
    try:
        proc = subprocess.run(
            test_cmd,
            shell=True,
            cwd=build_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return None, "", f"test_cmd timed out after {timeout}s"


def parse_pytest_passed(stdout_text, stderr_text):
    """Best-effort extraction of the number of passed tests from pytest -q output."""
    combined = stdout_text + "\n" + stderr_text
    last_match = None
    for match in _PYTEST_SUMMARY_RE.finditer(combined):
        last_match = match
    if not last_match:
        if "no tests ran" in combined.lower():
            return 0
        return None
    passed = last_match.group("passed") or last_match.group("passed2")
    return int(passed) if passed is not None else 0


def observe_build(build_dir, spec_checks):
    """Run every spec-declared observation against one build dir. Pure observation, no opinions."""
    files = observe_files(build_dir, spec_checks.get("requires_file", []))
    syms = observe_symbols(build_dir, spec_checks.get("requires_symbol", []))
    exit_code, stdout_text, stderr_text = run_test_cmd(build_dir, spec_checks["test_cmd"])

    tests_passed = None
    if spec_checks.get("runner") == "pytest":
        tests_passed = parse_pytest_passed(stdout_text, stderr_text)

    return {
        "files": files,
        "symbols": syms,
        "test_cmd_exit": exit_code,
        "tests_passed": tests_passed,
        "_raw_stdout": stdout_text,
        "_raw_stderr": stderr_text,
    }
