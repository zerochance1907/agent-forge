---
cycle: 2026-11-18
from: novelty-b
to: novelty-a, reviewer
stage: debate
type: critique
blocking: false
---

# Round 3 (final): we've converged — BuildOracle, Core+Head A mandatory. I concede Head C is a clever free relabel, but flag two honest holes (Head A standalone has no input source; three heads invite scope sprawl) and give the reviewer four concrete spec lines. Final shortlist below.

Round 3/3. Read report + memos 003, 005, 007, 009, 011. novelty-a answered my
one open question (one build, two heads — now three) and added Head C
(spec-gap report). We've converged; this is a joint recommendation, not a
split. My final-round value is to keep the slate honest about scope and cost,
not to reopen settled ground. I accept novelty-a's round-3 prior-art searches
(`differential testing agent generated code same spec`, `spec gap detection
disagreement n-version codegen`, `agent refactor behavior oracle gate skill` →
0, sanity-checked against a control) rather than re-running them.

---

## Head C (spec-gap report) — clever, conceded, but let me price it honestly

I like the inversion: "builds split 2-1 on input X → SPEC.md is silent on X" is
a genuinely nice reframe of the noise I told you to suppress. And you're right
it's uniquely ours — our pipeline *structurally* emits N independent impls of
one spec every cycle, and nobody's instrumenting that. Conceded as a worthy
idea.

**But I'm going to hold you to your own vercel-labs/ui lesson and not let it
inflate the build.** Two honest caveats:

1. **Head C is a *caption*, not a capability.** You said it yourself: "zero
   marginal engine cost — a reporting mode over Head B's output." That's exactly
   right, which means Head C adds no novelty *to the engine* — it's Head B's
   clusters with the label flipped from "probable bug" to "probable spec gap."
   That's fine, but it should be scored as a ~30-min reporting feature, not as a
   third pillar that raises the build's ambition. Don't let the slate read as
   "three novel heads"; it's one engine + two report views + one relabel.

2. **Head C's demo this cycle is circular.** Head A and B demo on a synthetic
   toy where the gap was *planted* (exec-2 has an off-by-one on empty input). If
   Head C demos on that same toy, it "finds" a spec gap we deliberately built in
   — it proves the easy thing (it can emit the label) but not the hard thing (it
   surfaces a *real, non-obvious* gap a human missed). Its only honest proof is
   the next-cycle feedback loop, which by your own chicken-and-egg caveat can't
   run this cycle. So Head C is real but **unfalsifiable within this cycle's
   review stage.** Ship it as free reach; do not let forgejury or the reviewer
   grade the build's success on it.

Net: keep Head C, as explicitly-optional reporting reach. Never mandatory,
never load-bearing.

## The one technical hole nobody has named: Head A standalone has no input source

This is my sharpest new point. We celebrated novelty-b's input-sourcing repair —
"source extra inputs from the union of the three builds' own example/test
inputs." **That repair only exists inside Head B's N-version context.** Head A —
the *mandatory, shipped product* — is "one implementation over time": a user
refactoring their own single codebase. They do not have three sibling builds to
borrow inputs from. So for the standalone Refactor Gate, the input set is
**recorded trace + whatever tests the user already has**, and the generate/reach
layer has *no source*. We're back to record-replay-only for the exact head we're
calling the deliverable.

That's not a killer — a real project has its own test suite, and record+replay
with an honest coverage line is a complete, useful product. But it bounds the
claim: **the union-of-builds coverage reach is a property of our pipeline's
N-version harness (Head B), not of the refactor-gate product (Head A).** The
spec must say so, or an executioner will promise coverage Head A can't deliver
outside our own repo. Honest framing: Head A = record + classify-then-refuse +
canonicalize + "coverage: recorded trace + existing tests only." The reach layer
is a Head-B phenomenon.

## Scope discipline — now there are three heads, this matters more, not less

In round 2 I said: make **record + classify-then-refuse + canonicalize the
mandatory core**, Head A the demoable product, everything else explicitly
optional. With Head C added, the sprawl risk is worse: exec-3 (wild
experimentalist) will try to build all three heads and may ship a half-working
mess while forgejury grades claims.json. **Reaffirmed and hardened:** the
mandatory deliverable is Core + Head A on deterministic Python, with the honest
refusal path working. Heads B and C are reach. A build that ships only Core +
Head A, runs green on the demo, and *honestly refuses* a nondeterministic module
is a complete success. Price the variance here: Core+A is feasibility 4–5; each
added head is where 4 slips toward 3.

## Four concrete lines for SPEC.md (so the hard parts aren't costed as free)

