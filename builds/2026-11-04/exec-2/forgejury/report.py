"""Human-readable rendering of a grade() report."""
from __future__ import annotations

from pathlib import Path


def _short(build: str) -> str:
    return Path(build).name


def _fmt_axis(axis: dict) -> str:
    lines = []
    for key, value in axis.items():
        if key.endswith("_detail"):
            continue
        detail = axis.get(f"{key}_detail")
        suffix = f"  ({detail})" if detail else ""
        lines.append(f"      {key:<28} {value}{suffix}")
    return "\n".join(lines) if lines else "      (none declared)"


def format_human_report(report: dict) -> str:
    out = ["=== Forgejury verdict ==="]

    for build in report["builds"]:
        out.append("")
        out.append(f"[{_short(build['build'])}] verdict={build['verdict']}")
        out.append("    spec axis:")
        out.append(_fmt_axis(build["spec_axis"]))
        out.append("    claims axis:")
        out.append(_fmt_axis(build["claims_axis"]))

    out.append("")
    out.append("=== Consensus (behavioral, stdout-only) ===")
    for fixture, data in report["consensus"].items():
        line = f"  {fixture}: {data['label']}"
        if data.get("diverging_build"):
            line += f"  <- diverging: {_short(data['diverging_build'])}"
        out.append(line)

        expected_match = data.get("expected_match")
        if expected_match:
            for build, result in expected_match.items():
                out.append(f"      expected-match[{_short(build)}]: {result}")

        errors = data.get("errors")
        if errors:
            for build, err in errors.items():
                out.append(f"      error[{_short(build)}]: {err}")

    return "\n".join(out)
