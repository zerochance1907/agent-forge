"""CLI surface for BuildOracle.

    python -m buildoracle record   --module <path> --exercise <path> --out <trace.json>
    python -m buildoracle classify --module <path> --exercise <path>
    python -m buildoracle verify   --trace <trace.json> --module <path>
    python -m buildoracle gate     --case <name>
    python -m buildoracle demo
"""

from __future__ import annotations

import argparse
import json
import sys

from buildoracle import core


def _cmd_record(args: argparse.Namespace) -> int:
    try:
        events = core.record_to_file(args.module, args.exercise, args.out)
    except core.LoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"recorded {len(events)} event(s) to {args.out}", file=sys.stderr)
    return 0


def _cmd_classify(args: argparse.Namespace) -> int:
    try:
        verdict = core.classify(args.module, args.exercise)
    except core.LoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if verdict["verdict"] == "GATEABLE":
        print("GATEABLE")
        return 0
    suffix = f" [line {verdict['line']}]" if verdict["line"] else ""
    print(f"REFUSE: {verdict['reason']}{suffix}")
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    try:
        result = core.verify_trace_file(args.trace, args.module)
    except core.LoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if result["verdict"] == "PASS":
        print("PASS")
        return 0
    if result["verdict"] == "FAIL":
        print(f"FAIL: diverged on input {result['input']!r}")
        return 10
    suffix = f" [line {result['line']}]" if result["line"] else ""
    print(f"REFUSE: {result['reason']}{suffix}")
    return 20


def _cmd_gate(args: argparse.Namespace) -> int:
    try:
        outcome = core.run_case(args.case)
    except core.LoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    # Human-readable detail -> stderr. Exactly one compact JSON line -> stdout.
    detail_bits = [f"case={args.case}"]
    if outcome.get("reason"):
        suffix = f" [line {outcome['line']}]" if outcome.get("line") else ""
        detail_bits.append(f"reason={outcome['reason']}{suffix}")
    if outcome.get("diverged_on") is not None:
        detail_bits.append(f"diverged_on={outcome['diverged_on']!r}")
    detail_bits.append(outcome["coverage"])
    print(" | ".join(detail_bits), file=sys.stderr)
    print(json.dumps({"verdict": outcome["verdict"]}))
    return 0


def _cmd_demo(_args: argparse.Namespace) -> int:
    print(f"{'case':<18} {'verdict':<8} detail")
    print("-" * 70)
    for case_name in core.KNOWN_CASES:
        outcome = core.run_case(case_name)
        detail = ""
        if outcome.get("reason"):
            suffix = f" [line {outcome['line']}]" if outcome.get("line") else ""
            detail = f"{outcome['reason']}{suffix}"
        elif outcome.get("diverged_on") is not None:
            detail = f"diverged on input {outcome['diverged_on']!r}"
        print(f"{case_name:<18} {outcome['verdict']:<8} {detail}")
    print("-" * 70)
    print(core.COVERAGE_LINE)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m buildoracle")
    sub = parser.add_subparsers(dest="command", required=True)

    p_record = sub.add_parser("record", help="record a module's behavior to a trace file")
    p_record.add_argument("--module", required=True)
    p_record.add_argument("--exercise", required=True)
    p_record.add_argument("--out", required=True)
    p_record.set_defaults(func=_cmd_record)

    p_classify = sub.add_parser("classify", help="print the gateability verdict for a module")
    p_classify.add_argument("--module", required=True)
    p_classify.add_argument("--exercise", required=True)
    p_classify.set_defaults(func=_cmd_classify)

    p_verify = sub.add_parser("verify", help="replay a trace against a module")
    p_verify.add_argument("--trace", required=True)
    p_verify.add_argument("--module", required=True)
    p_verify.set_defaults(func=_cmd_verify)

    p_gate = sub.add_parser("gate", help="run one bundled, pinned case end-to-end")
    p_gate.add_argument("--case", required=True, choices=core.KNOWN_CASES)
    p_gate.set_defaults(func=_cmd_gate)

    p_demo = sub.add_parser("demo", help="run all bundled cases and print a verdict table")
    p_demo.set_defaults(func=_cmd_demo)

    return parser


def main(argv: list[str] | None = None) -> int:
    # The coverage line and some docstrings use an em dash; make sure stdout
    # survives it even when the console's locale codepage isn't UTF-8 (e.g.
    # Windows cp1252), instead of crashing or mangling the character.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
