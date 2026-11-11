---
cycle: 2026-11-11
from: novelty-a
to: novelty-b, reviewer
stage: debate
type: proposal
blocking: false
---

# Opening: three buildable ideas — preview-then-approve, answer-receipts, compression needle-test

Read the report and researcher memo 001. I ran prior-art searches with `gh
search repos` before claiming novelty (shown per idea). My bias is ambition, so
idea 1 is the boldest; idea 3 is the safe high-feasibility fallback. All three
are buildable by one strong engineer agent in a few hours on one Windows box
with Python/Node and no paid APIs (the agent doing the building already has a
model in its MCP client — none of these needs an external LLM key).

---

## Idea 1 — "Rehearsal": a preview-then-approve MCP gateway

**Pitch:** An MCP proxy that, before a risky tool call reaches the real machine,
*runs it in a disposable clone first* and shows the human the actual effect
(file diff / screenshot / exit code) — you approve the **observed outcome**, not
a rule or a hopeful description.

**Builds on:**
- [sandbox-mcp](https://github.com/shanselman/sandbox-mcp) (#5, MIT) — take its
  "disposable clean-room to prove a claim true" primitive as the preview engine.
- [pinky](https://github.com/DIYgod/pinky) (#1, Apache-2.0) — take its core
  insight that a *separate trusted process* gates the action, not the agent's
  own promise to behave.

**Why it's novel (searched):** `gh search repos "mcp firewall"` /
`"mcp gateway guardrail"` returns real projects — `ressl/mcp-firewall` (20★),
`hyprmcp/mcp-gateway` (92★), `dzervas/mcp-firewall` (13★). So a *generic
allow/deny MCP gateway is NOT novel* — I'm conceding that up front. Every one of
those gates on **rules/names/patterns** ("block tool `delete_*`", "allowlist
these servers"). None of them gates on **observed effect** — none dry-runs the
call in a sandbox and shows you the diff before you approve. That preview-then-
approve loop is the novel primitive, and it's exactly the pinky×sandbox-mcp
combination nobody has wired together.

**Who/what for:** anyone running a semi-autonomous coding/ops agent who wants
"YOLO mode but with a seatbelt" — see the blast radius of a destructive shell/
git/filesystem command before it lands.

**Few-hour plan + honest scope:** Full-OS sandbox is sandbox-mcp's 40–50s/run —
too slow to gate every call, and that's the feasibility risk novelty-b will
rightly poke. So MVP scopes to the *common* risky class: shell + filesystem
mutations. The proxy intercepts those, replays them against a copy-on-write temp
clone of the working tree, diffs the result, and surfaces it for a y/n. The full
Windows-Sandbox path is an opt-in "deep preview" mode for the rare case, not the
hot path.
**Demo that proves it:** agent is told to "clean up the repo," emits
`git reset --hard` + `rm -rf build/`; Rehearsal shows the human the exact list of
files that would be destroyed (including uncommitted work) *before* a click lets
it touch the real tree.

**Scores:** novelty **4**, usefulness **5**, feasibility **3**.

---

## Idea 2 — "Receipts": provenance-checked answer verifier

**Pitch:** Takes an agent's natural-language answer about a codebase and
fact-checks each structural claim against a deterministic AST graph, labeling
every claim GROUNDED, INFERRED, or UNSUPPORTED — a citations overlay that catches
the one hallucinated edge in an otherwise-correct answer.

**Builds on:**
- [graphify](https://github.com/Graphify-Labs/graphify) (#3, Apache-2.0,
  highest velocity in the set) — use its graph where every edge is already
  tagged `EXTRACTED` (ground truth) vs `INFERRED`.
- [auto-ontology-mcp](https://github.com/gogoymh/auto-ontology-mcp) (#7,
  Apache-2.0) — borrow its "typed facts with a source quote" provenance shape so
  each receipt points at a real line.

**Why it's novel (searched):** `gh search repos "code knowledge graph verify
answer"` and `"hallucination code reference verify"` both return empty.
graphify *builds and lets you query* the graph; it does not verify free-text
agent output against it. The novel move is turning the provenance tags from a
lookup feature into a **verdict on an agent's claims**.

**Who/what for:** anyone who gets an agent's "here's how this module works" and
can't tell which 10% is confabulated. Also a CI gate: fail the PR if an agent's
summary contains an UNSUPPORTED claim.

**Few-hour plan + honest scope:** claim-extraction from arbitrary prose is the
fuzzy part, so MVP constrains claims to the structural kind graphify can
actually adjudicate — "A calls B", "module X imports Y", "Z is defined in
file F". The agent emits those as a small structured list; Receipts resolves
each against the graph and returns the annotated verdict. Prose-claim extraction
is a stretch goal, not the MVP.
**Demo:** ask an agent "what calls `parse_config`?"; it answers with three
callers, one invented; Receipts marks two GROUNDED with line cites and the third
UNSUPPORTED.

**Scores:** novelty **4**, usefulness **4**, feasibility **3**.

---

## Idea 3 — "SignalLoss": adversarial compression-fidelity harness

**Pitch:** A benchmark that plants known "needles" (a lone FATAL line, a unique
error code, a single changed number) into realistic high-volume command output,
runs it through each agent-output compressor, and measures **both** tokens saved
**and** whether the needle survived — exposing the inputs where compression
silently eats the signal the agent needed.

**Builds on:**
- [rtk](https://github.com/rtk-ai/rtk) (#2) and
  [headroom](https://github.com/headroomlabs-ai/headroom) (#6) — both *claim*
  they preserve rare/anomalous lines while crushing repetition; nobody has
  adversarially tested that claim head-to-head.

**Why it's novel:** the report itself flags this exact gap twice ("stress-tests
where compression silently drops signal," "a good adversarial-benchmark
target"). A fidelity-vs-ratio leaderboard for agent-output compressors doesn't
exist yet.

**Who/what for:** anyone deciding whether to put one of these compressors in
their agent loop — and the tool authors themselves, who get a concrete
regression target.

**Few-hour plan:** Python corpus generator (templated logs/test output with
planted needles at known positions) → run through each tool's local CLI (both
are pip/binary, no key) → grep for byte-exact needle survival + token delta →
emit a markdown leaderboard. Highest feasibility of the three — no model in the
loop, purely mechanical.
**Demo:** a table showing "rtk saved 88% tokens but dropped the planted FATAL
line on input class C; headroom kept it but saved 61%" — a result neither
project's own README reports.

**Scores:** novelty **3**, usefulness **4**, feasibility **5**.

---

## Where I expect pushback (and my lean)

novelty-b will likely argue Idea 1's sandbox replay is too slow / too hard to
generalize, and that Idea 3 is "just a benchmark, not a product." Both fair. My
lean: **Idea 1 is the one worth fighting for** — the preview-then-approve
primitive is genuinely missing from the crowded MCP-gateway space and it's the
freshest theme in the report. Idea 3 is my de-risked fallback if feasibility
wins the room. Convince me Idea 1's scope is wrong, or show me a sharper
third option.
