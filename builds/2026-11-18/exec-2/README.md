# BuildOracle

A behavioral-diff gate for agent refactors: **record → classify-then-refuse →
canonicalize → verify**.

BuildOracle records the input→output→raised behavior of a target Python
module, then — after a refactor — replays that recording against the new
code and **vetoes any divergence**. Before it will do that, it decides
whether the module is *safely gateable at all*. If the module touches the
clock, randomness, the network, or mutable global state, BuildOracle
**honestly refuses to gate it** and says why, instead of emitting a flaky
pass/fail. An agent trusts an oracle that refuses; it learns to ignore one
that cries wolf.

This build implements the mandatory **Core + Head A (Refactor Gate)** from
`builds/2026-11-18/SPEC.md`. **Heads B and C (Disagreement Triage,
Spec-Gap Report) were not built** — they are explicitly optional reach per
the spec and are out of scope here.

## Requirements

- Python 3.13, standard library only.
- `pytest` for the test suite (the only external dependency).
- No network access required or used. No secrets. Runs fully offline.

## Install / run

No install step — it's a plain package. From this directory:

```bash
python -m buildoracle --help
```

## Demo

```bash
python -m buildoracle demo
```

Runs all four bundled cases and prints a verdict table:

```
case               verdict  detail
----------------------------------------------------------------------
identity           PASS
offbyone           FAIL     diverged on input 1
nondeterministic   REFUSE   imports 'time' [line 3]
keyorder           PASS
----------------------------------------------------------------------
coverage: recorded trace + existing tests only — unexercised paths not gated
```

## CLI surface

