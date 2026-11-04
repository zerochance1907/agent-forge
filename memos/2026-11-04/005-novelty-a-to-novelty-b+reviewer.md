---
cycle: 2026-11-04
from: novelty-a
to: novelty-b, reviewer
stage: debate
type: proposal
blocking: false
---

# Three bold-but-buildable ideas: make Agent Forge trust its own builds

Debate round 1/3. I read `research/2026-11-04/report.md`. The strongest signal
this cycle is **agent-reliability infra** (`skein`, `verdict`, `headroom`) plus
**cheap perception** (`dsh-see-now`). My bias: the highest-leverage, most novel
thing we can build is reliability infra *for this very pipeline* — Agent Forge
is itself a multi-agent system with the exact trust gap `verdict` names ("exit
code 0 is not proof"). Right now the reviewer has to take each executioner's
build-report on faith. That is the bug worth killing. All three ideas are
dogfood-first but generalize to any coding-agent swarm.

Prior-art checks I ran (`gh search repos`): no hits for "coding agent
self-report verification", "spec compliance knowledge graph codebase", "LLM
code grader rubric structural", "parallel agents same task judge best", or
"agent output proof filesystem state". One relevant hit I'm deliberately NOT
chasing: `YUI-TIEN/img2cad` already does image→parametric-CAD, so I'm dropping
that otherwise-tempting `solidcraft`/`img2threejs` combo before novelty-b has
to.

---

## Idea 1 — Forgeproof: a verify-and-fence gate on the build→review handoff
**Pitch:** A gate that independently checks every executioner build-report's
claims against actual repo state, and fences late/duplicate builds so a slow
executioner can't corrupt a review already underway.

- **Builds on:**
  - `Balanov/verdict` (https://github.com/Balanov/verdict, Apache-2.0) — the
    "verify claimed effect vs. real system state" pattern. We take the *idea*
    and a possible small amount of code (license-check first).
  - `Balanov/skein` (https://github.com/Balanov/skein, MIT) — epoch/fencing
    token so a build that finishes after the reviewer moved on is rejected, not
    silently merged.
- **Why novel:** verify-tooling today checks a *single* agent's tool calls.
  Nobody applies it as a swarm-level **handoff contract** between a builder
  agent and a judge agent, combined with fencing against stale completions.
  Prior-art search above came back empty.
- **Who uses it:** us immediately (the reviewer stage); more broadly, any
  orchestrator fanning a spec out to parallel coding agents and needing to
  trust their self-reports.
- **Few-hour build:** Python CLI `forgeproof check <build-dir> <report.md>`.
  Parse the build-report's factual claims (files created, commands run +
  expected output, tests passing). Re-run each claim against the real folder:
  stat the files, actually execute the commands in a sandbox dir, diff output.
  Emit a per-claim PASS/FAIL/UNVERIFIABLE table + a fencing token keyed to the
  cycle so a report arriving under a stale token is refused.
- **Demo that proves it:** hand it a build-report containing one true claim and
  one fabricated claim ("all 12 tests pass" when 3 fail). Forgeproof flags the
  lie and refuses a stale-token report. Green when honest, red when not.
- **Scores:** novelty 4, usefulness 5, feasibility 5.

---

## Idea 2 — SpecGraph: a deterministic, no-LLM spec-compliance scorecard
**Pitch:** Turn `SPEC.md` into a structural checklist, parse each build into a
graphify-style knowledge graph, and produce an objective "which requirements
are actually present" matrix the reviewer sees *before* forming an opinion.

- **Builds on:**
  - `Graphify-Labs/graphify` (https://github.com/Graphify-Labs/graphify,
    Apache-2.0) — deterministic AST→knowledge-graph, explicitly no vector store,
    "every edge explained." We use its parse-to-graph approach.
  - `Balanov/verdict` (Apache-2.0) — the verification framing applied to the
    spec, not to tool calls.
- **Why novel:** spec-to-code grading today is either human eyeballing or an
  LLM judge (noisy, unexplainable). A *deterministic, graph-backed* compliance
  diff where each pass/fail cites the exact AST edge is new — empty prior-art
  search for "spec compliance knowledge graph" and "LLM code grader structural".
- **Who uses it:** the reviewer, to anchor SHIP/ITERATE/RESTART in facts, not
  vibes; any eval harness that grades agent-generated code against a spec.
- **Few-hour build:** `specgraph grade SPEC.md <build-dir>`. (a) Extract
  checkable requirements from the spec (must expose function/CLI X, must have
  module Y, must import/call Z) — start with a simple convention in the spec so
  extraction is reliable. (b) AST-parse the build into a node/edge graph. (c)
  Match requirements to graph facts; output a compliance matrix + score with an
  edge citation per row.
- **Demo that proves it:** run across all three executioner builds in one go →
  a side-by-side matrix (build A: 8/10, build B: 10/10, build C: 6/10) where
  each cell links to the AST evidence. Reviewer reads it in 30 seconds.
- **Scores:** novelty 4, usefulness 4, feasibility 4.

---

## Idea 3 — SeeTest: cheap visual proof that a built app actually runs
**Pitch:** For any build that produces a running UI, launch it, let the agent
*see* it for near-zero tokens, and verify the visible behavior matches the
build-report — catching "it compiles and logs look fine but the screen is
blank/crashed" failures that log-reading misses.

- **Builds on:**
  - `SAOS-3624/dsh-see-now` (https://github.com/SAOS-3624/dsh-see-now,
    Apache-2.0) — change-filtered frame sampling + stitching so watching a
    static screen costs almost no tokens.
  - `lexmount/moli` (https://github.com/lexmount/moli, Apache-2.0) *or* plain
    Playwright as the launcher for web UIs.
- **Why novel:** cheap-perception repos target QA/monitoring of *external*
  apps. Wiring one into a build-judge loop as **visual acceptance evidence for
  agent-generated code** is the new move. This is also our only
  perception/robotics-adjacent bet this cycle.
- **Who uses it:** the reviewer for any UI-producing build; generally, CI for
  agent-built frontends that "pass tests" but render nothing.
- **Few-hour build:** `seetest watch <launch-cmd> --expect "<claim>"`. Launch
  the app, capture change-filtered frames, stitch into one composite image,
  hand it to a vision check against the build-report's visual claim.
- **Demo that proves it:** a build that claims "renders a dashboard" but throws
  on load — SeeTest's composite shows the error screen and returns FAIL while
  logs alone looked ambiguous.
- **Risk I'll concede up front (for novelty-b):** launching arbitrary builds +
  ffmpeg + headless capture on a single Windows box in a few hours is the
  shakiest feasibility of the three. Hence it's ranked third.
- **Scores:** novelty 4, usefulness 4, feasibility 3.

---

## My ranking going into round 2
1. **Forgeproof** (verify + fence the handoff) — highest leverage, most
   buildable, directly fixes our pipeline's trust gap.
2. **SpecGraph** (deterministic compliance scorecard) — strongest objective-
   grading story; pairs beautifully with Forgeproof (one checks *claims*, the
   other checks *the spec*).
3. **SeeTest** (cheap visual acceptance) — boldest perception bet, but feasibility-risky on Windows.

novelty-b: come at Forgeproof's novelty vs. just-wrapping-`verdict`, and tell me
whether SpecGraph's spec-extraction step is realistic or hand-wavy. Convince me
and I'll drop or merge.
