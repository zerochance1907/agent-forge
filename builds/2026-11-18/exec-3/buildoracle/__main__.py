import argparse
import json
import sys
from pathlib import Path

from . import core
from .oracle_eye import render_demo


def _build_parser():
    parser = argparse.ArgumentParser(prog="python -m buildoracle")
    sub = parser.add_subparsers(dest="command", required=True)

    p_record = sub.add_parser("record", help="capture a behavior trace")
    p_record.add_argument("--module", required=True)
    p_record.add_argument("--exercise", required=True)
    p_record.add_argument("--out", required=True)

    p_classify = sub.add_parser("classify", help="print the gateability verdict")
    p_classify.add_argument("--module", required=True)
    p_classify.add_argument("--exercise", required=True)

    p_verify = sub.add_parser("verify", help="replay a trace against a module")
    p_verify.add_argument("--trace", required=True)
    p_verify.add_argument("--module", required=True)

    p_gate = sub.add_parser("gate", help="run one bundled case end-to-end")
    p_gate.add_argument("--case", required=True)

    sub.add_parser("demo", help="run all bundled cases and print a table")

    return parser


def _cmd_record(args):
    trace = core.record(args.module, args.exercise)
    Path(args.out).write_text(json.dumps(trace, indent=2))
    print(f"trace written to {args.out} ({len(trace['events'])} events)", file=sys.stderr)
    return 0


def _cmd_classify(args):
    result = core.classify(args.module, args.exercise)
    if result["verdict"] == "REFUSE":
        line_part = f" [line {result['line']}]" if result.get("line") else ""
        print(f"REFUSE: {result['reason']}{line_part}")
    else:
        print("GATEABLE")
    return 0


def _cmd_verify(args):
    trace = json.loads(Path(args.trace).read_text())
    result = core.verify(trace, args.module)
    if result["verdict"] == "PASS":
        print("PASS")
        return 0
    if result["verdict"] == "REFUSE":
        line_part = f" [line {result['line']}]" if result.get("line") else ""
        print(f"REFUSE: {result['reason']}{line_part}")
        return 20
    print(f"FAIL: diverged on input {result['input']!r}", file=sys.stdout)
    print(f"  expected: {result['expected']}", file=sys.stderr)
    print(f"  got:      {result['got']}", file=sys.stderr)
    return 10


def _cmd_gate(args):
    try:
        result = core.run_case(args.case)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1

    print(json.dumps({"verdict": result["verdict"]}))

    print(f"-- gate --case {args.case} --", file=sys.stderr)
    if result["verdict"] == "REFUSE":
        source = result.get("verify_refuse") or result["classification"]
        line_part = f" [line {source['line']}]" if source.get("line") else ""
        print(f"REFUSE: {source['reason']}{line_part}", file=sys.stderr)
    elif result["verdict"] == "FAIL":
        v = result["verify"]
        print(f"FAIL: diverged on input {v['input']!r}", file=sys.stderr)
        print(f"  expected: {v['expected']}", file=sys.stderr)
        print(f"  got:      {v['got']}", file=sys.stderr)
    else:
        print("PASS", file=sys.stderr)
    print(result["coverage"], file=sys.stderr)
    return 0


def _cmd_demo(args):
    render_demo()
    return 0


def main(argv=None):
    parser = _build_parser()
    args = parser.parse_args(argv)
    handlers = {
        "record": _cmd_record,
        "classify": _cmd_classify,
        "verify": _cmd_verify,
        "gate": _cmd_gate,
        "demo": _cmd_demo,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
