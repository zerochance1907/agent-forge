"""Layer 2: behavioral/stdout-only consensus across build dirs. An attention router,
not a correctness oracle. 3-0 agree -> bedrock. 2-1 split -> route attention to the
diverging build. 3-way split -> the fixture itself is ambiguous (valid only because
layer 0 already rejected volatile fixtures)."""

import subprocess

from .canon import canonicalize

AGREE_3_0 = "3-0"
SPLIT_2_1 = "2-1"
SPLIT_3_WAY = "3-way"


def run_invoke(build_dir, invoke_template, fixture_input, timeout=30):
    """Substitute {input} and run the invocation with cwd=build_dir."""
    cmd = invoke_template.replace("{input}", fixture_input)
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=build_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return canonicalize(proc.stdout), proc.returncode
    except subprocess.TimeoutExpired:
        return "<TIMEOUT>", None


def classify_fixture(build_dirs, invoke_template, fixture):
    """Run one fixture against every build dir, group by canonical stdout.

    Returns a dict with per-build raw output, the agreement class, the diverging
    build (only set on a 2-1 split), and a pinned-expected PASS/FAIL per build
    when fixture['expected'] is present.
    """
    outputs = {}
    for build_dir in build_dirs:
        stdout, _rc = run_invoke(build_dir, invoke_template, fixture["input"])
        outputs[build_dir] = stdout

    groups = {}
    for build_dir, out in outputs.items():
        groups.setdefault(out, []).append(build_dir)

    diverging_build = None
    if len(groups) == 1:
        agreement = AGREE_3_0
    elif len(groups) == 2:
        agreement = SPLIT_2_1
        minority = min(groups.values(), key=len)
        if len(minority) == 1:
            diverging_build = minority[0]
    else:
        agreement = SPLIT_3_WAY

    expected = fixture.get("expected")
    correctness = None
    if expected is not None:
        expected_canon = canonicalize(expected)
        correctness = {
            build_dir: ("PASS" if out == expected_canon else "FAIL")
            for build_dir, out in outputs.items()
        }

    return {
        "fixture": fixture["name"],
        "outputs": outputs,
        "agreement": agreement,
        "diverging_build": diverging_build,
        "correctness": correctness,
    }


def run_consensus(build_dirs, consensus_block):
    invoke_template = consensus_block["invoke"]
    return [
        classify_fixture(build_dirs, invoke_template, fixture)
        for fixture in consensus_block["fixtures"]
    ]
