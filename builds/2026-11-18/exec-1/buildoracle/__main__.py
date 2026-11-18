"""CLI: python -m buildoracle {record,classify,verify,gate,demo}"""

import argparse
import json
import sys
from pathlib import Path

from . import core

CASES_DIR = Path(__file__).parent / "cases"
CASE_NAMES = ["identity", "offbyone", "nondeterministic", "keyorder"]
COVERAGE_LINE = "coverage: recorded trace + existing tests only -- unexercised paths not gated"


def _case_paths(name):
    d = CASES_DIR / name
    return d / "original.py", d / "refactored.py", d / "exercise.py"


def _format_refuse(result):
    line_part = f" [line {result['line']}]" if result.get("line") else ""
    return f"REFUSE: {result['reason']}{line_part}"


def _format_fail(result):
    return f"FAIL: diverged on input func={result['func']} args={result['args']} kwargs={result['kwargs']}"


def run_gate_case(name):
    """record the case's original -> classify -> verify its refactor.
    Returns (verdict, detail_dict)."""
    original, refactored, exercise = _case_paths(name)

    classification = core.classify(str(original), str(exercise))
    if classification["verdict"] == "REFUSE":
        print(_format_refuse(classification), file=sys.stderr)
        print(COVERAGE_LINE, file=sys.stderr)
        return "REFUSE", classification

    trace = core.record(str(original), str(exercise))
    result = core.verify(trace, str(refactored))

    if result["verdict"] == "PASS":
        print("PASS", file=sys.stderr)
    elif result["verdict"] == "FAIL":
        print(_format_fail(result), file=sys.stderr)
    else:
        print(_format_refuse(result), file=sys.stderr)

    print(COVERAGE_LINE, file=sys.stderr)
    return result["verdict"], result


def cmd_record(args):
    trace = core.record(args.module, args.exercise, args.out)
    print(f"recorded {len(trace)} events to {args.out}", file=sys.stderr)


def cmd_classify(args):
    result = core.classify(args.module, args.exercise)
    if result["verdict"] == "GATEABLE":
        print("GATEABLE")
    else:
        print(_format_refuse(result))


def cmd_verify(args):
    trace = json.loads(Path(args.trace).read_text())
    result = core.verify(trace, args.module)
    print(COVERAGE_LINE, file=sys.stderr)
    if result["verdict"] == "PASS":
        print("PASS")
        sys.exit(0)
    elif result["verdict"] == "FAIL":
        print(_format_fail(result))
        sys.exit(10)
    else:
        print(_format_refuse(result))
        sys.exit(20)


def cmd_gate(args):
    if args.case not in CASE_NAMES:
        print(f"unknown case '{args.case}', known cases: {CASE_NAMES}", file=sys.stderr)
        sys.exit(1)
    verdict, _detail = run_gate_case(args.case)
    print(json.dumps({"verdict": verdict}))
    sys.exit(0)


def cmd_demo(_args):
    print(f"{'case':<18} verdict")
    print("-" * 30)
    for name in CASE_NAMES:
        verdict, _detail = run_gate_case(name)
        print(f"{name:<18} {verdict}")
    print(file=sys.stderr)
    print(COVERAGE_LINE, file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(prog="buildoracle")
    sub = parser.add_subparsers(dest="command", required=True)

    p_record = sub.add_parser("record")
    p_record.add_argument("--module", required=True)
    p_record.add_argument("--exercise", required=True)
    p_record.add_argument("--out", required=True)
    p_record.set_defaults(func=cmd_record)

    p_classify = sub.add_parser("classify")
    p_classify.add_argument("--module", required=True)
    p_classify.add_argument("--exercise", required=True)
    p_classify.set_defaults(func=cmd_classify)

    p_verify = sub.add_parser("verify")
    p_verify.add_argument("--trace", required=True)
    p_verify.add_argument("--module", required=True)
    p_verify.set_defaults(func=cmd_verify)

    p_gate = sub.add_parser("gate")
    p_gate.add_argument("--case", required=True)
    p_gate.set_defaults(func=cmd_gate)

    p_demo = sub.add_parser("demo")
    p_demo.set_defaults(func=cmd_demo)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
