---
cycle: 2026-11-18
from: exec-2
to: reviewer
stage: build
type: build-report
blocking: false
---

# BuildOracle (exec-2, production-engineer persona) — Core + Head A, fully passing, Forgejury-clean

Built at `builds/2026-11-18/exec-2/`. Python 3.13, stdlib only, `pytest` the
only dependency, fully offline. **No vendor/ directory — nothing to
vendor**, matching the spec (concept anchors only, no third-party code
copied).

## What I built

- `buildoracle/core.py` — `canonicalize`, `static_scan`, `classify`,
  `record`/`record_to_file`, `verify`/`verify_trace_file`, `run_case`,
  `run_exercise`. All comparisons route through `canonicalize`.
- `buildoracle/__main__.py` — CLI: `record`, `classify`, `verify`, `gate`,
  `demo`. `gate` prints exactly one compact-JSON line to stdout and sends
  everything else to stderr; exits 0 on any successful verdict, non-zero
  only on crash or unknown `--case`.
- `buildoracle/cases/{identity,offbyone,nondeterministic,keyorder}/` — the
  four pinned fixtures (`original.py`, `refactored.py`, `exercise.py`).
- `tests/test_core.py` — 21 tests.
- `README.md`, `claims.json`.

## Acceptance criteria — all met

1. **Runnable, demo works.** `python -m buildoracle demo` runs all four
   cases, prints the table + coverage line.
2. **`gate --case <name>` stdout contract.** Verified by hand and by a
   subprocess test: exactly one line, compact JSON, exit 0, for all four
   cases. Matches the pinned fixtures byte-for-byte (confirmed via
   `python -m forgejury grade` below).
3. **classify uses both signals.** Static AST scan (import blocklist +
   `global` reassignment) **and** an empirical double-run (run the exercise
   twice against one loaded module instance, compare canonicalized traces).
   Unit-tested with a fixture that imports only `itertools` (not
   blocklisted) and reads a module-level counter without a `global`
   statement — static scan provably misses it (`assert reason is None`
   in the test), the double-run catches it.
4. **canonicalize is mandatory core, tested.** Dedicated tests for dict
   key-order, float-precision rounding (6 decimals), string whitespace, and
   a nested-structure combination. `keyorder` case is built so a *raw*
   comparison would actually FAIL (double space in a string field, not just
   key order, since Python dict `==` is already order-blind) — a dedicated
   test (`test_verify_pass_because_canonicalization_ran`) proves the raw
   values differ before asserting the canonicalized verdict is PASS.
5. **verify exit codes.** 0 (PASS) / 10 (FAIL) / 20 (REFUSE), confirmed via
   real CLI subprocess calls, not just unit tests.
6. **Honest coverage line.** Exact spec string emitted by `demo` and by
   `gate`'s stderr detail on every case.
7. **Offline, no secrets.** No network imports anywhere; confirmed by
   reading the source — the only non-stdlib import across the whole build
   is `pytest` in the test suite.
8. **README** covers install/run, demo, the four verdicts, the full
   record→classify→verify flow, honest-refusal behavior, the coverage
   limitation, and explicitly that Heads B/C are unbuilt.
9. **tests/test_core.py** covers canonicalize, both refuse signals, and a
   pass + fail through `verify`, plus the four bundled cases and the CLI.
10. **claims.json** — see below.

## One real bug I caught and fixed during the build

The spec's required coverage line contains an em dash (`—`). On first run,
`python -m buildoracle demo > file` on this Windows box encoded that
character using the console's locale codepage (cp1252) rather than UTF-8,
which would mangle the line for any downstream UTF-8 reader (and my own
`subprocess.run(text=True)` tests failed on it — Windows `locale.
getpreferredencoding()` defaults to cp1252, not UTF-8). Fixed by having
`main()` reconfigure `sys.stdout`/`sys.stderr` to UTF-8 explicitly
(`stream.reconfigure(encoding="utf-8")`), and by passing `encoding="utf-8"`
explicitly in my own test harness's `subprocess.run` calls. Flagging this
because it's a real cross-platform gotcha the spec's own text triggers —
worth checking the other two builds didn't just get lucky on their OS's
default codepage.

## Demo command and real output

```
$ python -m buildoracle demo
case               verdict  detail
----------------------------------------------------------------------
identity           PASS
offbyone           FAIL     diverged on input 1
nondeterministic   REFUSE   imports 'time' [line 3]
keyorder           PASS
----------------------------------------------------------------------
coverage: recorded trace + existing tests only — unexercised paths not gated
```

```
$ python -m buildoracle gate --case offbyone 2>/dev/null
{"verdict": "FAIL"}
```

## Test suite — real output

```
$ python -m pytest -q
.....................                                                    [100%]
21 passed in 1.18s
```

## Forgejury — ran it myself from repo root, real output

```
$ python -m forgejury grade builds/2026-11-18/SPEC.md builds/2026-11-18/exec-2
=== Forgejury verdict ===
Summary: 1/1 builds PASS

[exec-2] verdict=PASS
    spec axis: file:README.md PASS, file:__main__.py PASS, file:core.py PASS,
               file:test_core.py PASS, file:claims.json PASS,
               symbol:canonicalize PASS, symbol:classify PASS, symbol:verify PASS,
               test_cmd PASS
    claims axis: files PASS, symbols PASS, test_cmd_exit PASS, tests_passed PASS

=== Consensus (behavioral, stdout-only) ===
  identity: 1-0 expected-match[exec-2]: PASS
  offbyone: 1-0 expected-match[exec-2]: PASS
  nondeterministic: 1-0 expected-match[exec-2]: PASS
  keyorder: 1-0 expected-match[exec-2]: PASS
```

## Known gaps

- Heads B and C: not built, per spec explicitly optional/ungraded. Did not
  spend time on them.
- No fuzzing/property generation: not built, per spec explicitly out of
  scope.
- Static-scan global-mutation detection only catches explicit `global`
  statements (reassignment), not bare reads of module-level state through
  closures — that gap is exactly why the empirical double-run exists and is
  mandatory, and it's unit-tested as the catch-all.

## Licenses

No third-party code vendored or copied. `erkamyaman/rust-anything` (MIT)
and `microsoft/TokenEconomizer` (MIT) were concept anchors only during
design, per SPEC.md — zero lines from either repo appear in this build.
