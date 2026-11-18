# BuildOracle

A behavioral-diff gate for agent refactors: **record → classify-then-refuse →
canonicalize → verify**. Pure Python 3.13 standard library (plus `pytest` for
the test suite). No network calls, no secrets, fully offline.

The problem: an agent (or human) refactors a module and the "optimized"
version silently returns something subtly different. BuildOracle records the
old behavior, then vetoes any divergence after the rewrite — but it only ever
gates what it can *honestly* vouch for. If the module is nondeterministic
(touches time, randomness, the network, the filesystem, or mutable global
state — directly or transitively), BuildOracle **refuses to gate it** and
says exactly why, instead of emitting a flaky pass/fail.

## Install / run

```
cd buildoracle-dir  # this directory
python -m buildoracle demo
```

No install step — stdlib only. `pytest` is only needed to run the test suite:

```
python -m pip install pytest
python -m pytest -q
```

## The demo command

```
python -m buildoracle demo
```

Runs all four bundled cases (`identity`, `offbyone`, `nondeterministic`,
`keyorder`) end to end and prints a human-readable report, including — for
the `keyorder` case — a **live proof** that the PASS happened *because*
`canonicalize()` ran: it prints the raw `repr()` of both the original's and
the refactor's recorded output (showing they are textually different: keys
inserted in a different order, and a `0.1` vs `0.10000000000000002` float
that only differ due to reordered arithmetic), then shows their canonical
forms are equal. Nothing in that proof is scripted — it's computed from an
actual `record()` call made during the demo run.

Each case also carries the honest coverage line:

```
coverage: recorded trace + existing tests only — unexercised paths not gated
```

BuildOracle never claims more assurance than the trace it actually replayed.

## The four verdicts

| verdict   | meaning                                                                 |
|-----------|--------------------------------------------------------------------------|
| `PASS`    | the refactor reproduces every recorded input→output/exception, after canonicalization |
| `FAIL`    | the refactor diverged on a specific recorded input — that input is named |
| `REFUSE`  | the module isn't safely gateable (nondeterministic by import or by observed behavior) — BuildOracle says why instead of guessing |

## record → classify → verify

1. **`record --module <path> --exercise <path> --out <trace.json>`** drives
   the module with the exercise script's `INPUTS` against its `FUNC`, and
   writes the ordered `(input, output, raised_exception)` events to a trace
   file.
2. **`classify --module <path> --exercise <path>`** decides gateability using
   **two independent signals**:
   - a **static AST scan** for imports of `time`, `random`, `datetime`,
     `socket`, `os`, `uuid`, `secrets`, and for any function that declares
     `global` (reads/writes module-level mutable state);
   - an **empirical double-run**: the exercise is run against the module
     *twice* and the two canonicalized traces are compared. This catches
     nondeterminism that enters through a dynamically-imported module
     (`__import__("random")`) or other means a static import scan can't see —
     see `tests/fixtures/hidden_nondeterminism.py`, which has no `import`
     statement at all and is still correctly REFUSEd.

   If either signal fires, `classify` prints `REFUSE: <reason>` (plus
   `[line N]` when the static scan located it) and never emits a pass/fail.
3. **`verify --trace <trace.json> --module <path>`** is the real agent-facing
   gate: it replays the recorded inputs against `<module>`, canonicalizing
   both the recorded and the live output/exception before comparing, and
   prints `PASS` or `FAIL: diverged on input <...>`. Exit codes carry meaning
   here: `0` = PASS, `10` = FAIL, `20` = REFUSE (reserved — `verify` itself
   only ever emits PASS/FAIL since it assumes `classify` already ran).

## Honest refusal

`classify`/`gate` never fake a verdict on a module they can't be sure about.
The `nondeterministic` bundled case imports `time` and is REFUSEd by the
static scan; `tests/fixtures/hidden_nondeterminism.py` has no suspicious
import at all (it reaches `random` via a dynamic `__import__` call) and is
still caught — but only by the empirical double-run, proving the two signals
are genuinely independent and both load-bearing.

## Coverage honesty (the limitation, stated plainly)

Head A's assurance is **recorded trace + existing tests only**. It gates
exactly the inputs the exercise script drove through the original module —
nothing more. It makes no claim about unexercised code paths. Widening
coverage via a union of multiple independent exercise sets is a property of
the (unbuilt, optional) Head B/Head C reporting modes, not of Head A alone.

## `gate` — the Forgejury consensus surface

```
python -m buildoracle gate --case <name>
```

runs one bundled case end-to-end (record original → classify → verify
refactor) and prints **exactly one line to stdout**:
`{"verdict": "PASS"}` / `{"verdict": "FAIL"}` / `{"verdict": "REFUSE"}`
(compact `json.dumps`). All human-readable detail (the reason, the diverging
input, the coverage line) goes to **stderr**. `gate` exits `0` whenever it
successfully emits a verdict; a non-zero exit is reserved for a crash or an
unknown `--case` name.

## Bundled cases

| case               | verdict   | why                                                                 |
|--------------------|-----------|----------------------------------------------------------------------|
| `identity`         | `PASS`    | refactor rewrites `dedupe_sorted` as a one-liner; same behavior      |
| `offbyone`         | `FAIL`    | refactor adds `+1` before clamping; diverges on input `[50, 50]`     |
| `nondeterministic` | `REFUSE`  | module imports `time` and calls `time.time()` — caught by the static scan |
| `keyorder`         | `PASS`    | refactor returns the same dict with reordered keys *and* a float that only differs by floating-point rounding (`0.1` vs `(0.1*3)/3`) — PASS only because `canonicalize()` ran |

## Upstream / licenses

No third-party code is vendored. Two repos from the research phase are
concept anchors only (license recorded, no code used):
[erkamyaman/rust-anything](https://github.com/erkamyaman/rust-anything) (MIT)
and [microsoft/TokenEconomizer](https://github.com/microsoft/TokenEconomizer)
(MIT).

## Scope

Core + Head A only, as specced. **Heads B (Disagreement Triage) and C
(Spec-Gap Report) were not built** — they are explicitly optional reach and
not required for a complete build. This build ships only the mandatory
deliverable: Core + Head A, on deterministic Python, with the honest-refusal
path exercised by both a static-only case and an empirical-only case.

## Offline / safety

No network calls, no subprocess-to-the-internet, no secrets, no filesystem
writes outside trace files you explicitly ask for with `--out`. Target
modules are loaded by file path via `importlib` and executed in-process.
