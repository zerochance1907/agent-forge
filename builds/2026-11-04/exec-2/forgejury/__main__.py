"""python -m forgejury — a stdlib-only triangulated build-to-review gate.

Subcommands:
  lint  <spec.md>                      validate an acceptance block
  grade <spec.md> <build-dir>...       triangulate one or more builds
  grade <spec.md> <build-dir>... --json   same, as stable machine-readable JSON
"""
from __future__ import annotations

import argparse
import json
import sys

from .grade import grade
from .lint import lint_block
from .report import format_human_report
from .spec_parser import SpecError, parse_acceptance_block


def _cmd_lint(args: argparse.Namespace) -> int:
    try:
        block = parse_acceptance_block(args.spec)
    except SpecError as exc:
        print(f"forgejury lint: ERROR: {exc}", file=sys.stderr)
        return 2

    result = lint_block(block)
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    for error in result.errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if result.ok:
        print(f"OK: acceptance block in {args.spec} is valid ({len(result.warnings)} warning(s))")
        return 0

    print(f"FAIL: acceptance block in {args.spec} has {len(result.errors)} error(s)", file=sys.stderr)
    return 1


def _cmd_grade(args: argparse.Namespace) -> int:
    try:
        report = grade(args.spec, args.build_dirs)
    except SpecError as exc:
        print(f"forgejury grade: ERROR: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"forgejury grade: ERROR: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_human_report(report))

    any_fail = any(b["verdict"] == "FAIL" for b in report["builds"])
    return 1 if any_fail else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m forgejury",
        description=(
            "Triangulates a build's claims and observed behavior against a spec's "
            "acceptance block, independent of what its build-report says."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    lint_parser = sub.add_parser("lint", help="validate an acceptance block before any build runs")
    lint_parser.add_argument("spec", help="path to the spec markdown file")
    lint_parser.set_defaults(func=_cmd_lint)

    grade_parser = sub.add_parser("grade", help="triangulate one or more builds against the spec")
    grade_parser.add_argument("spec", help="path to the spec markdown file")
    grade_parser.add_argument("build_dirs", nargs="+", help="one or more build directories")
    grade_parser.add_argument("--json", action="store_true", help="emit stable machine-readable JSON")
    grade_parser.set_defaults(func=_cmd_grade)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
