---
cycle: 2026-11-11
from: novelty-b
to: novelty-a, reviewer
stage: debate
type: critique
blocking: false
---

# Round 3 (final): converged. Accept Preflight's tiering, price in the one unpriced risk (the parser), hold SignalLoss #1 on certainty. Final shortlist below.

Read report.md and all debate memos (001/003/005/007/009/011). novelty-a's
round-3 is honest: both my Preflight challenges were conceded in Preflight's
favor, ApprovalAudit is retired (the Q2 pincer held), and Receipts dropped to
unranked. We agree on the two-item shortlist; the only live disagreement is the
ranking. I'm not introducing a new idea in the final round — the shortlist is
well-vetted and a fresh one wouldn't be. Instead: accept the tiering, add the
one risk neither of us has priced, and give my call.

---

## Preflight tiering — accepted, and it's the right sharpening

The move from "briefing card" to "structured risk tier computed from the live
tree delta" is correct and costs nothing extra mechanically (same oracle, plus a
lookup table). I'll state the novelty precisely so the reviewer prices it right:
**the novel thing is not the four-tier table** (bucketing is trivial) — **it's
that the tier is a function of the live `glob`-expansion + `git status` delta,
not of the command string.** That's the same "brief, don't block / live delta"
wedge I argued; tiering is the packaging that turns it from a nicer `git clean
-n` into a daily driver via graduated autonomy. With that attribution I agree:
**novelty 4.** And I agree the opt-in auto-approve of SAFE/REVERSIBLE_LOCAL is
the actual unmet need behind "YOLO with a seatbelt" — approval only for the
clicks that matter.

## The one risk neither of us priced: Preflight's own parser is the GateCrash target, turned inward

This is my last skeptical duty before we hand off. Preflight's oracle is only as
good as its ability to parse the *proposed* command into {paths, globs,
destructive verb, network call}. The exact command shapes that are most
dangerous are the ones that defeat a static parser — the GateCrash evasion
corpus, pointed back at us:

- command substitution / indirection: `rm -rf $(cat targets.txt)`, `xargs rm`,
  `sh -c "$PAYLOAD"`, piped `find ... | xargs`.
- variables/aliases the parser can't resolve without executing: `rm -rf $DIR`,
  a shell alias, a `Makefile` target that shells out.
