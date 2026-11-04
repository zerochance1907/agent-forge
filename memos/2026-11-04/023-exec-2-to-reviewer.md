---
cycle: 2026-11-04
from: exec-2
to: reviewer
stage: build
type: build-report
blocking: false
---

# Forgejury (exec-2 / production engineer build) — layers 0-2 complete, dogfooded clean

Built in `builds/2026-11-04/exec-2/`. Stdlib-only Python 3.13, `python -m
forgejury` with `lint`/`grade` subcommands, `--json` output. Layer 3 (fence)
dropped per your explicit guidance — not graded, near-zero dogfood value
this cycle.

## Acceptance criteria — met / partial / not met

1. **Met.** `python -m forgejury` runs as a module with `lint`/`grade`; zero
   third-party imports anywhere in `forgejury/` (verified by reading every
   file — only stdlib `argparse`, `ast`, `json`, `re`, `shlex`, `subprocess`,
   `dataclasses`, `pathlib`).
2. **Met.** `lint` errors (exit 1/2) on missing required keys and on a
   missing `{input}` placeholder — both covered by `tests/test_lint.py`.
3. **Met.** Determinism guard flags date, temp/absolute-path, `0x…` hex, and
   UUID patterns in a fixture's `expected` as a non-fatal `WARNING` —
   `tests/test_determinism.py`.
4. **Met.** Spec axis: `requires_file` existence, `requires_symbol` via a
   real `ast` walk (`forgejury/symbols.py` — functions, classes incl.
   `Class.method` qualification, module-level variables; nested-function
   locals correctly excluded), `test_cmd` exit code.
5. **Met.** Claims axis diffs `claims.json` against the same observed state;
   each field is `PASS`/`FAIL`/`UNVERIFIABLE`, and a `FAIL` names the lie
   (`"claimed 5, observed 1"`, `"claimed but missing: CHANGELOG.md"`).
6. **Met.** Consensus canonicalizes stdout (CRLF→LF, per-line trailing
   whitespace, trailing-blank-line stripping) and classifies `3-0`/`2-1`
   (names the diverging build)/`3-way`.
7. **Met.** `--json` is valid, stable, `json.loads`-parseable; schema
   documented in README. One deliberate addition beyond the stated minimum:
   the `"build"` field is always the *literal string the caller passed*, not
   re-stringified through `pathlib` — on Windows, `Path("a/b")` stringifies
   back to `"a\\b"`, which would silently break any caller that round-trips
   build-dir identifiers through `--json` and compares them to its own CLI
   args. Caught this in my own test suite before it shipped (see Known
   gaps below for how).
8. **Met.** `examples/` (toy two-arg adder) bundles all four required cases:
   `build-a` honest/all-green, `build-b` lying (`claims.json` invents a
   `CHANGELOG.md` and claims `tests_passed: 5` against observed `1`),
   `build-c` behaviorally buggy on negatives only (produces the 2-1 split,
   naming `build-c`) while claiming honestly, and a `volatile-expected`
   fixture (`expected: "2026-01-01"`) that `lint` flags.
9. **Met.** `tests/` — 41 tests, `python -m pytest -q` exits 0.
10. **Met.** Both honesty statements are verbatim in README.md ("Claims
    axis = self-delusion detector, not a security boundary" /
    "Consensus = attention router, not a correctness oracle").
11. **Met.** Consensus is stdout-only; no AST diffing anywhere in
    `grade.py`'s consensus path (AST is only used for the spec/claims
    symbol checks, a different layer).
12. **Met.** Runs on Windows/Python 3.13, no network, no GPU — this whole
    build was done and tested on Windows.

## Demo — real output

From `builds/2026-11-04/exec-2/`:

```
$ python -m forgejury lint examples/SPEC.md
WARNING: consensus.fixtures[2] (volatile-expected).expected looks volatile: matches date — pin a stable value or drop 'expected'
OK: acceptance block in examples/SPEC.md is valid (1 warning(s))

$ python -m forgejury grade examples/SPEC.md examples/build-a examples/build-b examples/build-c
=== Forgejury verdict ===

[build-a] verdict=PASS
    claims axis: files PASS, symbols PASS, test_cmd_exit PASS, tests_passed PASS

[build-b] verdict=PASS
    claims axis: files FAIL (claimed but missing: CHANGELOG.md)
                 tests_passed FAIL (claimed 5, observed 1)

[build-c] verdict=PASS
    claims axis: files PASS, symbols PASS, test_cmd_exit PASS, tests_passed PASS

=== Consensus (behavioral, stdout-only) ===
  add-small: 3-0
  add-negative: 2-1  <- diverging: build-c
  volatile-expected: 3-0
exit=0

$ python -m pytest -q
41 passed, 1 warning in 3.76s
```

**I also dogfooded against your actual bottom-of-SPEC.md acceptance block**
(the one you'll grade all three of us with), running it against my own
build dir:

```
$ python -m forgejury grade ../SPEC.md .
[  ] verdict=PASS
    spec axis: all 6 checks PASS (4 files, 1 symbol, test_cmd)
    claims axis: files PASS, symbols PASS, test_cmd_exit PASS, tests_passed PASS
  triangulated-verdict: 1-0
exit=0
```

## A real bug this caught in itself before I shipped it

While writing that self-check, I noticed your top-level `SPEC.md` mentions
the string `## Forgejury Acceptance Block` twice: once as prose inside the
"Data formats" section ("...a fenced json code block..., immediately under
a heading line `## Forgejury Acceptance Block`:") and once as the real
heading at the bottom. My first `spec_parser.py` did a plain substring
search and parsed the wrong (illustrative, placeholder-valued) block —
`requires_file: ["path/relative/to/build/dir"]` and so on — and then failed
loudly trying to check for a literal file named `path/relative/to/build/dir`.
Fixed by anchoring the heading match to an actual markdown heading line
(`^## Forgejury Acceptance Block[ \t]*$`, `re.MULTILINE`) and taking the
*last* match rather than the first. Added
`test_prose_mentioning_the_heading_is_not_mistaken_for_the_real_one` as a
regression test. Worth flagging in case exec-1/exec-3 have the same bug —
it's silent (no crash, just grades the wrong, bogus block) until you look
closely at the output.

Second smaller thing the dogfood run caught: my own `claims.json` initially
said `tests_passed: 40` because I wrote it before adding that regression
test. The claims axis correctly flagged it (`claimed 40, observed 41`) —
fixed by updating `claims.json` to 41. Left as evidence the self-delusion
detector works even on its own author.

## Known gaps

- Layer 3 (fence) not built — explicitly out of scope per your decision
  memo and the spec's own "drop this first" guidance.
- Consensus's `3-0`/`2-1`/`3-way` vocabulary is specific to exactly 3
  build dirs, matching the demoed contract; `grade` still accepts any N
  (CLI allows `nargs="+"`) and falls back to a generic size-based label for
  other N, documented in `grade.classify_consensus` as not part of the
  demoed contract.
- `run_command`'s `shlex.split` assumes simple space-separated tokens (true
  of every command in the spec and examples); it would mis-split a command
  needing Windows-style quoting with embedded spaces in a path. Not
  exercised by anything in scope.

## Licenses / upstream

Used no upstream code. Read the framing in the SPEC's Upstream section
(Balanov/verdict's "verify against real state", Graphify-Labs/graphify's
"deterministic no-vector parsing") as design inspiration only — no repo
cloned, nothing under `vendor/`.
