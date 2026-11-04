---
cycle: 2026-11-04
from: exec-3
to: reviewer
stage: build
type: build-report
blocking: false
---

# Forgejury (exec-3, wild experimentalist): layers 0-2 complete, full demo green, plus a literal triangulation diagram

Built in `builds/2026-11-04/exec-3/`. All required layers (0 lint, 1 spec+claims
axis, 2 consensus) are done and the exact two demo commands from SPEC.md and the
decision memo produce the described output. Layer 3 (fence) was dropped
deliberately per the decision memo's own guidance ("drop this first if time is
short" / near-zero dogfood value this cycle) — everything else got the time
instead.

## Acceptance criteria (1-12), checked against the real run below

1. **Met.** `python -m forgejury` with `lint`/`grade` subcommands; `grep -n "^import\|^from" forgejury/*.py` shows only stdlib (`ast`, `json`, `os`, `re`, `subprocess`, `argparse`, `sys`) plus intra-package imports.
2. **Met.** `lint` hard-fails (exit 1) with named errors on missing `spec_checks`/`consensus` keys and a missing `{input}` placeholder — verified separately against a deliberately broken spec.
3. **Met.** Determinism warnings fire on date, hex-address, and UUID patterns (unit-tested in `tests/test_block.py`); demo spec triggers date + hex-address on the same fixture.
4. **Met.** Spec axis: `requires_file` (os.path), `requires_symbol` (real `ast.walk`, not grep — checks nested defs/classes/assigns too), `test_cmd` exit-0 gate, all independently observed per build dir.
5. **Met.** Claims axis catches `build-b`'s lie and **names the field**: `tests_passed` claimed `3`, observed `2`; `test_cmd_exit` claimed `0`, observed `1`.
6. **Met.** Consensus runs `invoke` per fixture per build, canonicalizes (CRLF→LF + per-line rstrip, in `canon.py`, unit-tested), classifies 3-0/2-1/3-way, names the diverging build on 2-1 (`examples/build-c` on `boundary-bug`).
7. **Met.** `grade --json` validated via `json.loads` in both my manual run and `tests/test_cli_examples.py`. One deliberate interpretation call: SPEC.md's prose for the top-level `consensus` schema (`{<fixture>: "3-0|2-1|3-way", "diverging_build": "<dir|null>"}`) is ambiguous for >1 fixture (a single flat `diverging_build` can't name which fixture it belongs to if several diverge). I implemented it literally for the common case — when at most one fixture has a 2-1 split (true for your own single-fixture `triangulated-verdict` invocation), `diverging_build` is exactly the flat `<dir|null>` the prose describes. Only if *multiple* fixtures diverge does it become a `{fixture: dir}` map instead of silently dropping data. See `report.py` docstring.
8. **Met.** `examples/` has all four demonstrated cases in one `grade` call (output below).
9. **Met.** `tests/` has 31 tests (unit + a real subprocess-level CLI integration test against the bundled examples), `python -m pytest -q` exits 0.
10. **Met.** Both honesty statements are in README.md verbatim, under their own heading.
11. **Met.** Consensus is stdout-diff only; no AST diffing anywhere in `consensus.py`.
12. **Met.** Ran entirely on Windows / Python 3.13.5 / git-bash, no network calls, no GPU.

## The twist (persona: push one step past spec, make it actually work)

The spec's own framing is "one **triangulated** verdict" — so the human-readable
`grade` report (not `--json`, which stays schema-stable) ends with a literal
triangle: one vertex per build, each edge labeled with how many of the shared
fixtures that pair agreed on, colored green/yellow/red by ratio (ANSI, degrades
to plain text under `NO_COLOR`/non-tty). It's a real aggregate computed from
`fixture_results`, not a static diagram — see the real rendering below where
A-B agree 4/5 but both only agree with C 3/5, visually pointing at the
odd-one-out before you've read a single row of text.

## Demo commands and real output

Setup (one-time, pytest isn't a forgejury dependency — it's only invoked as a
subprocess because the toy `examples/` builds chose it as their test runner):

```
python -m venv .venv
.venv/Scripts/python.exe -m pip install pytest
export PATH="$(pwd)/.venv/Scripts:$PATH"
```

```
$ python -m forgejury lint examples/SPEC.md
WARNING: consensus.fixtures[4] ('seeded-volatile'): expected output looks volatile (date: '2026-11-04') -- pin a stable value or the 3-way consensus signal becomes indistinguishable from real nondeterminism
WARNING: consensus.fixtures[4] ('seeded-volatile'): expected output looks volatile (hex-address: '0xdeadbeef') -- pin a stable value or the 3-way consensus signal becomes indistinguishable from real nondeterminism
LINT OK (2 warning(s))

$ python -m forgejury grade examples/SPEC.md examples/build-a examples/build-b examples/build-c
=== Forgejury verdict ===

[examples/build-a] -> PASS
  spec axis: requires_file:app.py PASS, requires_file:tests/test_app.py PASS,
    requires_symbol:app.py::classify PASS, test_cmd_exit_0 PASS, expected_tests_pass PASS
  claims axis: files PASS, symbols PASS, test_cmd_exit PASS, tests_passed PASS

[examples/build-b] -> FAIL
  spec axis: ... test_cmd_exit_0 FAIL, expected_tests_pass FAIL
  claims axis: files PASS, symbols PASS,
    test_cmd_exit FAIL (claimed 0, observed 1),
    tests_passed FAIL (claimed 3, observed 2)

[examples/build-c] -> PASS
  spec axis: all PASS
  claims axis: all PASS

=== Consensus (behavioral, stdout-only) ===
  small-even: 3-0
  small-odd: 3-0
  boundary-bug: 2-1  <- diverging build: examples/build-c  pinned-expected FAIL: ['examples/build-c']
  negative-triway: 3-way
  seeded-volatile: 3-0  pinned-expected FAIL: ['examples/build-a', 'examples/build-b', 'examples/build-c']

Triangulation (pairwise fixture agreement):

        [A]
        / \
   4/5   3/5
      /     \
   [B] --- 3/5 --- [C]

  A = build-a
  B = build-b
  C = build-c

$ python -m pytest -q
...............................                                          [100%]
31 passed in 12.32s
```

(Full untruncated output and all source is in the build dir; this is trimmed
for the memo.)

## Known gaps

- Layer 3 (fence) not built — optional, not graded, dropped per the decision
  memo's own call.
- `--json` `diverging_build` interpretation call documented above (point 7) —
  flag if you read it differently; easy one-line change either way.
- `tests/test_cli_examples.py` shells out to `python -m forgejury ...` via
  `sys.executable`, but Forgejury's *own* internal `grade` subprocess calls
  (running each toy build's `test_cmd`/`invoke`) use a bare `python` found on
  `PATH` — so the demo requires a `pytest`-capable `python` on `PATH`, not
  just `sys.executable`. Documented in README's Setup section; this is a
  property of the spec's "test_cmd run with cwd = build dir" contract, not
  something Forgejury itself could sidestep without hardcoding an
  interpreter.

## Licenses

No upstream code vendored or copied. `Balanov/verdict` (Apache-2.0) and
`Balanov/skein` (MIT) — read for framing only (verify-real-state-vs-trust-
report; epoch fencing for the unbuilt layer 3), no code taken.
`Graphify-Labs/graphify` (Apache-2.0) — not consulted; stdlib `ast` was
sufficient. `pytest` (MIT) is invoked as a subprocess by the bundled toy
examples and by this build's own `test_cmd`, never imported by `forgejury/`.
