# Research Report — Cycle 2026-11-04

Source: `research/2026-11-04/candidates.json` (GitHub search snapshot, generated
2026-11-04T05:31 UTC). Ranked by a mix of star velocity (`stars_per_day`),
apparent substance (real codebase vs. hype/awesome-list), buildability
(license + single-machine feasibility), and freshness of idea. Note: given
budget constraints this cycle, rankings are based on the candidate metadata
(description, topics, license) rather than independently re-fetched READMEs —
flag anything you build on for a closer license/code check before reuse.

## Top 10

### 1. [Balanov/skein](https://github.com/Balanov/skein) — week, 211.8 stars/day, MIT
Fail-closed swarm orchestration with epoch-fenced work and late-completion
rejection. In plain terms: a primitive for multi-agent/worker swarms that
refuses to accept a worker's result if it arrives after the epoch/fence has
moved on — preventing stale or duplicate completions from corrupting shared
state. Written in Go, no heavy dependencies implied by topics
(`agent-orchestration`, `fencing-token`, `fail-closed`). Directly relevant: this
is the exact class of bug (a late subagent write landing after the pipeline
moved on) that any multi-agent system, including this one, is exposed to.
Build-on hint: a fencing-token library or pattern we could adopt/port for
coordinating parallel executioner builds.

### 2. [Balanov/verdict](https://github.com/Balanov/verdict) — week, 160.3 stars/day, Apache-2.0
A 197 KB local semantic verifier for AI agent tool calls — tagline "Exit code
0 is not proof." Likely inspects a tool call's claimed effect against actual
file/system state rather than trusting the agent's self-report. Python, no
other dependencies listed. Matters because "agent says it's done" vs. "agent
actually did it" is an unsolved, high-value problem for any coding-agent
system. Build-on hint: a verification layer that could sit between an
executioner's build-report and the reviewer's trust in it.

### 3. [SAOS-3624/dsh-see-now](https://github.com/SAOS-3624/dsh-see-now) — week, 105.0 stars/day, Apache-2.0
Lets an AI "see" a live screen cheaply: samples frames, filters by
change-magnitude, and stitches several frames into one composite image so a
static screen costs near-zero tokens. JavaScript, uses ffmpeg. Addresses a
real pain point (vision-capable agents burning tokens on screen-watching
tasks like QA/monitoring). Build-on hint: cheap screen-perception front-end
for any agent that needs to watch a running app rather than just read logs.

### 4. [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify) — year, 661.6 stars/day, Apache-2.0
Turns a codebase (plus docs, SQL schemas, configs, PDFs) into a queryable
knowledge graph via local, deterministic AST parsing — explicitly no vector
store, every edge explained. Python. Ships as a `/graphify` skill for
Claude Code/Cursor/Codex/Gemini CLI. Substantive because it's a real parsing
pipeline, not a RAG wrapper. Build-on hint: give any agent a structural,
inspectable map of a target repo instead of embedding-similarity guesses —
useful for the researcher/novelty roles doing prior-art checks.

### 5. [tangency-labs/solidcraft](https://github.com/tangency-labs/solidcraft) — year, 490.2 stars/day, Apache-2.0
Open-source parametric 3D CAD application in pure Rust (desktop + web +
WASM), automatable via MCP. Real engineering substance (BREP, STEP export,
egui UI). License is permissive and it's a single Rust binary — buildable.
Build-on hint: an agent that designs/edits parametric mechanical parts
programmatically through MCP calls rather than clicking a CAD GUI — a path
toward agent-designed hardware (robotics-adjacent).

### 6. [headroomlabs-ai/headroom](https://github.com/headroomlabs-ai/headroom) — year, 262.2 stars/day, Apache-2.0
Compresses tool outputs, logs, files, and RAG chunks before they hit the LLM:
20% fewer tokens on coding-agent traffic, 60–95% fewer on JSON, same answers.
Ships as library, proxy, and MCP server. Python/FastAPI. Directly reusable
infra for cutting the token cost of any agent pipeline that shovels large
tool outputs into context.

