# Forgejury (exec-2 / production engineer build)

A standard-library-only Python 3.13 gate on a build→review handoff. It reads
a machine-readable **acceptance block** embedded in a spec, independently
re-observes each build's state, diffs that against what the build's own
`claims.json` asserts, and diffs the builds against each other on a thin,
behavioral invocation contract.

## Setup

No install step and no dependencies for Forgejury itself — stdlib only.

```
python --version      # 3.13+
```

Running the bundled test suite requires `pytest` as a subprocess dependency
(Forgejury's own source imports nothing outside the standard library — only
`tests/` uses pytest):

```
python -m pip install --user pytest
```

Everything below is run with **cwd = this directory**
(`builds/2026-11-04/exec-2/`), so that `python -m forgejury` resolves the
`forgejury` package from the current working directory.

## Commands

```
python -m forgejury lint <spec.md>
python -m forgejury grade <spec.md> <build-dir> [<build-dir> ...]
python -m forgejury grade <spec.md> <build-dir> [<build-dir> ...] --json
```

- `lint` validates the acceptance block: fails loudly (exit 2 or non-zero on
  hard parse errors) on a missing required key or a missing `{input}`
  placeholder in `invoke`; emits a non-fatal `WARNING` when a fixture's
  pinned `expected` output looks volatile (matches a date, a temp/absolute
  path, a `0x…` address, or a UUID). Exit 0 iff there are no errors (warnings
  don't fail the gate).
- `grade` runs layer 1 (spec axis + claims axis per build, independently
  observed) and layer 2 (behavioral consensus across builds on each
  fixture). Exit 0 iff every build's spec axis is all-PASS; prints a
  human-readable table by default, or `--json` for the stable schema below.

### `--json` schema

```jsonc
{
  "builds": [
    {
      "build": "<dir>",                       // exactly the string you passed in
      "spec_axis": {"<check>": "PASS|FAIL"},
      "claims_axis": {"<field>": "PASS|FAIL|UNVERIFIABLE"},
      "verdict": "PASS|FAIL"
    }
  ],
  "consensus": {
    "<fixture-name>": {
      "label": "3-0|2-1|3-way",
      "diverging_build": "<dir>|null",
      "expected_match": {"<dir>": "PASS|FAIL"} ,  // null if the fixture has no pinned `expected`
      "outputs": {"<dir>": "<canonicalized stdout>"},
      "errors": {"<dir>": "<reason>"} // null if every build's invoke exited 0
    }
  }
}
```

`expected_match`, `outputs`, and `errors` are extra debugging fields beyond
the spec's minimum schema — kept because a production triage tool should let
you see *why*, not just the verdict. The `"build"` field is always exactly
the directory string you passed on the command line (not re-normalized
through `pathlib`), so round-tripping through `--json` and comparing against
your own CLI arguments always matches, on Windows or POSIX.

## Demo

```
python -m forgejury lint examples/SPEC.md
python -m forgejury grade examples/SPEC.md examples/build-a examples/build-b examples/build-c
```

`examples/` bundles a toy two-argument adder CLI spec and three toy builds
that together exercise every required signal:

- **`build-a`** — honest: correct behavior, `claims.json` matches reality.
- **`build-b`** — lying: behaviorally correct, but its `claims.json` claims a
  `CHANGELOG.md` that doesn't exist and `tests_passed: 5` against an observed
  `1`. The claims axis fails both, naming the exact lie in each case.
- **`build-c`** — honest claims, but a real bug: `add()` takes `abs()` of
  both operands, so it agrees with `build-a`/`build-b` on `add-small` (both
  positive) but disagrees on `add-negative`, producing a 2-1 consensus split
  that names `build-c` as the diverging build.
- A `volatile-expected` fixture pins `"2026-01-01"` as `expected` — `lint`
  flags this as a determinism warning before `grade` ever runs it.

## Honesty statements

- **Claims axis = self-delusion detector, not a security boundary.** It
  catches "the report says 12 tests passed, a fresh run sees 9" — drift
  between a report and reality. It does **not** survive an executioner who
  runs Forgejury themselves and tunes `claims.json` to match whatever it
  reports.
- **Consensus = attention router, not a correctness oracle.** With N=3, a
  2-1 majority can be two builds sharing the same wrong assumption while the
  "diverging" build is actually right. The gate points the reviewer's
  attention at a fixture; it does not decide correctness for them.

## Design notes

- **Spec axis** (`grade`, per build): every `requires_file` exists; every
  `requires_symbol` is defined, found via a `stdlib ast` walk (not grep) —
  `forgejury/symbols.py` walks module-level functions, classes (and their
  methods, qualified as `Class.method`), and module-level variable
  assignments. The floor gate is `test_cmd` exiting 0.
- **Claims axis** (`grade`, per build): diffs `claims.json` against the same
  observed state. `tests_passed` is only checked when the acceptance block
  declares a `runner`: `pytest` output is parsed for its `N passed` summary
  line; `exit-code` runners treat a 0 exit as 1 passed, non-zero as 0 passed
  (there's no structured count to recover otherwise). No `runner` declared →
  `UNVERIFIABLE`, not a silent pass.
- **Consensus** (`grade`, across builds): runs the block's `invoke` per
  fixture per build, canonicalizes stdout (`forgejury/canonical.py`: CRLF→LF,
  per-line trailing whitespace stripped, trailing blank lines dropped), then
  classifies `3-0` / `2-1` (names the diverging build) / `3-way`. This is
  **behavioral/stdout-only** — no AST public-surface diffing, since three
  personas legitimately differ internally and that's noise, not signal.
  When a fixture declares `expected`, each build's canonicalized stdout is
  also compared to it directly (a correctness check, independent of
  agreement).
- No arbitrary command execution: the only commands ever run are the
  spec-declared `test_cmd` and `invoke` — never anything a build-report
  names.
- Layer 3 (fence) was dropped per the spec's own guidance — `forge.py`
  serializes stages this cycle, so it has near-zero dogfood value this
  round.

## Tests

```
python -m pytest -q
```

41 tests across `tests/test_canonical.py`, `test_determinism.py`,
`test_lint.py`, `test_symbols.py`, `test_spec_parser.py`, `test_grade.py`
(unit + integration against the bundled examples), and `test_main.py`
(subprocess-level CLI tests, including that `--json` output round-trips
through `json.loads` and matches the schema above).

Real output from this build, run from this directory:

```
$ python -m pytest -q
........................................                                 [100%]
41 passed, 1 warning in 3.76s
```
