# Build Spec — Forgejury (cycle 2026-11-04)

> One stdlib-Python gate on the build→review handoff. It reads a
> machine-readable **acceptance block** that the reviewer authored in a spec,
> independently re-observes each build's state, diffs that against what each
> build *claimed*, and diffs the builds against each other on a thin-waist
> invocation contract. It emits one triangulated verdict the reviewer can read
> in ~30 seconds instead of three build folders top-to-bottom.

## Problem and target user

A multi-agent build pipeline (this one) fans one spec out to three parallel
coding agents, then the reviewer has to decide SHIP/ITERATE/RESTART. Today the
reviewer takes each executioner's prose build-report **on faith** — "exit code
0 is not proof." There is no independent check that (a) the code satisfies the
spec, (b) the report's claims match reality, or (c) where the three builds
actually disagree.

**Target user:** the reviewer of this pipeline (immediate dogfood), and more
broadly any orchestrator fanning one spec out to parallel coding agents who
needs to trust self-reports without reading every file.

## Upstream repositories

Adopt **patterns/ideas only** — do not vendor or commit third-party code
wholesale. License-check before touching any upstream code and record it in
your build-report.

- **Balanov/verdict** — https://github.com/Balanov/verdict — Apache-2.0.
  Take the *framing* only: verify a claimed effect against real system state
  rather than trusting a self-report. No code.
- **Balanov/skein** — https://github.com/Balanov/skein — MIT. Epoch/fencing
  token idea, used only by the **optional** fence layer (layer 3). No code.
- **Graphify-Labs/graphify** — https://github.com/Graphify-Labs/graphify —
  Apache-2.0. Inspiration for deterministic, no-vector parsing. **Not a
  dependency** — Python stdlib `ast` is sufficient.

You should not need any upstream code at all. If you do reuse a snippet,
cite the file, the license, and why in your build-report.

## Scope

**Language/runtime:** Python 3.13, **standard library only** (no PyYAML, no
pytest-as-dependency — you may *invoke* pytest as a subprocess if a fixture
build uses it, but Forgejury itself imports nothing outside stdlib). This
keeps it portable and unkillable on a plain Windows box, no GPU.

**Entrypoint (mandatory, identical across all three builds so the reviewer can
judge you consistently):** `python -m forgejury ...`

### Build these layers, in this order (shippable at any prefix)

- **Layer 0 — `lint` (REQUIRED):** validate the acceptance block before any
  build runs. Required keys present, `test_cmd` non-empty, `invoke` present and
  contains the `{input}` placeholder, each fixture concrete. **Determinism
  guard:** warn (non-zero advisory) when a fixture's pinned `expected` output
  looks volatile — matches an obvious date, a temp/absolute path, a `0x…`
  hex address, or a UUID. This guard is what makes the layer-2 3-way signal
  trustworthy; do not skip it.
- **Layer 1 — `grade` floor (REQUIRED):** for each build dir, independently
  observe state and produce **two axes**:
  - **Spec axis** (build vs spec): each `requires_file` exists; each
    `requires_symbol` is defined (stdlib `ast` walk, not grep-guessing); the
    declared `test_cmd` exits 0. The unkillable gate is **exit code 0**.
  - **Claims axis** (report vs reality): diff the build's `claims.json` against
    what Forgejury actually observed (files present, symbols present, test exit
    code, and `tests_passed` *only when* the block declares a `runner`). Each
    cell is `PASS` / `FAIL` / `UNVERIFIABLE`.
- **Layer 2 — `grade` consensus (REQUIRED):** run the block's canonical
  `invoke` on each `fixture` in each build dir, **canonicalize stdout before
  diffing** (strip trailing whitespace per line, normalize CRLF→LF), then:
  - **3–0 agree** → bedrock, trust it.
  - **2–1 split** → route reviewer attention to the diverging build (this is an
    *attention heuristic, not a correctness verdict*).
  - **3-way split** → flag the **spec/fixture as ambiguous** (valid only
    because layer 0 forbade volatile fixtures; otherwise it would be
    indistinguishable from nondeterministic output).
  - When a fixture declares a pinned `expected`, also compare each build's
    canonicalized stdout to it (a correctness check, not just agreement).
  Consensus is **behavioral (stdout) only** — do **not** diff AST public
  surface; three personas legitimately differ internally and that is noise.
- **Layer 3 — fence (OPTIONAL / stretch):** a `--fence <epoch>` option that
  rejects a build-report carrying a stale/duplicate epoch token. Real swarm
  bug, but `forge.py` serializes stages this cycle so it has near-zero dogfood
  value. **Drop this first if time is short.** Not required to pass review.

### Explicitly do NOT build

- **No prose/NLP parsing** of build-reports. The contract is `claims.json`.
- **No arbitrary command execution** from the report. Run only the
  spec-declared `test_cmd` and `invoke` — never a command a report names.
- **No graphify knowledge-graph / vector store.** stdlib `ast` only.
- **No AST public-surface diff** in consensus. Behavioral/stdout only.
- **No SeeTest / visual acceptance / browser capture.** Nothing this cycle
  renders a UI; out of scope.
- **No third-party dependencies** in Forgejury itself.

### Honesty statements your output and README must carry

- **Claims axis = self-delusion detector, not a security boundary.** It catches
  "I reported 12 pass, the fresh run sees 9." It does *not* survive an
  executioner who runs Forgejury and tunes `claims.json` to match.
- **Consensus = attention router, not a correctness oracle.** With N=3, a 2–1
  majority can be two builds sharing the same wrong assumption. The gate points;
  the reviewer decides.