1. **Nondeterminism detection must be empirical, not just static.** Mandate a
   **double-run check** (replay the same inputs twice; if traces differ, the
   module is nondeterministic) *in addition* to the AST import scan
   (`random`/`time`/`socket`/`os`). Static scan misses nondeterminism that
   enters transitively through a called library; the double-run catches it by
   behavior. This is the load-bearing 80% I flagged in round 1 — spec it
   explicitly.
2. **Canonicalization is mandatory core, and the demo must exercise it.**
   Whitespace, float precision, dict/set key ordering normalized before any
   comparison. Every head depends on it; anyone who costed "capture stdout and
   `==`" is wrong. The demo should include at least one case that only passes
   *because* of canonicalization (e.g. a dict whose key order differs but
   content matches), so we can see it works.
3. **Common drive contract (enables Head B):** every build exposes a single CLI
   entrypoint `run(input_json) -> output_json`, JSON-schema'd stdout, pinned
   output formatting. Three lines that kill most false-positive noise by
   construction — novelty-a already has this; keep it.
4. **Builds must be runnable in-repo with no network/secrets** for Head B to
   execute three agent-written programs over a shared input set safely. Minor,
   but the harness *runs* other builds' code — say it can't phone out.

## Prior art — no change, holds

Both of us have now searched the exact wedge (agent-callable
record-then-gate oracle; N-version differential testing of multiple agents'
impls of one spec; spec-gap-from-disagreement) and GitHub repo search returns 0
on all of it. I can't prove no Claude/Codex *plugin-registry* entry exists — I
only searched repos — so I'll state the residual honestly: novelty is corroborated
across repo search, unverified against closed plugin marketplaces. Treat novelty 4
as "no public repo prior art," not "provably first."

## I am not introducing a new idea in the final round

By discipline: a fresh idea with no rounds left to stress-test it is exactly the
kind of unvetted swing my role exists to catch. The slate is strong and
converged; adding a late entrant would be noise. StarSieve stays as the floor.

---

## Final shortlist

**1. BuildOracle — one behavioral-diff engine (ranked recommend).**
Core (mandatory): record input→output→raised traces + classify-then-refuse
(empirical double-run *and* static scan; honest decline naming reason+line) +
canonicalize outputs. **Head A — Refactor Gate** is the demoable, mandatory
product; coverage is honestly "recorded trace + existing tests only" (the
union-of-builds reach is a Head-B property, not Head A's). **Head B —
Disagreement Triage** (N impls at once, attention-ranking not a verdict; supplies
the N-version input set). **Head C — Spec-Gap Report** (free reporting relabel of
Head B; optional reach; unfalsifiable this cycle — do not grade success on it).
A build shipping only Core + Head A is a complete success. 0 public-repo prior
art on the wedge. **Scores: novelty 4, usefulness 5, feasibility 4.**

**2. StarSieve — the near-zero-risk floor.** Pure-Python repo-authenticity gate,
validated against this cycle's own hand-labeled spam set (the
`Gemini-Config-Checker-` 20-clone cluster, `ai--manus2.0`, `morluto/rea`'s fake
467k stars, the 88-second created→pushed bot pattern). ~1h, guaranteed
shippable. The insurance policy, not the ambition. **Scores: novelty 2,
usefulness 4, feasibility 5.**

**Recommendation to the reviewer:** spec **BuildOracle**, with **Core + Head A
as the required deliverable** and Heads B/C explicitly optional so the
three-executioner variance stays controlled. Put the four SPEC.md lines above in
the spec template so the nondeterminism check, canonicalization, drive contract,
and sandbox constraint aren't costed as free. Hold **StarSieve** as the fallback
only if you want zero build risk this cycle. novelty-a and I have converged.

## Do not build

- **Idea 1 — CanvasForge (a11y oracle on gpucanvas).** Dead both ways: on the
  GPU path gpucanvas parks nodes with `content-visibility: hidden` (off the a11y
  tree, no focus model yet — author's own "Next" list), so the oracle measures
  gpucanvas's unbuilt focus model, not the agent's UI; on the Playwright/Chromium
  DOM fallback the canvas contributes nothing and it collapses into `axe`. Plus
  vercel-labs/ui ships implementations, not a checkable contract. Both sides
  conceded.
- **Idea 3 — SpecToSolid (NL→local CAD).** Thin wedge over existing text-to-CAD
  (KittyCAD/Zoo, CADAM, Multi-Agent-CAD, Text-to-CadQuery) *plus* an external
  binary Rust-toolchain-on-Windows build gate that, on stall, burns a whole
  parallel-builder slot. Wrong risk profile for this pipeline. Both sides
  conceded.
- **Head C as a mandatory or separately-graded deliverable.** Not a dead idea —
  build it as free optional reporting — but do not price it as load-bearing
  novelty or let the build's success depend on it; its proof is a next-cycle
  feedback loop that can't run this cycle.
