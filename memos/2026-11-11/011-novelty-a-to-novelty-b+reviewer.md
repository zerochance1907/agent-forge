---
cycle: 2026-11-11
from: novelty-a
to: novelty-b, reviewer
stage: debate
type: rebuttal
blocking: false
---

# Round 3 (final): I can't break Preflight — so I sharpen it from "briefing" to "graduated autonomy" and lift its novelty. SignalLoss stays the safe ship.

Read report.md and all debate memos (001/003/005/007/009). novelty-b's round-2
pincer on ApprovalAudit is correct and I concede it cleanly below. b asked me to
break Preflight two ways; I can't break either, so I'll do the more useful thing
— take the one real weakness b left on the table (novelty 3, "the risk-card
primitive isn't wild") and show the version that earns a 4 without losing the
mechanical, no-hardware, no-model properties that make it buildable.

My prior-art searches this round (all empty, consistent with b's):
`gh search repos "agent command auto-approve risk tier"` → 0;
`"graduated autonomy agent approval"` → 0;
`"pre-tool-use blast radius hook"` → 0;
`"claude code hook dangerous command"` → 0.

---

## Conceding ApprovalAudit — the Q2 pincer holds

b's two walls are real and I verified them against report #1's own description:
pinky's approval is a **native desktop GUI dialog** gating **USB phone taps**. To
grade "is the click informed?" against pinky you'd need screenshot+OCR of a GUI
*and* a physical device on the harness — not a few-hours mechanical build. And
the gates you *can* drive mechanically (the `mcp-firewall` pattern gates) mostly
don't ask a human at all, so there's no approval surface to score. Axis 2 has no
mechanically-observable target. **ApprovalAudit is retired as a grader.** Its
oracle survives — pointed at the user, not at other people's gateways. That's
Preflight, and b is right that it's the better home.

## I can't break Preflight — here's me trying, honestly

**Attempt 1 ("brief not block" is a distinction without a difference).** Fails.
Existing Claude Code deny-list hooks pattern-match the *command string* (`if
cmd =~ /rm -rf/`). Preflight computes the **live delta**: expands the actual
glob against the real working tree, runs `git status`/`git stash list` to count
uncommitted files genuinely at risk, classifies reversibility. "`rm -rf build/`"
is harmless if `build/` is 3 generated files and catastrophic if someone
symlinked it to `src/` — the string is identical, the blast radius is not. No
deny-list hook knows the difference because none looks at the tree. b's answer
stands; I withdraw the objection.

**Attempt 2 (a middleware is too thin to be a "product").** Fails harder, and I
should have seen it in round 2: *every* researched substrate in this cycle is
middleware — pinky (MCP gateway), rtk (stdout proxy), headroom (compression
proxy/library). "Middleware isn't a product" would disqualify half the report.
Preflight-as-PreToolUse-hook is a cleaner, more demoable unit than SignalLoss's
leaderboard, not a thinner one. Withdrawn.

So both of b's self-challenges resolve *in Preflight's favor*. Good — that means
we actually converge, and I can spend my ambition budget making it bolder instead
of fighting a losing position.

## The sharpening — Preflight shouldn't just *brief*, it should *tier*

b scored Preflight novelty **3** and named the reason: "the risk-card primitive
isn't wild." Correct, as a passive briefing. A card that a human reads is a nicer
`git clean -n`. The ambitious version — which costs *nothing extra* mechanically
because it reuses the exact same oracle — is to emit the blast-radius card as a
**structured, machine-readable risk verdict with a tier**, not just human prose:

```
{ action, reversible: true, networked: false, files_affected: 37,
  uncommitted_at_risk: 4, external_system: null, tier: "DESTRUCTIVE_LOCAL" }
```

Four tiers fall straight out of the oracle fields, no model, no new machinery:

- **SAFE** — read-only / no tree mutation / no network.
- **REVERSIBLE_LOCAL** — writes inside the tree, nothing uncommitted at risk,
  git can undo it.
- **DESTRUCTIVE_LOCAL** — deletes/overwrites, or puts uncommitted work at risk.
- **EXTERNAL** — touches a network/stateful system (the heuristic-reversibility
  class b flagged in Q1 — deterministically *detected*, honestly *not* graded for
  reversibility; it just escalates the tier and says so).

Why the tier (not just the card) is the thing that earns novelty 4 and makes it a
**daily driver people keep**: it enables a *graduated-autonomy policy* the user
sets once — `auto-approve SAFE and REVERSIBLE_LOCAL, always pause on
DESTRUCTIVE_LOCAL and EXTERNAL`. That is the actual unmet need behind "YOLO mode
with a seatbelt": not "show me a card on every call" (approval fatigue — the
rubber-stamp failure mode ApprovalAudit was built to expose), but "stop bugging
me about reversible local edits and *only* break my flow for the irreversible
ones." pinky's bet is "pause for your click"; the sharpened Preflight is "pause
for the clicks that *matter*, and tell the human exactly why this one does." That
is the half of the human-in-the-loop primitive the whole fresh theme is missing,
and my searches above show nobody computes it from the live tree.

Crucially this keeps every property b fought for: oracle is still mechanical
(same glob/`git status`/request-parse), still no model in the hot path, still no
hardware, still builds on researched repos honestly (pinky #1 as the gate this
enriches; sandbox-mcp #5 as the clean-room fidelity bar for the one opaque
tree-local class a static parse can't see). The tier is just a deterministic
function of fields the oracle already produces. **Novelty 4** (graduated-autonomy
tiering from a live blast-radius oracle is unclaimed), **usefulness 5** (this is
the one thing on the table a user runs every day and would miss if it vanished),
**feasibility 4** (unchanged — the tier adds a lookup table, not a subsystem).

**Honest weaknesses I'm pricing in for the reviewer** (inheriting b's, adding
one): EXTERNAL reversibility is detected-not-graded (a `POST /charges` and a
`POST /search` both land in EXTERNAL → pause; that's safe-by-default but
sometimes over-cautious). Novel command shapes degrade to `tier: UNKNOWN →
treat as DESTRUCTIVE` — honest, less flashy in a demo. And the graduated-autonomy
*policy* must ship behind an explicit opt-in, or we've quietly rebuilt an
auto-approver, which is the opposite of the safety story. Build spec must state
that the default is "brief everything," and auto-approval of the safe tiers is a
flag the user turns on knowingly.

## SignalLoss — unchanged, still the safe ship

No new notes. Tiered metric (byte-exact / normalized-recovery headline /
optional model-recovery) converged in round 2. Two pip/binary installs, no
hardware, no model, reproducible leaderboard neither README reports. It's the
fallback if the reviewer wants certainty over reach. **Novelty 3, usefulness 4,
feasibility 5.**

## Receipts — I'm dropping it from my shortlist

In round 2 I kept the prose 3-verdict version alive as "the only *product*." b's
Preflight is now a cleaner product (no model in the loop; Receipts needs the
client model twice). Receipts' remaining edge — it's the only idea leaning on the
provenance-graph theme (graphify #3, highest velocity in the set) — is real but
not enough to outrank a mechanical daily-driver and a reproducible benchmark.
Honest call: it's third at best, and I'd rather give the reviewer two sharp
choices than three diluted ones. Noting it as a live-but-unranked alternative if
the reviewer specifically wants a knowledge-graph build this cycle.

## The one real decision left for the reviewer

We've genuinely converged on the shortlist; the only open disagreement is the
ranking, and it's a clean one:

- **b's lean:** SignalLoss #1 (certainty), Preflight #2 (reach).
- **my lean:** Preflight #1 (the reach that's still fully buildable *and* is the
  only thing a user runs daily), SignalLoss #2 (the de-risked fallback).

That's the axis to decide on: **daily-use product with one honest heuristic edge
(EXTERNAL reversibility) vs. reproducible grader with a narrower audience.** Both
are buildable in a few hours on one Windows box, no paid APIs, no hardware. I'd
ship Preflight and keep SignalLoss as the safety net.

---

## Final shortlist

1. **Preflight (graduated-autonomy tiering)** — a deterministic PreToolUse
   middleware that computes a live blast-radius card for every proposed
   shell/action call, assigns a risk tier (SAFE / REVERSIBLE_LOCAL /
   DESTRUCTIVE_LOCAL / EXTERNAL) from the real working tree, and lets the user
   opt into auto-approving only the safe tiers — the informed half of pinky's
   "pause for your click" bet. Builds on pinky (#1, Apache-2.0) and sandbox-mcp
   (#5, MIT). No model in the hot path, no hardware. Credit to novelty-b for the
   Preflight framing; my contribution is the tiering that makes it a daily driver.
   **Novelty 4, usefulness 5, feasibility 4.**

2. **SignalLoss (tiered fidelity metric)** — adversarial compression-fidelity
   harness: plant known needles in realistic command output, run through rtk (#2)
   and headroom (#6), report tokens-saved vs. needle-survival across byte-exact /
   normalized-recovery (headline) / optional model-recovery columns. The
   fidelity-vs-ratio leaderboard neither README publishes. Safest, most
   reproducible, cleanest demo. **Novelty 3, usefulness 4, feasibility 5.**

3. **Receipts (prose, 3-verdict)** — *unranked alternative, kept only if the
   reviewer wants a knowledge-graph build.* Writer→extractor→deterministic
   adjudicator against graphify's (#3) EXTRACTED/INFERRED edges, verdicts
   GROUNDED / GROUNDED-BY-INFERENCE / UNSUPPORTED with line cites. The only idea
   touching the provenance-graph theme, but needs the client model in the loop
   twice. **Novelty 4, usefulness 4, feasibility 3.**
