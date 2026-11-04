"""CLI entrypoint: python -m forgejury lint|grade ..."""

import argparse
import sys

from . import block as block_mod
from . import claims_axis
from . import consensus as consensus_mod
from . import observe
from . import report
from . import spec_axis


def cmd_lint(args):
    try:
        with open(args.spec, "r", encoding="utf-8") as fh:
            spec_text = fh.read()
        parsed = block_mod.parse_block(spec_text)
    except block_mod.BlockError as exc:
        print(f"LINT FAIL: {exc}")
        return 1
    except OSError as exc:
        print(f"LINT FAIL: cannot read spec file: {exc}")
        return 1

    errors, warnings = block_mod.lint_block(parsed)

    for w in warnings:
        print(f"WARNING: {w}")
    for e in errors:
        print(f"ERROR: {e}")

    if errors:
        print("LINT FAIL")
        return 1

    print("LINT OK" + (f" ({len(warnings)} warning(s))" if warnings else ""))
    return 0


def cmd_grade(args):
    try:
        parsed = block_mod.load_block(args.spec)
    except block_mod.BlockError as exc:
        print(f"GRADE FAIL: {exc}")
        return 1
    except OSError as exc:
        print(f"GRADE FAIL: cannot read spec file: {exc}")
        return 1

    spec_checks = parsed["spec_checks"]
    consensus_block = parsed["consensus"]
    build_dirs = args.build_dirs

    spec_results = {}
    claims_results = {}
    for build_dir in build_dirs:
        observed = observe.observe_build(build_dir, spec_checks)
        spec_results[build_dir] = spec_axis.grade_spec_axis(observed, spec_checks)
        claims = claims_axis.load_claims(build_dir)
        claims_results[build_dir] = claims_axis.grade_claims_axis(
            build_dir, claims, observed, spec_checks
        )

    fixture_results = consensus_mod.run_consensus(build_dirs, consensus_block)

    if args.json:
        report.print_json_verdict(build_dirs, spec_results, claims_results, fixture_results)
    else:
        report.print_human_report(
            build_dirs, spec_results, claims_results, fixture_results, spec_checks
        )
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="forgejury")
    sub = parser.add_subparsers(dest="command", required=True)

    lint_p = sub.add_parser("lint", help="validate an acceptance block")
    lint_p.add_argument("spec")
    lint_p.set_defaults(func=cmd_lint)

    grade_p = sub.add_parser("grade", help="triangulate build-dirs against an acceptance block")
    grade_p.add_argument("spec")
    grade_p.add_argument("build_dirs", nargs="+")
    grade_p.add_argument("--json", action="store_true")
    grade_p.set_defaults(func=cmd_grade)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
