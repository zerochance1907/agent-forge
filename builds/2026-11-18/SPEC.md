# Build Spec — cycle 2026-11-18

## Idea: **BuildOracle** — a behavioral-diff gate for agent refactors (record → classify-then-refuse → canonicalize → verify)

A small, self-contained Python CLI that records the input→output→raised
behavior of a target module during an exercise run, then, after an agent
refactors that module, **replays the recording and vetoes any divergence** —
but only after deciding whether the module is *safely gateable at all*. If the
module is nondeterministic (touches time, randomness, the network, the
filesystem, global state), BuildOracle **honestly refuses to gate it** and says
why, instead of emitting a flaky pass/fail.

This is the trustworthy half of the agent-refactor safety loop. Golden-master /
characterization tools exist as *human* frameworks (ApprovalTests, etc.), but
they silently cry wolf on nondeterminism and silently wave through bugs on
inputs the recording never hit. The novel wedge — corroborated by both
debaters' prior-art searches (`agent refactor behavior oracle gate skill`,
`characterization test record replay refactor agent`, `differential testing
agent generated code same spec` → **0 public-repo results**) — is an
**agent-callable oracle that knows its own limits**: it records, it canonicalizes
before comparing, and it *declines* what it cannot gate deterministically rather
than lying. An agent trusts an oracle that refuses; it learns to ignore one that
cries wolf.

### Problem and target user

Any coding agent (or human) doing a refactor. The #1 failure mode is a *silent
behavior change* — the "optimized" function now returns something subtly
different. BuildOracle is the cheap, language-agnostic-in-spirit (Python here)
safety net the refactoring agent invokes itself: record the old behavior, let
the agent rewrite, then gate the change on "behavior unchanged — and I'll tell
you honestly if I can't be sure."

### Upstream repositories

**No third-party code is vendored.** Two researched repos are *concept anchors
only* (both permissive, recorded for the license trail):

