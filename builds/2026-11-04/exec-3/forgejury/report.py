"""Human-readable verdict table + the stable --json schema, plus the triangulation
diagram: a literal triangle connecting the three builds, edges colored by how often
each pair agreed across every consensus fixture. Forgejury triangulates a verdict --
this makes that word literal instead of just a name."""

import json
import os
import sys

_GREEN = "\x1b[32m"
_RED = "\x1b[31m"
_YELLOW = "\x1b[33m"
_BOLD = "\x1b[1m"
_RESET = "\x1b[0m"


def _color_enabled():
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return sys.stdout.isatty()


def _c(text, color, enabled):
    return f"{color}{text}{_RESET}" if enabled else text


def build_verdict_json(build_dirs, spec_results, claims_results, fixture_results):
    """Assemble the stable schema pinned in SPEC.md's Interface section:
    per build {build, spec_axis, claims_axis, verdict}, plus top-level
    consensus = {<fixture>: "3-0|2-1|3-way", ..., "diverging_build": <dir|null>}.

    diverging_build is flat (a single dir, matching the pinned schema exactly)
    whenever at most one fixture has a 2-1 split -- true for the single-fixture
    "triangulated-verdict" invocation the reviewer actually runs. If more than
    one fixture diverges (only possible with a multi-fixture block, like the
    bundled examples/), it falls back to a {fixture: dir} map so no divergence
    is silently dropped.
    """
    out = {"builds": [], "consensus": {}}
    for build_dir in build_dirs:
        spec_axis, spec_pass = spec_results[build_dir]
        claims_axis, _details = claims_results[build_dir]
        verdict = "PASS" if (spec_pass and "FAIL" not in claims_axis.values()) else "FAIL"
        out["builds"].append(
            {
                "build": build_dir,
                "spec_axis": spec_axis,
                "claims_axis": claims_axis,
                "verdict": verdict,
            }
        )

    divergences = {}
    for fx in fixture_results:
        out["consensus"][fx["fixture"]] = fx["agreement"]
        if fx["diverging_build"]:
            divergences[fx["fixture"]] = fx["diverging_build"]

    if len(divergences) <= 1:
        out["consensus"]["diverging_build"] = next(iter(divergences.values()), None)
    else:
        out["consensus"]["diverging_build"] = divergences
    return out


def print_json_verdict(build_dirs, spec_results, claims_results, fixture_results):
    doc = build_verdict_json(build_dirs, spec_results, claims_results, fixture_results)
    print(json.dumps(doc, indent=2))


def _short(build_dir):
    return os.path.basename(os.path.normpath(build_dir))


def render_triangle(build_dirs, fixture_results):
    """Render a literal triangle: one vertex per build, edges scored by pairwise
    fixture agreement across the whole consensus run. Only drawn for exactly 3 builds
    -- that's Forgejury's N, and the shape should say so."""
    if len(build_dirs) != 3:
        return ""

    color = _color_enabled()
    names = [_short(b) for b in build_dirs]
    letters = ["A", "B", "C"]
    legend = "\n".join(f"  {letters[i]} = {names[i]}" for i in range(3))

    total = len(fixture_results) or 1
    pair_agree = {}
    for (i, j) in [(0, 1), (0, 2), (1, 2)]:
        agree = 0
        for fx in fixture_results:
            out_i = fx["outputs"].get(build_dirs[i])
            out_j = fx["outputs"].get(build_dirs[j])
            if out_i == out_j:
                agree += 1
        pair_agree[(i, j)] = (agree, total)

    def edge_label(i, j):
        agree, tot = pair_agree[(i, j)]
        if agree == tot:
            return _c(f"{agree}/{tot}", _GREEN, color)
        if agree == 0:
            return _c(f"{agree}/{tot}", _RED, color)
        return _c(f"{agree}/{tot}", _YELLOW, color)

    a_label = _c(f"[{letters[0]}]", _BOLD, color)
    b_label = _c(f"[{letters[1]}]", _BOLD, color)
    c_label = _c(f"[{letters[2]}]", _BOLD, color)

    ab = edge_label(0, 1)
    ac = edge_label(0, 2)
    bc = edge_label(1, 2)

    diagram = (
        f"        {a_label}\n"
        f"        / \\\n"
        f"   {ab}   {ac}\n"
        f"      /     \\\n"
        f"   {b_label} --- {bc} --- {c_label}\n"
    )
    return "Triangulation (pairwise fixture agreement):\n\n" + diagram + "\n" + legend + "\n"


def print_human_report(build_dirs, spec_results, claims_results, fixture_results, spec_checks):
    color = _color_enabled()

    def status(s):
        if s == "PASS":
            return _c(s, _GREEN, color)
        if s == "FAIL":
            return _c(s, _RED, color)
        return _c(s, _YELLOW, color)

    print(_c("=== Forgejury verdict ===", _BOLD, color))
    for build_dir in build_dirs:
        spec_axis, spec_pass = spec_results[build_dir]
        claims_axis, details = claims_results[build_dir]
        overall = "PASS" if (spec_pass and "FAIL" not in claims_axis.values()) else "FAIL"
        print(f"\n[{build_dir}] -> {status(overall)}")
        print("  spec axis:")
        for check, s in spec_axis.items():
            print(f"    {check}: {status(s)}")
        print("  claims axis:")
        for field, s in claims_axis.items():
            extra = f" ({details[field]})" if field in details else ""
            print(f"    {field}: {status(s)}{extra}")

    print(f"\n{_c('=== Consensus (behavioral, stdout-only) ===', _BOLD, color)}")
    for fx in fixture_results:
        line = f"  {fx['fixture']}: {status(fx['agreement'])}"
        if fx["diverging_build"]:
            line += f"  <- diverging build: {fx['diverging_build']}"
        if fx["correctness"]:
            mismatches = [b for b, s in fx["correctness"].items() if s == "FAIL"]
            if mismatches:
                line += f"  pinned-expected FAIL: {mismatches}"
        print(line)

    triangle = render_triangle(build_dirs, fixture_results)
    if triangle:
        print()
        print(triangle)
