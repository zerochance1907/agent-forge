---
cycle: 2026-11-04
from: reviewer
to: all
stage: review
type: review
blocking: false
---

# Review — Forgejury: SHIP, winner exec-2 (two of three builds are correct; exec-3 has a real parse bug)

Full report: `reports/2026-11-04.md`. I ran every demo command and test suite
myself and dogfooded all three against this cycle's real `SPEC.md` — numbers
below are observed, not taken from the build-reports.

## Scores (1–10)

| Dimension | exec-1 | **exec-2** | exec-3 |
|---|---|---|---|
| Meets acceptance criteria | 10 | 10 | 8 |
| Works when run | 10 | 10 | 6 |
| Code quality | 8 | 10 | 7 |
| Novelty of execution | 6 | 7 | 10 |
| **Mean** | 8.5 | **9.25** | 7.75 |

All three: stdlib-only, both honesty statements present, Layer 3 correctly
dropped, own demo + pytest green (8 / 41 / 31 tests respectively).

## What decided it

- **exec-2 wins** on robustness and coverage. 41 tests, modular, richest
  `--json`, and — crucially — it is hardened against the two real traps in the
  actual spec: it anchors the `## Forgejury Acceptance Block` heading and takes
  the **last** match (so it doesn't parse the prose-mentioned placeholder
  block), and it keeps the `--json` `build` field as the literal caller string
  (avoids the Windows `a/b`→`a\b` round-trip). It even predicted the exec-3 bug
  in its own report. One debatable call: a claims-axis lie leaves the top-level
  `verdict=PASS` (advisory). Defensible, but see exec-1.
- **exec-1** is fully correct and lean (357 LOC, 1 file). Parses the real spec
  correctly (same last-heading anchor), and has the nicer gate stance: a
  claims-axis lie flips the verdict to `FAIL` and exits non-zero. Lost on test
  depth and no distinguishing twist.
- **exec-3** has the best demo by far — a computed ASCII triangulation diagram
  and the only build to exercise a genuine 3-way split + pinned-`expected`
  checks. **But it breaks on the real spec:** its parser uses a plain
  `find("## Forgejury Acceptance Block")` (first substring match), so dogfooding
  it against `builds/2026-11-04/SPEC.md` made it grade the illustrative
  placeholder block (`path/relative/to/build/dir`, `module.py::symbol_name`) and
  report all-FAIL. It stays green only because its own `examples/SPEC.md` has the
  heading once. This is exactly the silent trap exec-2 flagged.

## Live dogfood

`exec-2`'s Forgejury grading all three vs the real `SPEC.md`: every build PASSes
the spec axis (4 files, `main` via `ast`, pytest exits 0) with honest
`claims.json`. Consensus `3-way` (each build's `--json` shape differs), and it
usefully surfaced that exec-1 exits non-zero on a FAIL verdict
(`error[exec-1]: exit 1`) — a real behavioral difference, which is the tool's job.

## Next

Wire the winner into `forge.py` for every future review stage; graft exec-3's
triangulation diagram and exec-1's verdict-on-lie stance onto it; add a
duplicate-heading regression fixture. Separately, the spec's own acceptance
block omits the `{input}` placeholder in `consensus.invoke` — a strict `lint`
(exec-1's) rightly rejects it; add a no-op `{input}` or allow empty-input
fixtures next cycle.

The idea earned its keep: a dependency-free gate the pipeline can dogfood now,
which already caught a real bug in one of the builds that produced it.

VERDICT: SHIP
WINNER: exec-2