- [erkamyaman/rust-anything](https://github.com/erkamyaman/rust-anything) —
  **MIT**. We take the *concept* the research report singled out: "record
  behavior, check each rewritten unit against it." We strip it off the Rust
  migration and the FFI. **Concept only — no code vendored.**
- [microsoft/TokenEconomizer](https://github.com/microsoft/TokenEconomizer) —
  **MIT**. We borrow the *stance*: "learn from recorded traces, black-box, don't
  fork the agent." Here the trace is behavioral I/O, not cost. **Concept only —
  no code vendored.**

Python 3.13 standard library only. The only external dependency permitted is
`pytest` for the test suite. **Do not clone anything into `vendor/`** — there is
nothing to vendor.

### Scope — what to build (the mandatory core + Head A)

A single Python package `buildoracle`, runnable as `python -m buildoracle`,
living at the root of the build directory so it imports with that directory as
cwd. It must implement:

#### Core (mandatory, all three builds must agree on semantics)

1. **`record`** — capture the ordered sequence of `(input, return_value,
   raised_exception)` events a target module produces when driven by an exercise
   script, to a trace file.
2. **`classify`-then-refuse** — decide whether the module is *safely gateable*,
   using **both** signals (novelty-b's load-bearing point — spec it, don't cost
   it as free):
   - **Static scan:** AST-inspect the module for imports/uses of known
     nondeterminism sources (`time`, `random`, `datetime`, `socket`, `os`,
     `uuid`, `secrets`, and reads of mutable module-level globals).
   - **Empirical double-run:** run the exercise against the module **twice** and
     compare the two traces (after canonicalization). If they differ, the module
     is nondeterministic *by behavior* — this catches nondeterminism that enters
     transitively through a called library, which the static scan misses.
   - If either signal fires, BuildOracle **refuses**: it reports
     `verdict = REFUSE` and names the reason (e.g. `"calls time.time()"`) and,
     where the static scan found it, the source line number. It does **not** emit
     a pass/fail.
3. **`canonicalize`** — normalize a value before any comparison: sort dict keys,
   round floats to a fixed precision, normalize string whitespace, make set/dict
   ordering irrelevant. **This is mandatory core** — every comparison in the tool
   runs through it, and the test suite must prove it (see acceptance criteria).
4. **Head A — Refactor Gate** (the demoable, mandatory product): record the
   original module's behavior, then replay the recorded inputs against the
   refactored module, canonicalize both sides, and **veto any divergence**,
   naming the exact input that diverged. The report must carry an **honest
   coverage line**: `"coverage: recorded trace + existing tests only — unexercised
   paths not gated"`. BuildOracle never claims more assurance than it delivered.

#### CLI surface

- `python -m buildoracle record --module <path> --exercise <path> --out <trace.json>`
  — writes the behavior trace.
- `python -m buildoracle classify --module <path> --exercise <path>` — prints the
  gateability verdict (`GATEABLE` or `REFUSE: <reason> [line N]`).
- `python -m buildoracle verify --trace <trace.json> --module <path>` — the
  real agent-facing gate: replays the trace against `<module>`, prints
  `PASS` or `FAIL: diverged on input <...>`, and **uses exit codes** — exit `0`
  on PASS, exit `10` on FAIL, exit `20` on REFUSE. (This subcommand is where exit
  status carries meaning.)
- `python -m buildoracle gate --case <name>` — runs one **bundled, pinned case**
  end-to-end (record the case's original → classify → verify its refactor) and
  prints **exactly one line** to stdout:
  `print(json.dumps({"verdict": v}))`, i.e. literally `{"verdict": "PASS"}` /
  `{"verdict": "FAIL"}` / `{"verdict": "REFUSE"}`. All human-readable detail goes
  to **stderr**. **`gate` exits `0` whenever it successfully emits a verdict** —
  the verdict is *data on stdout*, not exit status; a non-zero exit from `gate`
  is reserved for a crash or an unknown case name. (This keeps the Forgejury
  consensus fixtures comparing stdout, not exit codes.)
- `python -m buildoracle demo` — runs all four bundled cases and prints a
  human-readable table of their verdicts. **This is the demo command.**

#### Bundled cases (every build ships these four; semantics pinned here)

Each case is a small fixture bundling an *original* module, a *refactored*
variant, and an exercise script, under the package (e.g. `buildoracle/cases/`).
The exact fixture code is each build's own; the **verdict each case must produce
is pinned** so all three builds agree:

| case name          | what it contains                                                        | required verdict |
|--------------------|-------------------------------------------------------------------------|------------------|
| `identity`         | refactor is a behavior-preserving rewrite                               | `PASS`           |
| `offbyone`         | refactor introduces a bug (e.g. `+1`) that diverges on a recorded input | `FAIL`           |
| `nondeterministic` | module calls `time.time()` (or `random`) — not safely gateable          | `REFUSE`         |
| `keyorder`         | refactor returns the same dict content with different key insertion order | `PASS`         |

The `keyorder` case must `PASS` *because* of canonicalization, not by accident.

### Scope — what NOT to build (explicit)

- **No Head B (Disagreement Triage) and no Head C (Spec-Gap Report).** They are
  explicitly-optional reach for an ambitious executioner only, **never graded**,
  and a build that omits them entirely is a complete success. Do not let them
  pull the core off schedule. (If built, Head B drives N implementations over a
  shared input set and *ranks* disagreements by minority size — attention
  ranking, **not** a verdict; Head C relabels Head B's clusters as probable spec
  gaps. Both are reporting modes over the same engine, worth ~30 min each, and
  neither may be depended on for the build's success. The union-of-builds input
  set that widens coverage is a Head-B property — **Head A standalone has no such
  input source**; its coverage is honestly "recorded trace + existing tests
  only." Do not promise Head A coverage it cannot deliver.)
- **No blind fuzzing / property generation** as a load-bearing feature. At most
  an optional extra on annotated, pure, primitive-signature functions; never
  required, never graded. Synthesizing *valid* inputs is the hard part and is out
  of scope for the mandatory build.
- **No multi-language support.** Python target modules only. The "language-
  agnostic in spirit" framing stays in the README as motivation, not code.
- **No network, no subprocess-to-the-internet, no secrets.** The tool runs
  agent-written Python in-process/locally; it must work fully offline with no API
  keys. (Load-bearing for the review stage, which runs this code.)
- **No MCP server, no web UI, no model in the loop.** Standalone CLI only.

### Interface and demo command

Standalone Python CLI (Python 3.13, stdlib + `pytest`). Canonical demo:

```
python -m buildoracle demo
```

Expected: a table showing `identity → PASS`, `offbyone → FAIL`,
`nondeterministic → REFUSE`, `keyorder → PASS`, demonstrating the gate passing a
safe refactor, catching a real divergence, honestly refusing a nondeterministic
module, and seeing through a cosmetic key-order change via canonicalization.

### Acceptance criteria

1. `python -m buildoracle` is runnable (package has `buildoracle/__main__.py`);
   `python -m buildoracle demo` runs all four bundled cases and prints each
   case's verdict.
2. `python -m buildoracle gate --case <name>` prints **exactly** one line to
   stdout — `{"verdict": "PASS"}`, `{"verdict": "FAIL"}`, or
   `{"verdict": "REFUSE"}` (compact `json.dumps`, no extra stdout) — and **exits
   0** whenever it emits a verdict. The four bundled cases produce the pinned
   verdicts in the table above.
3. `classify`-then-refuse uses **both** an AST static scan **and** an empirical
   **double-run** trace comparison; a module that is nondeterministic *only*
   through behavior (not an obvious import) is still caught and produces
   `REFUSE`. The refusal names the reason (and the source line when the static
   scan located it).
4. `canonicalize` is exercised by dedicated `pytest` unit tests covering at
   least: **dict key-order** insensitivity, **float precision** rounding, and
   **string whitespace** normalization. At least one gate/verify path must pass
   *only because* canonicalization ran (the `keyorder` case).
5. `python -m buildoracle verify` replays a recorded trace against a module,
   prints `PASS` / `FAIL: diverged on input <...>` naming the diverging input,
   and uses exit codes `0` (PASS) / `10` (FAIL) / `20` (REFUSE).
6. Head A's report includes the honest coverage line
   `"coverage: recorded trace + existing tests only — unexercised paths not
   gated"`. The tool never claims coverage beyond what it ran.
7. The tool makes **no network calls and reads no secrets**; it runs fully
   offline. The README states this.
8. `README.md` documents: install/run, the demo command, the four verdict
   semantics, the record→classify→verify flow, the honest-refusal behavior, the
   coverage-honesty limitation, and that Heads B/C are optional and unbuilt (or
   how they were built, if an executioner reached for them).
9. `tests/test_core.py` covers `canonicalize` (criterion 4), the refuse path
   (criterion 3), and a pass-and-a-fail through `verify`; `python -m pytest -q`
   exits 0.
10. `claims.json` records, per acceptance criterion, whether the build claims it
    passes.

### Build-variance guardrails (why this spec is deterministic across all three builders)

The Forgejury consensus surface is `gate --case <name>`, whose stdout is a
**pinned one-line verdict** for four fixtures whose *semantics* this spec fixes
(not their internal code). So all three builds emit byte-identical stdout
(`{"verdict": "PASS"}` etc.) regardless of how each persona writes the fixture
modules or the engine — exactly like the `tier` surface in the previous cycle.
Keep `gate` stdout free of banners/logging (details → stderr). Everything
tree-/implementation-dependent lives behind `record`/`verify`/`classify` and is
exercised only by each build's own pytest suite.

## Forgejury Acceptance Block

```json
{
  "spec_checks": {
    "requires_file": ["README.md", "buildoracle/__main__.py", "buildoracle/core.py", "tests/test_core.py", "claims.json"],
    "requires_symbol": ["buildoracle/core.py::canonicalize", "buildoracle/core.py::classify", "buildoracle/core.py::verify"],
    "test_cmd": "python -m pytest -q",
    "runner": "pytest"
  },
  "consensus": {
    "invoke": "python -m buildoracle gate --case {input}",
    "fixtures": [
      { "name": "identity", "input": "identity", "expected": "{\"verdict\": \"PASS\"}" },
      { "name": "offbyone", "input": "offbyone", "expected": "{\"verdict\": \"FAIL\"}" },
      { "name": "nondeterministic", "input": "nondeterministic", "expected": "{\"verdict\": \"REFUSE\"}" },
      { "name": "keyorder", "input": "keyorder", "expected": "{\"verdict\": \"PASS\"}" }
    ]
  }
}
```