## Data formats (pin these exactly — all JSON, stdlib-parseable)

**Acceptance block** — a fenced ` ```json ` code block in a spec file,
immediately under a heading line `## Forgejury Acceptance Block`:

```json
{
  "spec_checks": {
    "requires_file": ["path/relative/to/build/dir"],
    "requires_symbol": ["module.py::symbol_name"],
    "test_cmd": "command run with cwd = build dir",
    "runner": "pytest | exit-code",
    "expected_tests_pass": 0
  },
  "consensus": {
    "invoke": "python app.py {input}",
    "fixtures": [
      { "name": "add-small", "input": "2 3", "expected": "5" }
    ]
  }
}
```

`runner`, `expected_tests_pass`, and each fixture's `expected` are optional.
`invoke` is run with cwd = each build dir, `{input}` substituted verbatim.

**`claims.json`** — one per build dir, next to the human-facing report:

```json
{
  "cycle": "2026-11-04",
  "files": ["app.py", "README.md"],
  "symbols": ["app.py::main"],
  "test_cmd_exit": 0,
  "tests_passed": 3
}
```

## Interface

- `python -m forgejury lint <spec.md>` → layer 0; prints validation result,
  exits 0 if the block is valid (warnings allowed), non-zero on hard error.
- `python -m forgejury grade <spec.md> <build-dir> [<build-dir> ...]` →
  layers 1+2; prints the triangulated verdict table (human-readable) to stdout.
- `python -m forgejury grade ... --json` → emits a **stable machine-readable
  JSON** verdict instead of the table. Required so the review stage can diff the
  three Forgejury builds against each other. Minimum schema per build:
  `{ "build": "<dir>", "spec_axis": {<check>: "PASS|FAIL|UNVERIFIABLE"},
  "claims_axis": {<field>: "PASS|FAIL|UNVERIFIABLE"}, "verdict": "PASS|FAIL" }`
  plus a top-level `"consensus": {<fixture>: "3-0|2-1|3-way",
  "diverging_build": "<dir|null>"}`.

## Required deliverables in your build dir

```
builds/2026-11-04/<your-exec-id>/
  forgejury/              # package, runnable as `python -m forgejury`
  examples/
    SPEC.md               # a sample spec containing one acceptance block
    build-a/  build-b/  build-c/   # three toy builds + a claims.json in each
  tests/                  # your tests
  claims.json             # YOUR claims about THIS Forgejury build (dogfood)
  README.md               # how to run + the two honesty statements above
```

The bundled `examples/` must self-demonstrate the full signal:
one **honest** build (all green), one **lying** build (`claims.json` says more
tests pass / more files exist than reality), a **2–1 consensus** divergence on
at least one fixture, and a **seeded nondeterministic fixture** that `lint`
catches with its determinism guard.

## The exact demo command

Run from your build dir, in this order:

```
python -m forgejury lint examples/SPEC.md
python -m forgejury grade examples/SPEC.md examples/build-a examples/build-b examples/build-c
```

The first must surface the determinism warning on the seeded volatile fixture.
The second must print a verdict table where the honest build is all-PASS, the
lying build shows a `FAIL` in the claims axis **naming the lie**, and the
consensus row shows a 2–1 split flagging the diverging build.

## Acceptance criteria (numbered, checkable)

1. `python -m forgejury` runs as a module with `lint` and `grade` subcommands;
   no third-party imports in the `forgejury` package.
2. `lint` validates the acceptance block: fails loudly on missing required keys
   or a missing `{input}` in `invoke`.
3. `lint` emits a determinism **warning** for a fixture whose `expected` output
   matches a date / temp path / `0x…` address / UUID.
4. `grade` spec axis: correctly reports presence of every `requires_file` and
   `requires_symbol` (via `ast`) and whether `test_cmd` exits 0, per build.
5. `grade` claims axis: diffs `claims.json` against observed state and marks
   each field `PASS`/`FAIL`/`UNVERIFIABLE`; a build claiming more passing tests
   or more files than reality is marked `FAIL` with the specific field named.
6. `grade` consensus: runs `invoke` per fixture per build, canonicalizes stdout
   (trailing whitespace + CRLF/LF), and classifies each fixture `3-0` / `2-1` /
   `3-way`, naming the diverging build on a 2–1 split.
7. `grade --json` emits the stable schema above (parseable by `json.loads`).
8. Bundled `examples/` demonstrate honest, lying, 2–1-divergent, and
   nondeterministic-fixture cases; the exact demo commands above produce the
   described output.
9. `tests/` exist and the declared `test_cmd` for this build exits 0.
10. `README.md` states both honesty limitations (claims axis = self-delusion
    detector, not security; consensus = attention router, not oracle).
11. Consensus is behavioral/stdout only — no AST public-surface diffing.
12. Runs on Windows, Python 3.13, with no network access and no GPU.

Layer 3 (fence) is **not** graded; include it only if everything above is done.

## Forgejury Acceptance Block

```json
{
  "spec_checks": {
    "requires_file": ["forgejury/__main__.py", "README.md", "claims.json", "examples/SPEC.md"],
    "requires_symbol": ["forgejury/__main__.py::main"],
    "test_cmd": "python -m pytest -q",
    "runner": "pytest"
  },
  "consensus": {
    "invoke": "python -m forgejury grade examples/SPEC.md examples/build-a examples/build-b examples/build-c --json",
    "fixtures": [
      { "name": "triangulated-verdict", "input": "" }
    ]
  }
}
```

DECISION: Forgejury — one acceptance-block gate on the build→review handoff
