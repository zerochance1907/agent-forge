"""Subprocess helpers.

Forgejury runs only the spec-declared `test_cmd` and `invoke` — never a
command named inside a build-report. That boundary is enforced by callers
only ever passing strings sourced from the parsed acceptance block.
"""
from __future__ import annotations

import re
import shlex
import subprocess

_PYTEST_SUMMARY = re.compile(r"(\d+)\s+passed")

DEFAULT_TIMEOUT = 120


def run_command(command: str, cwd, timeout: int = DEFAULT_TIMEOUT):
    """Run `command` (shell-style split) with the given cwd.

    Returns (exit_code, stdout, stderr). A command that fails to even start
    (bad executable, missing file, timeout) reports exit_code -1 with the
    failure reason in stderr instead of raising.
    """
    try:
        args = shlex.split(command)
    except ValueError as exc:
        return -1, "", f"could not parse command {command!r}: {exc}"

    if not args:
        return -1, "", f"empty command: {command!r}"

    try:
        proc = subprocess.run(
            args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        return -1, exc.stdout or "", f"timed out after {timeout}s"
    except OSError as exc:
        return -1, "", str(exc)


def parse_pytest_passed(stdout: str, stderr: str) -> int:
    """Extract the 'N passed' count from pytest's summary line, else 0."""
    for text in (stdout, stderr):
        match = _PYTEST_SUMMARY.search(text)
        if match:
            return int(match.group(1))
    return 0
