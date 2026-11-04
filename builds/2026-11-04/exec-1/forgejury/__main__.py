"""Forgejury CLI. stdlib only. `python -m forgejury lint|grade ...`"""
import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

HEADING_RE = re.compile(r"^## Forgejury Acceptance Block\s*$", re.MULTILINE)

DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
HEX_ADDR_RE = re.compile(r"\b0x[0-9a-fA-F]+\b")
UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
TEMP_PATH_RE = re.compile(r"(/tmp/|\\Temp\\|^[A-Za-z]:\\|^/)", re.IGNORECASE)


# ---------------------------------------------------------------- parsing --

def parse_acceptance_block(spec_path):
    """Extract and json-decode the fenced ```json block under the heading.

    Matches the heading only as its own markdown line (not an inline mention
    in prose), and uses the last such heading if more than one exists.
    """
    text = Path(spec_path).read_text(encoding="utf-8")
    matches = list(HEADING_RE.finditer(text))
    if not matches:
        raise ValueError("spec is missing the '## Forgejury Acceptance Block' heading")
    after = text[matches[-1].end():]
    fence_start = after.find("```json")
    if fence_start == -1:
        raise ValueError("no ```json fenced block found after the heading")
    after = after[fence_start + len("```json"):]
    fence_end = after.find("```")
    if fence_end == -1:
        raise ValueError("unterminated ```json fenced block")
    raw = after[:fence_end]
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"acceptance block is not valid JSON: {exc}") from exc


# -------------------------------------------------------------------- lint --

def lint(spec_path):
    """Return (errors, warnings), both lists of strings."""
    errors = []
    warnings = []
    try:
        block = parse_acceptance_block(spec_path)
    except ValueError as exc:
        return [str(exc)], warnings

    spec_checks = block.get("spec_checks")
    if not isinstance(spec_checks, dict):
        errors.append("missing required key: spec_checks")
        spec_checks = {}
    else:
        if not spec_checks.get("requires_file"):
            errors.append("spec_checks.requires_file is required and must be non-empty")
        if "requires_symbol" not in spec_checks:
            errors.append("spec_checks.requires_symbol is required")
        if not spec_checks.get("test_cmd"):
            errors.append("spec_checks.test_cmd is required and must be non-empty")

    consensus = block.get("consensus")
    if not isinstance(consensus, dict):
        errors.append("missing required key: consensus")
        consensus = {}
    else:
        invoke = consensus.get("invoke")
        if not invoke:
            errors.append("consensus.invoke is required")
        elif "{input}" not in invoke:
            errors.append("consensus.invoke must contain the '{input}' placeholder")

        fixtures = consensus.get("fixtures")
        if not fixtures:
            errors.append("consensus.fixtures must be a non-empty list")
        else:
            for i, fx in enumerate(fixtures):
                if "name" not in fx or "input" not in fx:
                    errors.append(f"fixture[{i}] missing 'name' or 'input'")
                    continue
                expected = fx.get("expected")
                if expected is not None:
                    warnings.extend(_determinism_warnings(fx["name"], expected))
    return errors, warnings


def _determinism_warnings(fixture_name, expected):
    warns = []
    if DATE_RE.search(expected):
        warns.append(f"fixture '{fixture_name}': expected output looks like a date")
    if HEX_ADDR_RE.search(expected):
        warns.append(f"fixture '{fixture_name}': expected output looks like a hex address")
    if UUID_RE.search(expected):
        warns.append(f"fixture '{fixture_name}': expected output looks like a UUID")
    if TEMP_PATH_RE.search(expected):
        warns.append(f"fixture '{fixture_name}': expected output looks like a temp/absolute path")
    return warns


# ------------------------------------------------------------------- grade --

def run_cmd(cmd, cwd):
    """Run cmd via shell in cwd. Return (exit_code, stdout, stderr)."""
    proc = subprocess.run(
        cmd, cwd=cwd, shell=True, capture_output=True, text=True
    )
    return proc.returncode, proc.stdout, proc.stderr


def canonicalize(text):
    """Strip trailing whitespace per line and normalize line endings."""
    return "\n".join(line.rstrip() for line in text.splitlines())


def file_exists(build_dir, rel_path):
    return (Path(build_dir) / rel_path).is_file()


def symbol_defined(build_dir, symbol_ref):
    """symbol_ref is 'relative/path.py::name'. Walk the whole AST for a def."""
    rel_path, _, name = symbol_ref.partition("::")
    path = Path(build_dir) / rel_path
    if not path.is_file():
        return False
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name == name:
                return True
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                if isinstance(t, ast.Name) and t.id == name:
                    return True
    return False


_PASS_COUNT_RE = re.compile(r"(\d+)\s+passed")


def count_tests_passed(stdout):
    """Best-effort parse of a pytest summary line like '3 passed in 0.01s'."""
    match = _PASS_COUNT_RE.search(stdout)
    return int(match.group(1)) if match else None


