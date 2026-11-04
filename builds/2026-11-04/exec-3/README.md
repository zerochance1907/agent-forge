# Forgejury (exec-3 build — the wild experimentalist)

One stdlib-Python gate on this pipeline's build→review handoff. It reads the
machine-readable **acceptance block** from a spec, independently re-observes
each build dir's real state, diffs that against what the build *claimed*
(`claims.json`), and runs each build against shared fixtures to triangulate
where the three builds actually agree or disagree. One verdict the reviewer
can read in seconds instead of three build folders top-to-bottom.

**stdlib only.** Nothing in `forgejury/` imports outside the Python 3.13
standard library. `pytest` is invoked as a subprocess only because the
toy example builds under `examples/` happen to use it as their test runner
-- it is not a dependency of Forgejury itself.

## Setup

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install pytest   # only needed to run *this
                                                  # build's own* test_cmd and
                                                  # the toy examples' test_cmd
                                                  # -- NOT imported by forgejury/
```

On Windows, make sure `.venv\Scripts` is on PATH before running the demo
below, since Forgejury's own `grade` shells out to `python -m pytest -q`
per build dir and needs that bare `python` to resolve to one with `pytest`
installed:

```
set PATH=%CD%\.venv\Scripts;%PATH%
```

(bash equivalent: `export PATH="$(pwd)/.venv/Scripts:$PATH"`)

## Demo

Run from this build dir (`builds/2026-11-04/exec-3/`):

```
python -m forgejury lint examples/SPEC.md
python -m forgejury grade examples/SPEC.md examples/build-a examples/build-b examples/build-c
```

`lint` surfaces a determinism warning on the `seeded-volatile` fixture
(its pinned `expected` deliberately contains a date and a hex address).
`grade` prints a table where:

- `examples/build-a` (honest) is all-`PASS`.
- `examples/build-b` (lying) shows `FAIL` in the claims axis, naming the
  exact lie: `tests_passed` claimed `3`, observed `2`; `test_cmd_exit`
  claimed `0`, observed `1`.
- `examples/build-c` is spec/claims-axis clean (it's honest about its own
  behavior) but the `boundary-bug` fixture shows a `2-1` consensus split
  naming `examples/build-c` as the diverging build, and the
  `negative-triway` fixture shows a genuine `3-way` split.

Add `--json` for the stable machine-readable schema instead of the table.

## The twist: a literal triangulation diagram

Forgejury's whole pitch is "one **triangulated** verdict." So the
human-readable `grade` report (not `--json`, which stays schema-stable)
ends with an actual triangle: one vertex per build, each edge labeled with
how many of the shared fixtures that pair of builds agreed on, colored
green/yellow/red by agreement ratio (ANSI; falls back to plain text when
`NO_COLOR` is set or stdout isn't a tty). On the bundled examples it renders
as:

```
Triangulation (pairwise fixture agreement):

        [A]
        / \
   4/5   3/5
      /     \
   [B] --- 3/5 --- [C]

  A = build-a
  B = build-b
  C = build-c
```

You can see at a glance that `build-a` and `build-b` agree on behavior more
often than either agrees with `build-c` -- the same information that's in
the per-fixture rows above it, just shaped so a reviewer's eye catches the
odd-one-out in one glance instead of reading five lines of text.

## Honesty statements

- **Claims axis = self-delusion detector, not a security boundary.** It
  catches "I reported 3 tests passing, the fresh run sees 2." It does
  **not** survive an executioner who runs Forgejury against their own build
  and then edits `claims.json` to match whatever Forgejury observed.
- **Consensus = attention router, not a correctness oracle.** With N=3, a
  2-1 majority can be two builds sharing the same wrong assumption while the
  minority build is actually right. The gate points the reviewer's
  attention at the disagreement; it does not resolve it. A pinned `expected`
  value turns one specific fixture into a real correctness check -- but
  only because `lint`'s determinism guard already rejected volatile pins,
  which is the only reason the 3-way signal in `negative-triway` is
  trustworthy instead of just noise.

## Layout

```
forgejury/
  __main__.py     CLI: lint, grade [--json]
  block.py        parse + validate the acceptance block, determinism guard
  symbols.py      ast-based symbol presence (no grep-guessing)
  observe.py      independent observation: files, symbols, test_cmd, pytest count
  spec_axis.py    build vs spec (the unkillable exit-code-0 gate)
  claims_axis.py  report vs reality (self-delusion detector)
  canon.py        CRLF/LF + trailing-whitespace canonicalization
  consensus.py    behavioral/stdout-only 3-0 / 2-1 / 3-way classification
  report.py       human table (+ triangulation diagram) and the --json schema
examples/
  SPEC.md         toy acceptance block: classify(n) by parity/magnitude
  build-a/        honest
  build-b/        lying (claims.json overstates test results)
  build-c/        honest about itself, but behaviorally diverges (the
                  consensus-layer story, deliberately decoupled from the
                  lying story)
tests/            forgejury's own test suite (pytest, 31 tests)
claims.json       this build's own dogfood claims
```

## Scope notes

- Layer 3 (fence/`--fence`) is **not built** -- `forge.py` serializes stages
  this cycle so it has near-zero dogfood value, and it's explicitly
  optional/not graded. Everything in layers 0-2 is complete.
- No prose/NLP claim parsing, no arbitrary report-command execution, no
  knowledge-graph/vector store, no AST public-surface diffing in consensus,
  no visual/browser capture layer. Consensus is behavioral (stdout) only.
- No third-party dependency in `forgejury/` itself; `pytest` is only ever
  invoked as a subprocess, and only because the bundled example builds
  chose it as their `runner`.

## License notes

No upstream code was vendored or copied. `Balanov/verdict` (Apache-2.0) and
`Balanov/skein` (MIT) contributed framing/ideas only (verify-real-state vs.
trust-the-report; epoch fencing for the optional, unbuilt layer 3) --
neither was read beyond its README, no code reused.
`Graphify-Labs/graphify` (Apache-2.0) was not consulted; stdlib `ast` was
sufficient and simpler for the symbol-presence check.
