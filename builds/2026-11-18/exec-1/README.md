# BuildOracle (exec-1 build)

A behavioral-diff refactor gate: **record → classify-then-refuse →
canonicalize → verify**. It records what a module actually does, then vetoes
any divergence after a refactor -- unless the module cannot be gated
deterministically, in which case it says so honestly instead of guessing.

Python 3.13, standard library only. `pytest` is the only external dependency
(dev/test only). **No network calls, no subprocess, no secrets, fully
offline.**

## Install / run

No install step. From this directory:

```
python -m buildoracle demo
```

## Demo

```
python -m buildoracle demo
```

Runs the four bundled cases end-to-end and prints a table:

```
case               verdict
------------------------------
identity           PASS
offbyone           FAIL
nondeterministic   REFUSE
keyorder           PASS
```

Human-readable detail (why each verdict fired, the diverging input on FAIL,
the refusal reason on REFUSE) goes to **stderr**; the table above is stdout.

## The four bundled cases and what they prove

| case               | proves                                                              |
|---------------------|----------------------------------------------------------------------|
| `identity`          | a genuinely behavior-preserving rewrite gates clean -> `PASS`        |
| `offbyone`           | a refactor that changes behavior on a recorded input is caught -> `FAIL`, naming the exact input |
| `nondeterministic`   | a module that calls `time.time()` is honestly refused, not flakily passed/failed -> `REFUSE` |
| `keyorder`           | a refactor that returns the same dict content in a different key order still `PASS`es *because canonicalization ran*, not by accident |

`tests/test_core.py::test_verify_pass_on_keyorder_case_via_canonicalization`
explicitly proves the raw key orders differ before asserting the canonicalized
comparison still passes.

## CLI surface

- `python -m buildoracle record --module <path> --exercise <path> --out <trace.json>`
  Drives `<module>` through every `(func, args, kwargs)` in `<exercise>`'s
  `INPUTS` list and writes the `(input, return_value, raised_exception)` trace
  to `<trace.json>`.
- `python -m buildoracle classify --module <path> --exercise <path>`
  Prints `GATEABLE` or `REFUSE: <reason> [line N]`. Uses **two** signals:
  1. **Static AST scan** of `<module>` for imports of
     `time`/`random`/`datetime`/`socket`/`os`/`uuid`/`secrets`, and for
     function bodies that *read* a mutable module-level global (a
     list/dict/set literal assigned at module scope).
  2. **Empirical double-run**: runs the exercise against `<module>` twice
     (fresh import each time) and canonical-compares the two traces. This
     catches nondeterminism that enters *transitively* through a called
     library, which the static scan can't see.
- `python -m buildoracle verify --trace <trace.json> --module <path>`
  The real agent-facing gate. Re-checks `<module>`'s own gateability (static
  scan + a double-run of the recorded trace against it) before trusting the
  comparison, then replays the trace and canonical-compares. Prints `PASS` /
  `FAIL: diverged on input ...` and **exits 0 / 10 / 20** for PASS / FAIL /
  REFUSE respectively. Exit code carries meaning here.
- `python -m buildoracle gate --case <name>` runs one bundled case end-to-end
  (`record` the original -> `classify` it -> `verify` the refactor against the
  recorded trace) and prints **exactly one line to stdout**:
  `{"verdict": "PASS"}` / `"FAIL"` / `"REFUSE"` (compact JSON). All
  human-readable detail goes to stderr. **Exits 0 whenever it successfully
  emits a verdict** -- a non-zero exit means a crash or an unknown case name,
  not REFUSE. This is the Forgejury consensus surface.
- `python -m buildoracle demo` runs all four bundled cases and prints the
  table above.

## Record/classify/verify flow

1. `record` captures the original module's behavior against an exercise
   script into a trace.
2. `classify` decides, *before* trusting any comparison, whether the module
   is safely gateable at all (static scan + double-run).
3. If `GATEABLE`, `verify` replays the trace against the refactored module,
   canonicalizing both sides before comparing, and names the first diverging
   input it finds.
4. If not gateable, BuildOracle **refuses** -- it never emits a flaky
   pass/fail on a module it can't reliably gate.

## Honest refusal and coverage honesty

- BuildOracle refuses rather than guesses whenever either the static scan or
  the empirical double-run detects nondeterminism. The refusal names the
  reason and, when the static scan located it, the source line.
- Every gate/verify/demo report prints:
  `coverage: recorded trace + existing tests only -- unexercised paths not gated`
  BuildOracle never claims assurance beyond what it actually ran. Widening
  coverage with other agents' recorded inputs (Head B, "Disagreement Triage")
  is explicitly out of scope for this build -- see below.

## What's not built (by design)

Per the spec, **Head B (Disagreement Triage) and Head C (Spec-Gap Report) are
not built.** They are optional, ungraded reach for this cycle. This build
ships only the mandatory Core + Head A (the Refactor Gate), with the
honest-refusal path fully working, and considers that a complete success --
not a partial one.

No blind fuzzing/property generation is included either; the spec treats that
as optional and out of scope for the mandatory build.

## Canonicalization

`buildoracle/core.py::canonicalize` is the single function every comparison in
the tool runs through:

- dict keys are sorted (so insertion order never matters)
- floats are rounded to 9 decimal places
- strings have internal whitespace collapsed and are stripped
- sets are reduced to a sorted list of their canonicalized elements

`tests/test_core.py` has dedicated unit tests for each of these, plus a test
proving `keyorder` passes *because* of canonicalization rather than by luck.

## Tests

```
python -m pytest -q
```

11 tests, covering `canonicalize` (dict order / float precision / whitespace /
nesting), the static-scan refuse path, a dedicated test for the **empirical
double-run** refuse path (a module that calls `timeit.default_timer()` --
`timeit` isn't in the static scan's known-nondeterministic-import list, so
only the double-run catches it; the test asserts the static scan finds
nothing *and* `classify` still REFUSEs), and a PASS/FAIL/PASS-via-
canonicalization trio through `verify`.

## License note

No third-party code is vendored or copied. Two upstream repos
([erkamyaman/rust-anything](https://github.com/erkamyaman/rust-anything), MIT;
[microsoft/TokenEconomizer](https://github.com/microsoft/TokenEconomizer), MIT)
were cited in the spec as concept anchors only -- their licenses are recorded
here for the trail but nothing was cloned or copied from either.