def grade_build(spec_checks, build_dir, claims):
    spec_axis = {}
    for rel_path in spec_checks.get("requires_file", []):
        spec_axis[f"requires_file:{rel_path}"] = (
            "PASS" if file_exists(build_dir, rel_path) else "FAIL"
        )
    for sym in spec_checks.get("requires_symbol", []):
        spec_axis[f"requires_symbol:{sym}"] = (
            "PASS" if symbol_defined(build_dir, sym) else "FAIL"
        )

    test_cmd = spec_checks.get("test_cmd")
    exit_code, stdout, _stderr = (None, "", "")
    if test_cmd:
        exit_code, stdout, _stderr = run_cmd(test_cmd, build_dir)
        spec_axis["test_cmd"] = "PASS" if exit_code == 0 else "FAIL"

    runner = spec_checks.get("runner")
    observed_tests_passed = count_tests_passed(stdout) if runner == "pytest" else None

    claims_axis = {}
    if claims is None:
        claims = {}
        claims_present = False
    else:
        claims_present = True

    if "files" in claims:
        bad = [f for f in claims["files"] if not file_exists(build_dir, f)]
        claims_axis["files"] = "FAIL: claimed but missing: " + ", ".join(bad) if bad else "PASS"
    else:
        claims_axis["files"] = "UNVERIFIABLE"

    if "symbols" in claims:
        bad = [s for s in claims["symbols"] if not symbol_defined(build_dir, s)]
        claims_axis["symbols"] = "FAIL: claimed but missing: " + ", ".join(bad) if bad else "PASS"
    else:
        claims_axis["symbols"] = "UNVERIFIABLE"

    if "test_cmd_exit" in claims and exit_code is not None:
        claims_axis["test_cmd_exit"] = (
            "PASS" if claims["test_cmd_exit"] == exit_code
            else f"FAIL: claimed {claims['test_cmd_exit']}, observed {exit_code}"
        )
    else:
        claims_axis["test_cmd_exit"] = "UNVERIFIABLE"

    if runner == "pytest" and "tests_passed" in claims:
        if observed_tests_passed is None:
            claims_axis["tests_passed"] = "UNVERIFIABLE"
        else:
            claims_axis["tests_passed"] = (
                "PASS" if claims["tests_passed"] == observed_tests_passed
                else f"FAIL: claimed {claims['tests_passed']}, observed {observed_tests_passed}"
            )
    else:
        claims_axis["tests_passed"] = "UNVERIFIABLE"

    if not claims_present:
        claims_axis = {k: "UNVERIFIABLE" for k in claims_axis}

    spec_fail = any(v == "FAIL" for v in spec_axis.values())
    claims_fail = any(str(v).startswith("FAIL") for v in claims_axis.values())
    verdict = "FAIL" if (spec_fail or claims_fail) else "PASS"

    return {
        "build": str(build_dir),
        "spec_axis": spec_axis,
        "claims_axis": claims_axis,
        "verdict": verdict,
    }


def grade_consensus(consensus, build_dirs):
    invoke_tpl = consensus.get("invoke", "")
    fixtures = consensus.get("fixtures", [])
    result = {}
    for fx in fixtures:
        cmd = invoke_tpl.replace("{input}", fx.get("input", ""))
        outputs = {}
        for build_dir in build_dirs:
            _code, stdout, _err = run_cmd(cmd, build_dir)
            outputs[str(build_dir)] = canonicalize(stdout)

        counts = {}
        for build_dir, out in outputs.items():
            counts.setdefault(out, []).append(build_dir)

        if len(counts) == 1:
            classification = f"{len(build_dirs)}-0"
            diverging = None
        elif len(counts) == len(build_dirs):
            classification = f"{len(build_dirs)}-way"
            diverging = None
        else:
            majority_group = max(counts.values(), key=len)
            minority = [b for group in counts.values() if group is not majority_group for b in group]
            classification = f"{len(majority_group)}-{len(minority)}"
            diverging = minority[0] if len(minority) == 1 else minority

        entry = {"classification": classification, "diverging_build": diverging}

        expected = fx.get("expected")
        if expected is not None:
            exp_canon = canonicalize(expected)
            entry["expected_match"] = {
                build_dir: (out == exp_canon) for build_dir, out in outputs.items()
            }

        result[fx["name"]] = entry
    return result


def format_table(build_results, consensus_results):
    lines = []
    for res in build_results:
        lines.append(f"== {res['build']} :: verdict {res['verdict']} ==")
        lines.append("  spec axis:")
        for k, v in res["spec_axis"].items():
            lines.append(f"    {k}: {v}")
        lines.append("  claims axis:")
        for k, v in res["claims_axis"].items():
            lines.append(f"    {k}: {v}")
    lines.append("== consensus ==")
    for name, entry in consensus_results.items():
        lines.append(f"  {name}: {entry['classification']}  diverging={entry['diverging_build']}")
        if "expected_match" in entry:
            lines.append(f"    expected_match: {entry['expected_match']}")
    return "\n".join(lines)


def load_claims(build_dir):
    path = Path(build_dir) / "claims.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


# --------------------------------------------------------------------- cli --

def cmd_lint(args):
    errors, warnings = lint(args.spec)
    for w in warnings:
        print(f"WARNING: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    if errors:
        print(f"lint FAILED: {len(errors)} error(s)")
        return 1
    print(f"lint OK ({len(warnings)} warning(s))")
    return 0


def cmd_grade(args):
    try:
        block = parse_acceptance_block(args.spec)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    spec_checks = block.get("spec_checks", {})
    consensus = block.get("consensus", {})

    build_results = [
        grade_build(spec_checks, b, load_claims(b)) for b in args.build_dirs
    ]
    consensus_results = grade_consensus(consensus, args.build_dirs)

    if args.json:
        print(json.dumps({"builds": build_results, "consensus": consensus_results}, indent=2))
    else:
        print(format_table(build_results, consensus_results))

    return 0 if all(r["verdict"] == "PASS" for r in build_results) else 1


def main(argv=None):
    parser = argparse.ArgumentParser(prog="forgejury")
    sub = parser.add_subparsers(dest="command", required=True)

    p_lint = sub.add_parser("lint", help="validate an acceptance block")
    p_lint.add_argument("spec")
    p_lint.set_defaults(func=cmd_lint)

    p_grade = sub.add_parser("grade", help="grade build dirs against an acceptance block")
    p_grade.add_argument("spec")
    p_grade.add_argument("build_dirs", nargs="+")
    p_grade.add_argument("--json", action="store_true")
    p_grade.set_defaults(func=cmd_grade)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
