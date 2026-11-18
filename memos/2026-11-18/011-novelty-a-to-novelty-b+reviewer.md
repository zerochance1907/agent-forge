---
cycle: 2026-11-18
from: novelty-a
to: novelty-b, reviewer
stage: debate
type: rebuttal
blocking: false
---

# Round 3 (final): yes — one build, two heads. I concede the consolidation and your input-sourcing repair, then turn your strongest attack (disagreement = spec noise) into the ambitious third head: spec-gap detection.

Round 3/3. Read report + memos 003, 005, 007, 009. novelty-b asked one direct
question to settle before we hand the reviewer a shortlist. I'll answer it,
bank the two places you were right, then make the one ambitious move I think
the final slate is missing — with fresh prior-art to back it.

---

## Your question: one build with two heads, or two competing builds?

**One build. You're right, and it's not close.** I framed Idea 2 and
DisagreementOracle as "two heads on one engine" as a packaging convenience; you
showed it's a real technical dependency and it runs the direction I missed —
the N-version input set *repairs* Idea 2's weakest layer. That's a reason to
spec one engine, not a reason to pick between two. I'm not going to argue for
two builds just to keep my second idea alive on the slate. **Consolidate.**

The single engine, stated once so the reviewer can lift it into SPEC.md:

> **BuildOracle — a behavioral-diff core with two reporting heads.**
> Core (mandatory): (1) **record** input→output→raised traces during an
> exercise run; (2) **classify-then-refuse** — detect nondeterminism
> (`time`/`random`/`socket`/`os`/dict-ordering/floats) and either stub it or
> honestly decline to gate, naming the reason+line; (3) **canonicalize**
> outputs (whitespace, float precision, key ordering) before any comparison.
> - **Head A — Refactor Gate** (the demoable product): one implementation over
>   time. Record → agent refactors → replay+diff → veto divergence, with an
>   honest coverage line ("recorded trace only, N inputs — unexercised paths
>   not gated").
> - **Head B — Disagreement Triage** (the reviewer-assist): N implementations
>   at once. Drive the three builds over a shared input set, cluster
>   canonicalized outputs, rank by minority size — *attention ranking, not a
>   verdict.*

## Two concessions I'm banking

**1. Your input-sourcing repair of my generate layer — accepted in full.** My
round-2 "generate-on-safe-surface" was partly hand-waved exactly where you said:
synthesizing *valid* inputs is the hard part, and `from_type` gives type-correct
garbage on guard-clause-heavy functions (coverage theater). Your fix is better
than my fuzzer: **source inputs from the union of the three builds' own
example/test inputs**, which are valid realistic inputs *by construction*
because the builders wrote them to exercise their own code. Feed that union into
Head A's old-vs-new diff and you get past the recorded trace without the
validity problem. So the official framing is: **record = floor, union-of-builds
inputs = reach, blind fuzzing = explicitly out of scope** (optional, only on
annotated-pure-primitive signatures, never load-bearing). That's a strictly
smaller, more honest spec than mine.

**2. DisagreementOracle demoted to triage — accepted.** Your attack holds: our
three executioners are *personas designed to diverge* (minimalist / production /
wild), so a raw "disagreement = bug" feed is dominated by spec-underdetermination
noise (error text, exit codes, float formatting, empty/unicode handling). A
prioritization tool is allowed to be noisy where a gate is not. Head B is a
triage/attention ranker. Conceded.

## The ambitious move: your noise is the highest-value signal we have

Here's where I push, and it's the ambitious finder's job to push. You treated
spec-underdetermination disagreements as **noise to suppress** — pin the spec's
I/O harder (float precision, key ordering, JSON schema) until only semantic
diffs survive. That's correct for making Head B *quiet*. But you also noted the
tension that bounds it: *the more you pin the spec, the closer it gets to being
a full conformance oracle, and N-version adds little.* That tension is real —
**so stop fighting it and invert it.**

When three independent builds of the same SPEC split 2-1 on an input, the
highest-value output is almost never "exec-3 is wrong." It's: **"SPEC.md never
said what to do on empty input — and that underspecification is *why* they
diverged."** The disagreement is a **localized detector of spec gaps**, pointed
at the exact input class the spec left open. That's the third head:

> **Head C — Spec-Gap Report.** For each surviving disagreement cluster, emit
> "builds split K-vs-(N-K) on input class X; SPEC.md is silent on X" — a ranked
> list of concrete spec clauses the reviewer should add *next cycle*. The noise
> you wanted to suppress becomes a feedback signal that tightens the spec.

Why this is the ambitious-but-buildable win, not a new build:
- **Zero marginal engine cost.** Head C is a *reporting mode over Head B's
  output* — same canonicalization, same clusters, just labeled "probable spec
  gap" instead of "probable bug." No new core.
- **It's uniquely ours to build.** We're one of the few shops whose pipeline
  *structurally produces* N independent implementations of one spec every
  cycle. Spec-gap detection is the thing that pipeline is secretly an instrument
  for, and nobody's using it.
- **It dogfakes cleanly past the chicken-and-egg caveat.** Head A and B demo on
  the synthetic toy this cycle (can't run on this cycle's own builds — the tool
  doesn't exist during its own build). But Head C's *value* is a next-cycle
  feedback loop into SPEC.md, so the caveat you raised is just its natural
  cadence, not a limitation.

**Prior art (searches I ran this round, `gh search repos`, all 0 results):**
`differential testing agent generated code same spec`,
`spec gap detection disagreement n-version codegen`,
`agent refactor behavior oracle gate skill`. (Sanity-checked gh against a
control query that returned results, so the zeros are real, not a broken CLI.)
The spec-gap framing specifically — *N-version disagreement as a spec-
underspecification detector* — is an open wedge. novelty-b's round-2 searches
(`"n-version programming consensus agent output"` → 0) corroborate the base.

**Honest cost of Head C (so I don't repeat my vercel-labs/ui mistake):**
grouping disagreements into *input classes* ("all empty inputs," "all unicode")
rather than per-input is a small clustering heuristic on top of Head B — real
work, ~30 min, not free, but not load-bearing. If it slips, Head C degrades
gracefully to per-input spec-gap flags, which are still useful.

---

## Final shortlist

**1. BuildOracle — one behavioral-diff engine, three heads (ranked recommend).**
Core = record + classify-then-refuse + canonicalize. Head A (Refactor Gate) is
the mandatory, demoable product and the floor of this build. Head B
(Disagreement Triage) is the reviewer's third eye and supplies Head A's input
set from the union of builds' own inputs. Head C (Spec-Gap Report) is the
ambitious reach — reframes 2-1 disagreements as concrete SPEC.md clauses to add
next cycle, zero new engine, uniquely enabled by our parallel-build pipeline, 0
prior art. **Spec guidance for the reviewer:** mandate in SPEC.md a single CLI
entrypoint `run(input_json) -> output_json`, JSON-schema'd stdout, and pinned
output formatting (float precision, key order, newline discipline) so only
semantic diffs survive — three lines that kill most false-positive noise by
construction. A build shipping only Core + Head A is a complete success; B and
C are the ambitious executioner's reach. **Scores: novelty 4, usefulness 5,
feasibility 4.**

**2. StarSieve — the near-zero-risk floor.** novelty-b's pure-Python repo-
authenticity gate, validated against this cycle's own hand-labeled spam set,
~1h. On the slate only as the guaranteed-shippable option if the reviewer wants
one build with no variance. I don't rank it above BuildOracle — it's the
insurance policy, not the ambition. **Scores: novelty 2, usefulness 4,
feasibility 5.**

**Cut (agreed both sides): Idea 1 CanvasForge** (gpucanvas parks nodes off the
a11y tree on the GPU path; on the DOM fallback it's axe-with-extra-steps),
**Idea 3 SpecToSolid** (thin wedge + external binary Rust-toolchain gate that
burns a builder slot on stall).

**My recommendation to the reviewer:** spec **BuildOracle** as the build, with
Core+Head A as the required deliverable and Heads B/C as explicitly-optional
reach so the three-executioner variance stays controlled. Hold StarSieve as the
fallback only if you want zero build risk this cycle. novelty-b and I have
converged — this is a joint recommendation, not a split.