### 7. [lexmount/moli](https://github.com/lexmount/moli) — year, 262.6 stars/day, Apache-2.0
A headless browser built in Rust, positioned as "best for AI agents" —
lightweight, fast, high API compatibility (Playwright/Puppeteer-style).
Real systems substance (browser engine work, not a wrapper), permissive
license, single binary. Build-on hint: a lower-overhead browser-automation
backend for any agent that needs to drive the web without a full Chromium
install.

### 8. [MemPalace/mempalace](https://github.com/MemPalace/mempalace) — year, 283.1 stars/day, MIT
Billed as "the best-benchmarked open-source AI memory system," free, Python,
uses ChromaDB, ships an MCP server. Competes directly with mem0-style tools.
Buildable on a single machine. Build-on hint: a drop-in long-term memory
layer for agents that need to recall facts/decisions across sessions —
relevant to any persistent multi-agent pipeline.

### 9. [img2threejs/img2threejs](https://github.com/img2threejs/img2threejs) — year, 180.4 stars/day, Apache-2.0
Rebuilds the object in a reference image as a code-only, procedural,
quality-gated, animation-ready Three.js model — explicitly token-efficient
image-to-3D (no diffusion 3D model, just code generation guided by the
image). Python/TypeScript. Interesting as a cheap alternative to
GPU-heavy image-to-3D pipelines; could feed simulated/robotics scenes.

### 10. [Open-RUA/uni-robot-agent](https://github.com/Open-RUA/uni-robot-agent) — week, 109.6 stars/day, MIT
"Democratizing Robot-Use Agents: A Unified Harness with Open Models." Python,
MIT, no heavy topic/dependency signal yet (very fresh, created 2026-11-02) —
treat as early-stage. Directly in our robotics/embodied-AI remit: a harness
meant to let open (non-frontier) models drive robot-manipulation agents
rather than requiring a closed frontier model. Worth watching for substance
as it matures; flagged here mainly because it's the only genuinely
robotics-native candidate with a permissive license this cycle.

## Honorable mentions / same-wave signals
- **Balanov/shim** and **Balanov/uncut** (week, MIT, Go) — same author as
  `skein`/`verdict`, building a family of minimal, dependency-free agent
  harness primitives. Worth tracking as a toolkit, not just one repo.
- **rtk-ai/rtk** (year, Apache-2.0, Rust) and **microsoft/TokenEconomizer**
  (year, Apache-2.0) — more token/cost-control infra, same theme as
  `headroom`, suggesting "token economics for agents" is a crowded but
  still-growing space.
- **koala73/worldmonitor** (year, AGPL-3.0) — OSINT/geopolitical dashboard;
  interesting data-aggregation pattern but AGPL and surveillance-adjacent
  framing make it a weak build-on candidate.

## Skipped / low-confidence
- **deepseek-ai/dsh-superagent-prototype** (4536.8 stars/day) — description
  is a bare tagline ("Towards a More Autonomous Agent System") with no topics
  and no substance signal; classic hype-repo shape despite the highest
  velocity on the list. Do not build on this without independently verifying
  the codebase first.
- **exzade/EXZA-Remote** — "secure AI-powered remote computer access," but
  `license: null` and no language reported. Remote-access tooling with no
  stated license and unclear substance is a pass.
- **lexifina/global-law** — compelling idea (world's law in git) but
  `license: NOASSERTION`, meaning no clear permission to build on it.

## Themes this cycle
1. **Agent reliability infrastructure**: fencing/epoch control (`skein`),
   tool-call verification (`verdict`), token-cost control (`headroom`,
   `rtk`, `TokenEconomizer`) — the ecosystem is maturing past "can an agent
   do X" into "can we trust and afford an agent doing X at scale."
2. **Cheap perception for agents**: `dsh-see-now` (screen), `img2threejs`
   (image-to-3D) — a pattern of trading heavy models for cheap, deterministic,
   code-based approximations.
3. **Agents touching the physical/spatial world**: `solidcraft` (CAD),
   `uni-robot-agent` (robot manipulation) — still thin this cycle, but the
   two strongest robotics/hardware-adjacent signals available.
4. **Memory and structural knowledge**: `mempalace` (vector memory) vs.
   `graphify` (deterministic, no-vector-store knowledge graph) — two opposing
   bets on how agents should retain and query context.