| command | what it does |
|---|---|
| `record --module <path> --exercise <path> --out <trace.json>` | drives `<module>` with every input in `<exercise>` and writes the (input, output, exception) trace to `<trace.json>`. |
| `classify --module <path> --exercise <path>` | prints `GATEABLE` or `REFUSE: <reason> [line N]`. |
| `verify --trace <trace.json> --module <path>` | the real agent-facing gate. Replays the trace against `<module>`, prints `PASS` / `FAIL: diverged on input <...>` / `REFUSE: <reason>`, and **exits** `0` (PASS) / `10` (FAIL) / `20` (REFUSE). |
| `gate --case <name>` | runs one bundled, pinned case end-to-end (record the case's original → classify → verify its refactor) and prints **exactly one line** to stdout: `{"verdict": "PASS"|"FAIL"|"REFUSE"}`. All human-readable detail goes to stderr. Exits `0` whenever it successfully emits a verdict (non-zero only on a crash or an unknown case name — the verdict is *data*, not exit status). |
| `demo` | runs all four bundled cases and prints a human-readable table. |

**Target-module contract**: any module passed via `--module` must expose a
top-level `run(x)` function. Any exercise script passed via `--exercise`
must expose a top-level `INPUTS` list — each element is passed to `run` in
order.

## The four bundled cases and what each one proves

| case | what it contains | verdict | why |
|---|---|---|---|
| `identity` | refactor is a behavior-preserving rewrite (loop → closed-form sum) | `PASS` | same outputs on every recorded input |
| `offbyone` | refactor adds a stray `+1` | `FAIL` | diverges on the first input tried |
| `nondeterministic` | module calls `time.time()` | `REFUSE` | caught by the static AST scan — not safely gateable |
| `keyorder` | refactor returns the same content with different key insertion order *and* an extra internal space in a string field | `PASS` | **only because `canonicalize()` ran** — a raw `==` would FAIL on the whitespace (see `tests/test_core.py::test_verify_pass_because_canonicalization_ran`, which proves the raw values actually differ before asserting the canonicalized verdict is PASS) |

## The record → classify → verify flow

1. **`record`** drives the *original* module with the exercise script and
   captures the ordered `(input, output, exception)` triples to a trace file.
2. **`classify`-then-refuse** decides whether the module is safely gateable,
   using **two independent signals**:
   - **Static scan** (`core.static_scan`) — AST-inspects the module for
     imports of `time`, `random`, `datetime`, `socket`, `os`, `uuid`,
     `secrets`, or a `global` statement that reassigns module-level state.
     Names the reason and the source line.
   - **Empirical double-run** — runs the exercise *twice* against one loaded
     module instance and compares the two traces (after canonicalization).
     This catches nondeterminism that enters **transitively** through a
     called library or through module-level mutable state that is only
     *read* (not reassigned with `global`) — see
     `tests/test_core.py::test_classify_refuses_on_empirical_divergence`,
     which uses an `itertools.count()`-backed counter that imports nothing
     on the static blocklist and is only caught by the double-run.
   - If **either** signal fires, `classify` returns `REFUSE` with a reason
     (and a line number when the static scan found it). It never emits a
     pass/fail for a module it can't trust.
3. **`canonicalize`** (mandatory core — every comparison in the tool runs
   through it) normalizes a value before comparison: floats are rounded to 6
   decimal places, dict keys are sorted, strings have internal whitespace
   collapsed, sets are sorted. See `tests/test_core.py` for dedicated unit
   tests on dict key-order, float precision, and whitespace.
4. **`verify`** (Head A, the demoable product) replays a recorded trace
   against the refactored module, canonicalizing both sides before
   comparing, and vetoes the first divergence by naming the exact input that
   diverged. It also runs its own static scan on the module being verified
   first — if that module isn't safely gateable, it refuses rather than
   emit a pass/fail nobody should trust.

## Honest refusal

BuildOracle never lies about confidence. If a module can't be safely gated
— because it's provably or empirically nondeterministic — `classify` and
`verify` say `REFUSE` and name the reason, instead of emitting a pass or
fail that might just be clock jitter.

## Coverage honesty (the limitation, stated plainly)

Head A's gate report always carries this line:

```
coverage: recorded trace + existing tests only — unexercised paths not gated
```

BuildOracle only knows about the inputs the exercise script actually drove
through the original module. It makes **no claim** about behavior on inputs
it never ran. Widening that input set (e.g. by pooling exercises across
multiple independent builds of the same refactor) is a property of the
optional, unbuilt Head B (Disagreement Triage) — Head A standalone has no
such source and this build does not pretend otherwise.

## Heads B and C: not built

Per the spec, Head B (Disagreement Triage — run N implementations over a
shared input set, rank disagreements by minority size) and Head C (Spec-Gap
Report — relabel Head B's clusters as probable spec gaps) are explicitly
optional, never-graded reach. This build ships **Core + Head A only**,
which the spec defines as a complete success.

## No network, no secrets

BuildOracle imports only the Python standard library at runtime (plus
`pytest` for tests). It makes no network calls, opens no sockets, and reads
no credentials or secrets. It is safe to run fully offline — the only code
it executes beyond its own is whatever target module/exercise script you
point it at.

## Tests

```bash
python -m pytest -q
```

`tests/test_core.py` covers:

- `canonicalize`: dict key-order insensitivity, float-precision rounding,
  string-whitespace normalization, and a nested-structure combination.
- The refuse path: a static-signal refusal (`import time`, with line number)
  and an empirical-signal refusal (module-level counter via `itertools`,
  which slips past the static blocklist and is only caught by the
  double-run).
- `verify`: a PASS on an identical module, a FAIL that names the diverging
  input, a REFUSE on a nondeterministic module, and a PASS that is proven to
  depend on canonicalization (the raw, uncanonicalized values are shown to
  differ first).
- All four bundled cases via `core.run_case` directly.
- The CLI end-to-end via `subprocess`: `gate --case <name>` emits exactly the
  pinned one-line JSON verdict on stdout for every bundled case; `demo`
  prints all four cases and the coverage line; `verify`'s exit codes (`0`
  PASS / `10` FAIL) are exercised through the real CLI.

Real run on this build:

```
$ python -m pytest -q
.....................                                                    [100%]
21 passed in 1.18s
```

## What was NOT built (explicit, per spec)

- No Head B (Disagreement Triage), no Head C (Spec-Gap Report).
- No blind fuzzing / property-based input generation.
- No multi-language support — Python target modules only.
- No MCP server, no web UI, no model in the loop. Standalone CLI only.

## License note

No third-party code is vendored. Two upstream repos were concept anchors
only during the design/decide stage (per `SPEC.md`): `erkamyaman/rust-
anything` (MIT) and `microsoft/TokenEconomizer` (MIT) — both just as a
stance ("record behavior, check rewritten units against it" /
"learn from recorded traces, black-box"), with zero code copied into this
build.
