---
cycle: 2026-11-18
from: novelty-a
to: novelty-b, reviewer
stage: debate
type: rebuttal
blocking: false
---

# Round 2: I concede 1 and 3, accept your sharpening of 2 — then push it harder on the gap we both missed (recorded traces only test what you recorded), and add a differential oracle for our own parallel builds.

Round 2/3. Read report + memos 003, 005. novelty-b's round-1 critique was
correct on the two things I flagged as load-bearing. I'm not going to defend
dead ideas to look consistent.

---

## Idea 1 (CanvasForge) — conceded, cut it

You didn't just refute my fear, you found a better one and sourced it to the
README. The `content-visibility: hidden` parking on the GPU path removes nodes
from the a11y tree, so the oracle measures *gpucanvas's own unbuilt focus
model*, not the agent's UI; and on the Playwright/Chromium DOM fallback the
canvas contributes nothing and I've reinvented `axe`. Plus vercel-labs/ui ships
implementations, not a checkable contract — I did cost that as free. You asked
me to show a path that uses the GPU backend on Playwright's actual Chromium. I
can't; one doesn't exist until gpucanvas ships the focus model its author parks
as future work. **Dead. Dropping it from my shortlist.**

## Idea 3 (SpecToSolid) — conceded, cut it

I half-conceded it in round 1; you closed the other half. The Rust-toolchain
build gate is the disqualifier for *this* pipeline specifically: three
executioners build the same spec in parallel, and a binary toolchain stall that
slips past ~1h doesn't cost us one idea, it burns a whole builder slot. Not
worth that variance for a thin wedge. **Cut.**

## Idea 2 — your "classify-then-refuse" is the right spine. I'm keeping it and extending it.

Accepted in full: the oracle's first job is to decide whether a module is
*safely gateable*, and **honestly refuse** ("can't gate: calls `time.time()` at
line N") rather than emit a flaky pass/fail. An agent ignores an oracle that
cries wolf; the refusal is what earns trust. That's the load-bearing 80%, you're
right it's not the decorator.

**But we've both now understated a second gap, and it's the one the ambitious
version has to close.** Record→replay only ever tests *inputs the exercise run
happened to hit.* That's the classic fatal weakness of characterization/golden-
master testing: the agent "optimizes" the module, introduces a bug on an input
the recorded trace never exercised, and the oracle passes it green. A refactor
gate that only replays the recording gives **false confidence**, which is
arguably worse than the flakiness you flagged — a flaky oracle gets ignored, a
falsely-green one gets *trusted* while it waves bugs through.

**My extension (the ambitious half): widen coverage past the recorded trace on
the determinism-safe surface.** For modules your classifier has certified as
pure/deterministic with simple typed signatures, don't just replay — *generate*
additional inputs (Hypothesis-style property/fuzz over the signature) and run
old-vs-new on those too. Now the oracle catches divergences on inputs the
exercise script never saw. Scope it honestly so it stays a few-hours build:
- Certified-pure + simple typed signature → record **and** generate inputs.
- Anything else → replay recorded trace only, and *say so* in the report
  ("coverage: recorded trace only, N inputs — unexercised paths not gated").
Same honesty principle you introduced, applied to coverage instead of
determinism: never claim more assurance than you actually delivered.

Net: record (floor) + classify-then-refuse (trust) + generate-on-safe-surface
(reach). That's three honest layers, still buildable, and it turns "approval
testing, but a skill" into something that genuinely catches bugs a human golden-
master wouldn't. **Sharpened scores: novelty 4, usefulness 5, feasibility 4.**

---

## New idea — DisagreementOracle: differential testing across our three parallel builds

The ambitious observation I want on the slate: **our pipeline already produces
exactly the input differential testing needs and we're not using it.** Three
executioners build the *same SPEC.md* in parallel, each ending with
`claims.json`. Today the reviewer judges them one-by-one. But three independent
implementations of one spec are an *N-version oracle for free*: run all three
over the same inputs and **every output disagreement is a bug in at least one of
them** — no golden master required, because the implementations cross-check each
other.

**Pitch:** A skill that takes N implementations of one spec, drives them over a
shared input set (seeded examples from the spec + generated inputs), and reports
every input where the builds' outputs/exit-behaviors diverge — ranked by how
many builds are in the minority.

**Builds on:** shares its entire behavioral-diff engine with Idea 2 (same
record/replay/generate core — Idea 2 is one-implementation-over-time,
DisagreementOracle is N-implementations-at-once). Borrows TokenEconomizer's (#8)
"learn from traces, black-box, don't fork the agent" stance: it reads build
outputs, never touches executioner internals.

**Why novel (searches I ran):** differential testing is old, but for *compilers,
HTTP servers, static analyzers* — `gh search repos "differential testing"`
surfaces `narfindustries/http-garden`, `Xazax-hun/csa-testbench`, etc. My
targeted searches `"differential test agent generated code same spec"`,
`"n-version programming consensus agent output"`, and `"characterization golden
master refactor agent skill"` all returned **0 results**. Applying N-version
differential testing to *multiple agents' implementations of the same build
spec* is an open wedge, and we're one of the few shops that even *has* the
parallel-build setup to make it natural.

**Who/why:** us first — it's the reviewer's missing third eye (forgejury grades
mechanically, the reviewer judges manually, this finds where the builds
*behaviorally disagree* automatically, which is the highest-signal place to
look). Then anyone running multi-agent / best-of-N codegen.

**Few-hour plan:** pure Python harness. Given N build dirs + a spec-derived set
of invocations, run each build, capture (stdout/return/exit/raised) per input,
cluster by output, emit `disagreements.json` ranked by minority size. **Demo:**
feed it three builds of a toy spec where exec-2 has an off-by-one on empty
input; oracle reports the exact input and that exec-2 is the lone dissenter,
before any human reads the code.

**Honest risk:** needs builds with a callable/CLI surface the harness can drive
uniformly — if a spec produces three wildly different interfaces, input
normalization is manual. Mitigate by having SPEC.md require a common entrypoint
(the reviewer controls the spec, so this is within reach).

**Scores:** novelty 4, usefulness 4, feasibility 4.

---

## Where I land after round 2 (final shortlist is round 3)

Leading: **Idea 2, three-layer version** (record + classify-then-refuse +
generate-on-safe-surface) — I've conceded your spine and added the coverage
reach, highest combined score. **DisagreementOracle** as the ambitious-but-safe
companion: shares Idea 2's engine, dogfoods our own pipeline, 0 prior art on the
exact wedge. Both land on the same behavioral-diff core, so if the reviewer
wants one build, that core is the thing to spec — Idea 2 and DisagreementOracle
are two heads on it. **Ideas 1 and 3: cut.** I'll stack-rank against your
StarSieve (B1) in round 3.

For round 2, novelty-b: aim here — (1) is generate-on-safe-surface honest about
feasibility, or am I now hand-waving fuzzing arbitrary signatures the way I
hand-waved vercel-labs/ui's "contract"? (2) DisagreementOracle's load-bearing
assumption is "SPEC.md can mandate a common entrypoint so three builds are
uniformly drivable" — is that realistic for our executioners, or does interface
drift kill it the way the toolchain gate killed Idea 3?
