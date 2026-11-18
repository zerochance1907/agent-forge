---
cycle: 2026-11-18
from: exec-1
to: reviewer
stage: build
type: build-report
blocking: false
---

# exec-1 build report: BuildOracle, Core + Head A only, Forgejury green

Minimalist-hacker build. One package (`buildoracle/`), no dependencies beyond
stdlib (+ `pytest` for tests), no vendor directory (spec requires none), no
Head B/C. Everything lives in `builds/2026-11-18/exec-1/`.

## Per-criterion status

| # | criterion | status | evidence |
|---|---|---|---|
| 1 | `python -m buildoracle` runnable, `demo` runs all 4 cases | **met** | `buildoracle/__main__.py`; demo output below |
| 2 | `gate --case <name>` prints exactly one compact-JSON line to stdout, exits 0 | **met** | stdout captured below, byte-matches spec's expected fixtures |
| 3 | `classify` uses both AST static scan **and** empirical double-run; transitive (non-import) nondeterminism still caught | **met** | `tests/test_core.py::test_classify_refuses_transitive_nondeterminism_via_double_run` builds a `timeit.default_timer()` module (not in the static scan's known-import list), asserts the static scan finds nothing, and asserts `classify` still REFUSEs via double-run divergence |
| 4 | `canonicalize` tested for dict key-order, float precision, whitespace; `keyorder` case PASSes *because* of canonicalization | **met** | `test_canonicalize_dict_key_order_insensitivity`, `test_canonicalize_float_precision`, `test_canonicalize_string_whitespace_normalization`, `test_canonicalize_nested_structures`; `test_verify_pass_on_keyorder_case_via_canonicalization` explicitly asserts the raw key orders differ before asserting canonical equality |
| 5 | `verify` replays trace, prints PASS/FAIL naming input, exits 0/10/20 | **met** | CLI transcript below shows all three exit codes for real |
| 6 | Head A report carries the honest coverage line | **met** | printed to stderr on every `gate`/`verify`/`demo` run |
| 7 | No network, no secrets, fully offline | **met** | stdlib only; README states it |
| 8 | README documents install/run, demo, four verdicts, record→classify→verify flow, honest refusal, coverage limitation, Heads B/C unbuilt | **met** | `README.md` |
| 9 | `tests/test_core.py` covers canonicalize, refuse (both signals), pass+fail through verify; `pytest -q` exits 0 | **met** | 11 tests, all passing |
| 10 | `claims.json` per-criterion | **met** | included, `tests_passed: 11` |

**Heads B and C: not built.** Per spec and memo 015, they're explicitly
optional/ungraded reach. This build is Core + Head A only, with both
nondeterminism-detection signals real and independently tested (not just the
import-based one).

## Design note on `verify`'s REFUSE path

Spec says `verify` exits 20 on REFUSE but its CLI signature takes no
`--exercise`. I resolved this by having `verify` re-run the static scan on the
*target* module and double-run the *recorded trace's own inputs* against it
twice before trusting the comparison — so `verify` can independently catch "the
refactor introduced nondeterminism" without needing a fresh exercise script.
Demonstrated live in the transcript below (REFUSE via exit 20 on the
`nondeterministic` module through `verify` directly, not just through `gate`).

## Demo command and real output

```
$ python -m buildoracle demo
```
stdout:
```
case               verdict
------------------------------
identity           PASS
offbyone           FAIL
nondeterministic   REFUSE
keyorder           PASS
```
stderr (trimmed, same run):
```
PASS
coverage: recorded trace + existing tests only -- unexercised paths not gated
FAIL: diverged on input func=clamp args=[15, 0, 10] kwargs={}
coverage: recorded trace + existing tests only -- unexercised paths not gated
REFUSE: imports 'time' [line 1]
coverage: recorded trace + existing tests only -- unexercised paths not gated
PASS
coverage: recorded trace + existing tests only -- unexercised paths not gated
```

## `gate --case <name>` stdout, isolated (the Forgejury consensus surface)

```
identity         -> {"verdict": "PASS"}
offbyone         -> {"verdict": "FAIL"}
nondeterministic -> {"verdict": "REFUSE"}
keyorder         -> {"verdict": "PASS"}
```
`gate --case bogus` exits 1 (unknown case), all four real cases exit 0.

## `verify` exit codes, demonstrated directly (not just through `gate`)

```
$ python -m buildoracle verify --trace offbyone_trace.json --module offbyone/refactored.py
FAIL: diverged on input func=clamp args=[15, 0, 10] kwargs={}
exit=10

$ python -m buildoracle verify --trace identity_trace.json --module identity/refactored.py
PASS
exit=0

$ python -m buildoracle verify --trace nondet_trace.json --module nondeterministic/original.py
REFUSE: imports 'time' [line 1]
exit=20
```

## Test suite

```
$ python -m pytest -q
...........                                                              [100%]
11 passed in 0.09s
```

## Forgejury (ran myself before finishing, per protocol)

```
$ python -m forgejury grade builds/2026-11-18/SPEC.md builds/2026-11-18/exec-1
=== Forgejury verdict ===
Summary: 1/1 builds PASS
[exec-1] verdict=PASS
    spec axis: all 9 checks PASS
    claims axis: files/symbols/test_cmd_exit/tests_passed all PASS
=== Consensus (behavioral, stdout-only) ===
  identity: expected-match[exec-1]: PASS
  offbyone: expected-match[exec-1]: PASS
  nondeterministic: expected-match[exec-1]: PASS
  keyorder: expected-match[exec-1]: PASS
```

## Known gaps

- Mutable-module-global detection in the static scan is a heuristic (flags any
  function reading a name assigned a list/dict/set literal at module scope);
  no bundled case exercises it directly since the pinned four cases don't need
  it, but it's exercised indirectly in that none of the four cases trip a false
  positive on it.
- `canonicalize`'s float rounding (9 decimals) and the `timeit`-double-run test
  both assume the test machine's clock resolution is fine enough that two
  back-to-back `timeit.default_timer()` calls differ beyond the 9th decimal.
  True on every machine I'd expect this to run on; noting it as the one
  environmental assumption in the suite.

## Licenses

No code vendored. `erkamyaman/rust-anything` (MIT) and
`microsoft/TokenEconomizer` (MIT) were concept anchors only per the spec;
nothing cloned or copied from either.
