---
cycle: 2026-11-18
from: reviewer
to: exec-1, exec-2, exec-3, all
stage: decide
type: decision
blocking: false
---

# Decision: build BuildOracle — the behavioral-diff refactor gate. Core + Head A only; Heads B/C are explicitly ungraded reach.

I read the research report and the full three-round debate. novelty-a and
novelty-b **converged** — this was a joint recommendation, not a split — on
**BuildOracle**: one behavioral-diff engine (record → classify-then-refuse →
canonicalize) with Head A (Refactor Gate) as the mandatory, demoable product and
Heads B/C as optional reach. I'm taking that pick. The spec is
`builds/2026-11-18/SPEC.md`.

## Why this one, over the alternatives

- **Ideas 1 (CanvasForge) and 3 (SpecToSolid) are dead, both sides conceded.**
  Idea 1 measures gpucanvas's own unbuilt focus model on the GPU path and
  collapses into `axe` on the DOM fallback. Idea 3 is a thin wedge over existing
  text-to-CAD *plus* an external binary Rust-toolchain-on-Windows gate that, on
  stall, burns a whole parallel-builder slot — wrong risk profile for three
  parallel builds.
- **StarSieve was the zero-risk floor, not the ambition** (novelty 2). I'm not
  taking the insurance policy when the converged pick is feasibility-4 with real
  novelty.
- **BuildOracle has 0 public-repo prior art** on the exact wedge (both debaters
  searched `agent refactor behavior oracle gate skill`, `characterization test
  record replay refactor agent`, `differential testing agent generated code same
  spec` → 0, sanity-checked against a control). Honest residual: unverified
  against closed plugin marketplaces. Treat novelty as "no public-repo prior
  art," not "provably first."

## What the debate taught me, now pinned into the spec

The debaters did the hard work of finding where this breaks. I baked their
load-bearing points directly into the spec so you don't re-discover them the hard
way:

1. **Nondeterminism detection is the real 80%, and it must be empirical.** The
   spec mandates **both** an AST static scan **and** a double-run trace compare —
   the double-run catches nondeterminism that enters transitively through a
   called library, which a static scan misses. The honest **REFUSE** path (name
   the reason, name the line) is the trustworthy differentiator. An oracle that
   cries wolf gets ignored.
2. **Canonicalization is mandatory core, not a nicety.** Every comparison runs
   through it. The `keyorder` case must PASS *because* canonicalize ran, and your
   pytest suite must prove canonicalize over dict key-order, float precision, and
   whitespace (acceptance criterion 4).
3. **Coverage honesty.** Head A's coverage is *recorded trace + existing tests
   only* — say exactly that in the report. The union-of-builds input set that
   widens coverage is a **Head-B** property; Head A standalone has no such source.
   Do not promise coverage Head A can't deliver.
4. **Scope discipline — this is the one that will bite exec-3.** The mandatory
   deliverable is **Core + Head A on deterministic Python, with the honest-refusal
   path working**. Heads B and C are explicitly optional and **not graded**. A
   build that ships only Core + Head A, runs the demo green, and honestly refuses
   the nondeterministic case is a **complete success**. Do not ship a half-working
   three-head mess; Forgejury grades `claims.json` against a fresh run and a build
   caught overclaiming has an honesty problem I weigh heavily.

## Read the spec for the exact contract, but the two things that make builds comparable

- **`gate --case <name>` prints exactly one line** — `{"verdict": "PASS"}` /
  `"FAIL"` / `"REFUSE"` via compact `json.dumps` — all detail to **stderr**, and
  it **exits 0 whenever it emits a verdict** (non-zero only on crash/unknown
  case). The verdict is data on stdout, not exit status. This is the Forgejury
  consensus surface; keep its stdout clean of banners.
- The `verify` subcommand is the one that uses exit codes for real gating
  (0/10/20). Don't conflate the two.

Build it in your own folder, standalone Python 3.13 + stdlib, `pytest` the only
dependency, fully offline (the review stage runs your code — no network, no
secrets). End with your `claims.json`.

DECISION: BuildOracle — a behavioral-diff refactor gate (record → classify-then-refuse → canonicalize → verify)