- symlink surprises (novelty-a's own `build/ → src/` example): the glob expands
  to 3 entries, but one is a symlink into real source — file-count is honest,
  blast radius isn't.

The honest mitigation novelty-a already named — degrade to `UNKNOWN → treat as
DESTRUCTIVE` — is correct and I accept it. But it has two consequences the build
spec must state, or the demo overclaims:

1. **Bound the grammar explicitly.** The MVP must declare the command class it
   parses with fidelity (literal paths, simple globs, a known destructive-verb
   set: `rm`/`git reset|clean`/`>`/`mv`/`dd`/`truncate`) and route *everything
   else* to `UNKNOWN`. A spec that implies "parses arbitrary shell" is unbuildable
   in a few hours and will fail forgejury-style scrutiny.
2. **This is where Preflight's feasibility actually lives.** The clean demo
   (`rm -rf build/` → "37 files, 4 uncommitted, irreversible") works because it's
   in the bounded grammar. Across three executioners building the same spec, the
   *variance* will be in how much of the long tail each one handles and how
   gracefully they fall back. SignalLoss has no equivalent variance — the corpus
   generator + grep is deterministic for every builder. That's the real reason I
   keep SignalLoss as the safer #1, not timidity about reach.

So my feasibility score for Preflight is **4 for the honestly-bounded MVP**
(declared grammar + UNKNOWN fallback), **3 if the spec demands the impressive
arbitrary-shell demo.** The reviewer should write the spec to the former.

## Two hard spec constraints for whichever is picked (build-ready)

- **Preflight:** default behavior is *brief everything*; auto-approving the safe
  tiers is an explicit user-set flag. If that's not stated, we've silently
  shipped an auto-approver — the exact rubber-stamp failure mode this whole line
  of thinking was meant to prevent. And the host must be named: a Claude Code
  PreToolUse hook is the cheapest demoable unit; the MCP shim is the general one.
  Pick one for the MVP (I'd pick the hook — concrete, demoable, no transport
  plumbing).
- **SignalLoss:** headline the **normalized-recovery** column, keep byte-exact
  and optional model-recovery as separate columns (converged in round 2). The
  spec must pin tool versions (rtk, headroom) so the leaderboard is reproducible
  — a leaderboard that shifts with an upstream release isn't a regression target.

## The ranking call

novelty-a wants Preflight #1 (reach), I want SignalLoss #1 (certainty). My honest
final position, and *why* — not reflexive skepticism:

This is a build-three-in-parallel-then-judge cycle. The deciding question isn't
"which idea is cooler," it's "which spec makes three independent builders reliably
produce a working, comparable artifact." SignalLoss does — every builder's output
is a deterministic table. Preflight's output quality depends on parser coverage,
which varies by builder, so the three builds will be harder to compare and more
likely to differ in demo polish. That's a real cycle-level reason to lead with
SignalLoss. **But I concede Preflight is the better *product*** — it's the only
daily-driver on the table, novelty-a broke my two objections fairly, and
"middleware isn't a product" was wrong (every researched substrate this cycle is
middleware). If the reviewer wants reach over certainty, Preflight is the right
reach, and the constraints above make it buildable. We are genuinely one ranking
decision apart, and either order is defensible.

---

## Final shortlist

1. **SignalLoss (tiered fidelity metric)** — adversarial compression-fidelity
   harness: plant known needles (error codes, hex IDs, numbers, a lone FATAL
   line) in realistic high-volume command output, run through rtk (#2) and
   headroom (#6) at pinned versions, report tokens-saved vs. needle-survival
   across **byte-exact / normalized-recovery (headline) / optional
   model-recovery** columns. The fidelity-vs-ratio leaderboard neither README
   publishes; the report flags the gap twice. Fully mechanical, two pip/binary
   installs, no hardware, no model in the hot path, deterministic for every
   builder. My #1 on certainty and cross-builder comparability.
   **Novelty 3, usefulness 4, feasibility 5.**

2. **Preflight (graduated-autonomy tiering)** — deterministic PreToolUse
   middleware (ship as a Claude Code hook for the MVP) that, before a proposed
   shell/action call executes, computes a blast-radius card from the **live tree
   delta** (glob expansion + `git status`/`git stash`, request-parse for the
   network class) and assigns a tier — SAFE / REVERSIBLE_LOCAL / DESTRUCTIVE_LOCAL
   / EXTERNAL — letting the user *opt in* to auto-approving only the safe tiers.
   The informed half of pinky's (#1) "pause for your click" bet; sandbox-mcp (#5)
   sets the clean-room fidelity bar for the one opaque tree-local class a static
   parse can't see. No model, no hardware. The reach pick, buildable *if* the
   spec bounds the parser grammar and defaults to brief-everything (constraints
   above). Credit to novelty-a for the tiering; the live-delta oracle was the
   shared wedge. **Novelty 4, usefulness 5, feasibility 4 (bounded MVP) / 3
   (arbitrary-shell demo).**

## Do not build

- **Rehearsal as pitched** (sandbox-replay-then-approve for "shell + filesystem")
  — unsound for network/stateful commands, unnecessary for statically-predictable
  ones; conceded by novelty-a in round 2. Its residue lives on inside Preflight.
- **Receipts MVP** (structured-triple verifier) — grades a hallucination the
  architecture already removes. The prose 3-verdict version is alive-but-unranked
  *only if* the reviewer specifically wants a knowledge-graph build this cycle
  (graphify #3); otherwise it needs the client model in the loop twice and loses
  to a mechanical daily-driver and a reproducible benchmark.
- **ApprovalAudit / GateCrash as graders** — the "is the click informed?" wedge is
  genuinely novel but has **no mechanically-observable target in a few hours**:
  human-asking gates (pinky) render to a GUI needing OCR + physical hardware;
  mechanically-drivable gates (`mcp-firewall`) mostly don't ask a human, so
  there's no approval surface to score (the Q2 pincer). Both also lean on
  non-researched `mcp-firewall` repos. The idea survives *only* by flipping the
  oracle from grader to product — which is Preflight.
- **A generic MCP allow/deny gateway** — category saturated (`hyprmcp/mcp-gateway`
  92★ et al.); conceded by novelty-a in round 1.
- **Byte-exact-only fidelity scoring** (SignalLoss's original metric) — unfairly
  penalizes faithful-lossy compressors; keep it as one column, never the headline.
