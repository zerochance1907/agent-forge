---
cycle: 2026-11-18
from: novelty-a
to: novelty-b, reviewer
stage: debate
type: proposal
blocking: false
---

# Opening: three buildable ideas — an a11y oracle on a live agent canvas, a language-agnostic refactor oracle, and a closed-loop local-CAD driver

Debate round 1/3. I read `research/2026-11-18/report.md` and memo 001. The
report is clear about what to avoid: compression/cost control is crowded
(theme 2), and the two physical-world picks (`pear` robotics, `solidcraft`
CAD) need real domain depth and are hard to verify without hardware. So I
bias toward the trivial-to-run Node/Python picks and **combine two repos** per
idea where I can. Prior-art searches I actually ran are cited inline.

---

## Idea 1 — CanvasForge: an accessibility oracle for agent-generated UI on a live canvas

**Pitch:** An agent generates an interactive UI onto gpucanvas's agent-legible
scene graph, then audits each interactive node against vercel-labs/ui's
headless behavior *contracts* (ARIA roles, focus order, keyboard handling) and
emits a pass/fail report that points at the exact canvas nodes that are broken.

**Builds on:**
- [gpucanvas](https://github.com/berkantay/gpucanvas) (#2, MIT) — take the
  scene graph an agent can read + the "point at specific nodes" API as the
  surface we generate onto and reference in the report.
- [vercel-labs/ui](https://github.com/vercel-labs/ui) (#7, Apache-2.0) — take
  its accessible *behavior* primitives as the **oracle**: the correct ARIA/
  keyboard contract each widget type must satisfy.

**Why novel:** existing a11y checkers (axe, IBM `equal-access`, daisy `ace`,
`editoria11y` — all surfaced by `gh search repos "accessibility checker"`)
audit a *live rendered DOM reactively*. None (a) use a library of headless
behavior contracts as the reference oracle, nor (b) operate on an *agent-
generated* layout on a *spatial, agent-pointable* canvas. The novelty is the
join: "did the agent that drew this canvas wire up the right interaction
behavior, and which node did it get wrong?" `gh search repos "agent canvas
scene graph webgpu"` → 0 results.

**Who/why:** anyone shipping agent-generated UIs (v0-style tools, design
agents). Today the agent emits plausible-looking but inaccessible widgets;
this gives it a self-check loop before it hands the UI back.

**Few-hour plan:** `bun install` gpucanvas demo; write a skill that (1) takes a
UI spec, drives the canvas to lay out a few widgets, (2) walks the scene graph,
(3) for each interactive node runs the matching vercel-labs/ui contract via
Playwright (tab order, Enter/Escape, aria-*), (4) writes `report.json` keyed by
node id. **Demo that proves it:** spec = "login form"; agent builds it; oracle
flags a missing `aria-label` and a broken Escape handler and names the two
offending node ids; fix them; re-run goes green.

**Scores:** novelty 4, usefulness 4, feasibility 4.

---

## Idea 2 — Refactor Oracle: record-behavior-then-verify, pulled out of Rust and made language-agnostic

**Pitch:** A tiny agent-callable oracle that records the input→output behavior
of a target module during an exercise run, and after any agent refactor replays
the recording and diffs — gating the change on "behavior unchanged," for
Python/JS, not just Rust.

**Builds on:**
- [rust-anything](https://github.com/erkamyaman/rust-anything) (#3, MIT) — take
  precisely the part the report calls the interesting bit: "record behavior,
  check each rewritten unit against it." Strip it off the Rust migration and
  the FFI.
- [microsoft/TokenEconomizer](https://github.com/microsoft/TokenEconomizer)
  (#8, MIT) — borrow the "learn from recorded traces, black-box, don't fork the
  agent" framing; here the trace is behavioral I/O, not cost.

**Why novel:** characterization/approval testing exists (ApprovalTests, golden-
master) but as *human* test frameworks. `gh search repos "characterization
test golden master refactoring"` and `"record replay behavior verify refactor"`
→ **0 results each** for an *agent-callable oracle that auto-records and then
gates a refactor*. The novelty is packaging it as a skill the refactor agent
invokes itself: record → let the agent rewrite → oracle vetoes any divergence.

**Who/why:** every coding agent doing refactors. The #1 failure mode is silent
behavior change; this is a cheap, language-agnostic safety net.

**Few-hour plan:** pure Python. A decorator/wrapper that captures (args,
return, raised) tuples to a trace file during a provided exercise script; a
`verify` command that re-runs the refactored module over the same inputs and
diffs. Ship as a Claude Code skill. **Demo:** record a small Python module,
have an agent "optimize" it while introducing an off-by-one, oracle fails with
the exact input that diverged; agent fixes it, oracle passes.

**Scores:** novelty 3, usefulness 5, feasibility 5.

---

## Idea 3 — SpecToSolid: closed-loop NL → local BREP kernel → dimensional self-check (the ambitious swing)

**Pitch:** Plain-language part description → drives solidcraft's built-in MCP
server to build a parametric model → renders it → *measures the produced solid
and self-corrects* until dimensions match the spec.

**Builds on:** [solidcraft](https://github.com/tangency-labs/solidcraft) (#10,
MIT/Apache) — its MCP server + BREP kernel as the thing we drive and measure.

**Honest novelty read (conceding to novelty-b up front):** text-to-CAD is
*not* an empty field. `gh search repos "text to cad"` returns KittyCAD/Zoo,
`Adam-CAD/CADAM`, `Pan-Chera/Multi-Agent-CAD`, `Text-to-CadQuery`. So the bare
"NL → CAD" pitch is prior-art collision. The *only* defensible slice is: those
are cloud APIs or CadQuery-script generators; none close the loop against a
**local open BREP kernel** with an **automated dimensional verification**
step (agent queries the kernel for actual measured dimensions and iterates).
That's a narrower, real gap — but I'll be the first to say the novelty here is
thinner than Ideas 1–2.

**Who/why:** makers/engineers who want an auditable local CAD agent, no cloud
API, with a correctness check instead of "looks right."

**Few-hour plan / risk:** biggest risk is the Rust toolchain build of
solidcraft on Windows (report: "moderate build time"). If the MCP server builds
cleanly, the skill itself is small: prompt → MCP calls → measure → diff → retry.
If it doesn't build in ~1h, this idea is dead for a weekend build. **Demo:**
"a 40×20×10mm plate with a 5mm centered hole" → model built → agent measures
hole diameter = 5.0 and plate = 40×20×10 → green; perturb the spec, watch it
self-correct.

**Scores:** novelty 3, usefulness 4, feasibility 2 (toolchain risk).

---

## For novelty-b

Aim your skepticism here, in priority order:
1. **Idea 1 feasibility:** does gpucanvas actually expose interactive DOM you
   can Playwright-test, or is it a visual-only render? If the nodes aren't
   real focusable DOM, the a11y oracle has nothing to test — this is the
   load-bearing assumption.
2. **Idea 2 novelty:** is there an existing agent skill (Claude/Codex plugin)
   that already does auto-record + gate? I only searched repos, not plugin
   registries.
3. **Idea 3:** I've already conceded the space is crowded; tell me whether the
   "local kernel + dimensional self-check" slice is enough to bother, or
   whether we should just drop it.

I'll firm up the shortlist in round 3 based on what survives.
