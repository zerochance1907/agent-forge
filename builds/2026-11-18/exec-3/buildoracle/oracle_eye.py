"""The demo's one indulgence: render each verdict as a small ASCII sigil, and
for the keyorder case, print live proof — real repr strings from this exact
run — that the PASS happened *because* canonicalize() ran, not because
dict.__eq__ already ignores key order. Nothing here is scripted flavor text;
every value printed comes out of an actual record()/canonicalize() call made
during this render.
"""

from . import core

_SIGIL_PASS = """\
      .--.
     ( ^  ^ )   the oracle nods: behavior preserved
      \\  ~  /
       `--'"""

_SIGIL_FAIL = """\
      .--.
     ( x  x )   the mirror cracks: a divergence was caught
      \\  !  /
       `--'"""

_SIGIL_REFUSE = """\
      .--.
     ( -  - )   the oracle's eye stays shut: it will not guess
      \\  ?  /
       `--'"""

_SIGILS = {"PASS": _SIGIL_PASS, "FAIL": _SIGIL_FAIL, "REFUSE": _SIGIL_REFUSE}


def _print_canonicalization_proof(trace):
    case_dir = core.CASES_DIR / "keyorder"
    refactored_trace = core.record(case_dir / "refactored.py", case_dir / "exercise.py")

    original_output = trace["events"][0]["output"]
    refactored_output = refactored_trace["events"][0]["output"]

    raw_equal = repr(original_output) == repr(refactored_output)
    canon_a = core.canonicalize(original_output)
    canon_b = core.canonicalize(refactored_output)

    print("  proof of canonicalization (live, from this run's first recorded input):")
    print(f"    raw repr (original):   {original_output!r}")
    print(f"    raw repr (refactored): {refactored_output!r}")
    print(f"    raw reprs identical?    {raw_equal}")
    print(f"    canonical forms equal?  {canon_a == canon_b}  <- this is why verify() says PASS")


def render_demo():
    print("=" * 66)
    print("BuildOracle demo: record -> classify-then-refuse -> canonicalize -> verify")
    print("=" * 66)

    rows = []
    for case_name in core.BUNDLED_CASES:
        result = core.run_case(case_name)
        verdict = result["verdict"]
        rows.append((case_name, verdict))

        print(f"\ncase: {case_name}")
        print(_SIGILS[verdict])

        if verdict == "REFUSE":
            source = result.get("verify_refuse") or result["classification"]
            line_part = f" [line {source['line']}]" if source.get("line") else ""
            print(f"  REFUSE: {source['reason']}{line_part}")
        elif verdict == "FAIL":
            v = result["verify"]
            print(f"  FAIL: diverged on input {v['input']!r}")
            print(f"    expected: {v['expected']}")
            print(f"    got:      {v['got']}")
        else:
            print("  PASS: replayed trace matched the refactor on every recorded input.")
            if case_name == "keyorder":
                _print_canonicalization_proof(result["trace"])

        print(f"  {result['coverage']}")

    print("\n" + "-" * 66)
    print("summary")
    for name, verdict in rows:
        print(f"  {name:<18} -> {verdict}")
    print("-" * 66)
