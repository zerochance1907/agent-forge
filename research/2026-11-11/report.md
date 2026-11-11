# Research Report — cycle 2026-11-11

Source: `research/2026-11-11/candidates.json` (scout.py, GitHub search API), plus
README verification via `gh api repos/<owner>/<repo>/readme` for every entry below.
Top 10 picked for momentum (stars/day), substance (real working code, not a list
or paper stub), buildability (license + single-machine + clear API/CLI), and
freshness of idea. Mix of `week` (brand new) and `year` (proven, still accelerating).

## Top 10

### 1. [DIYgod/pinky](https://github.com/DIYgod/pinky) — week, 382.4 stars/day
Lets any MCP-capable agent (Claude Code, Claude Desktop, Codex, Cursor) drive a
real iPhone or Android phone, with a human-in-the-loop approval gateway: risky
taps (payments, sends, deletes) pause for your click, banking/password apps are
invisible to the agent, and the agent never sees unlock PINs. Approval is
enforced by Pinky's own gateway process, not by prompting the agent to behave.
Native desktop app (no Electron), ~16-22MB, works over MCP stdio or HTTP.
**License:** Apache-2.0. **Run locally:** download a prebuilt binary (Mac/Win/Linux),
plug in a phone over USB, add to agent's MCP config — no build step. **Author:**
DIYgod (maintainer of RSSHub, a well-known OSS dev) — credible, pre-alpha but
already end-to-end tested on real devices. **Build-on hints:** the
approval-gateway pattern (agent proposes an action, a separate trusted process
gates it before it reaches the real device) generalizes past phones — to any
agent-driven side effect you want audited/intercepted without trusting the
agent's own judgment.

### 2. [rtk-ai/rtk](https://github.com/rtk-ai/rtk) — year, 294.4 stars/day
Rust CLI proxy that transparently compresses the noisy stdout of 100+ common dev
commands (test runners, diffs, logs, builds) before a coding agent reads them —
measured up to 90% fewer tokens, <25ms overhead, zero config. Goes further with
user-authored "pipelines": route specific command output to a cheaper model,
compress non-bash sources, or dedupe. `rtk gain` shows savings per command.
**License:** Apache-2.0 core + BUSL-1.1 for some pro features — check which files
before reusing. **Run locally:** single static binary, `rtk init -g` registers a
shell hook. **Build-on hints:** the "cheap-model-summarizes-before-expensive-
model-reads" pipeline concept is still young (author's own benchmark claims only
20.2% on top of the base compressor) — there's room for a sharper pipeline
pattern or a benchmark that stress-tests where compression silently drops
signal an agent needed.

### 3. [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify) — year, 657.8 stars/day (highest velocity in the set)
`/graphify` skill maps a codebase (plus docs, PDFs, images, video) into a local
knowledge graph via deterministic tree-sitter AST parsing — no embeddings, no
vector store, no LLM call for the code pass. Every edge is tagged `EXTRACTED`
(found directly in source) vs `INFERRED` (resolved by graphify), so an agent
querying it can tell ground truth from inference. Ships a clickable
force-directed `graph.html`. Cloud tier (not needed for local use) adds
cross-repo graphs and formal verification.
**License:** Apache-2.0. **Run locally:** `uv tool install graphifyy && graphify
install`, 30 seconds, Python 3.10+. **Build-on hints:** the EXTRACTED/INFERRED
provenance tagging is the interesting primitive — most RAG/graph tools blur that
line. A build that leans on provenance-tagged graphs for agent-verifiable
reasoning (not just faster lookup) hasn't been done by graphify itself yet.

### 4. [tangency-labs/solidcraft](https://github.com/tangency-labs/solidcraft) — year, 451.1 stars/day
Open-source parametric 3D CAD (sketch → constrain → extrude/fillet/shell →
parametric rebuild on dimension change) written in pure Rust, with desktop, web
(WASM), and an MCP server so agents can model directly — demoed building a
Raspberry Pi case end-to-end from an agent prompt, including engraved text and
material-based mass properties. Real geometry kernel (BREP), not a toy.
**License:** Apache-2.0. **Run locally:** prebuilt installers for
Win/Mac/Linux/Snap, or try in-browser with zero install. **Build-on hints:**
first CAD tool in this batch with a real agent-facing MCP surface — a natural
anchor for anything that needs agents to reason about physical geometry
(manufacturing, enclosures, robotics mechanical design) instead of just code.

### 5. [shanselman/sandbox-mcp](https://github.com/shanselman/sandbox-mcp) — week, 88.7 stars/day
CLI (`sbx`) + optional MCP adapter that automates Windows Sandbox: boot a real,
network-off, disposable Windows 11 VM, deploy an app, drive it with native UI
Automation (not pixel-matching), diagnose missing dependencies (e.g. "fails
because VC++ redistributable isn't installed on a clean machine"), capture
screenshots/recordings/HTML reports, then destroy the guest. ~40-50s per run.
Real measured output pasted in the README (not illustrative).
**License:** MIT. **Run locally:** Windows 10/11 host only (Sandbox feature
required), portable CLI bundles its own Node.js — no separate install.
**Author:** Scott Hanselman (Microsoft) — credible, actively maintained.
**Build-on hints:** "give an agent a disposable clean-room OS to prove a claim
true" is a strong verification primitive — currently scoped to Windows desktop
apps; the same idea applied to e.g. clean-room dependency/installer testing for
other ecosystems is open.

### 6. [headroomlabs-ai/headroom](https://github.com/headroomlabs-ai/headroom) — year, 258.0 stars/day
Library/proxy/MCP server that compresses tool outputs, logs, files and RAG
chunks before they reach the LLM — 21-57% fewer input tokens on four measured
agent scenarios, 90%+ on repeated JSON/log lines, generic prose barely
compresses (reported honestly). Distinct from rtk (#2): operates as a library
you call around any content, not just shell command output, and ships a trained
small model (`kompress-v2-base`) for lossy-but-faithful compression of
structured text, with a specific claim about preserving rare signal (a FATAL
log line surviving byte-for-byte through compression).
**License:** Apache-2.0. **Run locally:** `pip`/`npm` install, works as library,
CLI proxy or MCP server. **Build-on hints:** the "preserve rare/anomalous lines
while crushing repetition" claim is testable and a good adversarial-benchmark
target — build a stress suite of logs with planted rare signals and see where
compression actually drops them.

### 7. [gogoymh/auto-ontology-mcp](https://github.com/gogoymh/auto-ontology-mcp) — week, 68.8 stars/day
MCP server bringing NVIDIA Auto Ontology's semantic layer to any MCP client for
two jobs: (a) text-to-SQL that's checked against a live ontology instead of
guessing at a schema, and (b) a personal knowledge base — feed it receipts,
papers, screenshots, it extracts typed facts + concept links into local SQLite,
with full source/quote provenance, and can export an Obsidian vault. Crucially,
*no LLM API key or hosted model required* — it hands the reading/writing steps
to whatever model is already in your MCP client and keeps only deterministic
work (schema extraction, validation, read-only execution) server-side.
**License:** Apache-2.0. **Run locally:** Python 3.12+, stdio or streamable
HTTP, SQLite — no infra. **Build-on hints:** positions itself explicitly against
Karpathy's "LLM Wiki" gist pattern — a concrete, checkable alternative to
vector-RAG for personal/longitudinal knowledge that's worth probing for where
it breaks (e.g. contradictory sources, schema drift over time).

### 8. [pktq/lasik](https://github.com/pktq/lasik) — week, 57.0 stars/day
Static deobfuscation CLI/MCP server that reverses "BLA" (Blind LLM Agent)
hardening — a code-protection scheme designed specifically to blind coding
agents and reverse-engineering tools. LASIK detects protection *structurally*
(by behavior, not by name/signature), so renamed/rebuilt protected binaries
still get healed; claims 59/63 BLA 3.2.2 shields healed in its own benchmark.
Strips opaque predicates, encrypted strings, decoy code, tamper checks, and
notably *prompt-injection text embedded in the binary aimed at the analyzing
agent itself*. Never executes the input (static only).
**License:** MIT. **Run locally:** npm package (`lasik-agents`), CLI, no
execution sandbox needed since it's purely static. **Legitimate use case:**
malware analysis / security research on adversarial anti-agent code — squarely
defensive. **Build-on hints:** this is a live arms race (BLA hardening vs. LASIK
unhardening) — a natural next move is either a detector for *new* anti-agent
tricks LASIK doesn't cover yet, or benchmarking how reliably an agent's own
judgment gets corrupted by embedded prompt injection before/after healing.

### 9. [lexmount/moli](https://github.com/lexmount/moli) — year, 251.6 stars/day
Headless browser built from scratch in Rust specifically for AI agents browsing
the web — positioned as lighter and faster than wrapping Chromium via
Playwright/Puppeteer, "structure first, pixels on demand" (i.e. returns DOM/
accessibility structure by default, screenshots only when asked).
**License:** Apache-2.0. **Run locally:** single Rust binary, no Chromium
download. **Buildability note:** younger/less documented than the others here
(README doesn't yet show install one-liners in the portion fetched) — worth a
second look at docs/examples before committing to it as a dependency.
**Build-on hints:** if the structure-first claim holds up under test, it's a
meaningfully cheaper substrate for any agent-browsing workload than the
Playwright-wrapping tools everyone defaults to.

### 10. [permitzip/mutinybim](https://github.com/permitzip/mutinybim) — week, 32.8 stars/day
Open-source browser-based BIM (Building Information Modeling) engine designed
for *multiple people and multiple AI agents editing the same building model
concurrently*. One shared kernel (elements, typed units, connected networks,
spaces, phases, sheets, commits) that knows nothing domain-specific, with
versioned trade add-ons (architecture, structural, electrical, plumbing, fire
protection, civil, pro-forma) plugged in on top. IFC 4.3 export, PDF sheets,
coordination lint. Explicitly "early, and honest about it" in its own README.
**License:** Apache-2.0. **Run locally:** Node-based scripting examples
(`npm run example -- rooftop-unit`) runnable standalone or pasted to an agent.
Lowest star velocity in this list, but included deliberately: it's the only
candidate modeling *physical, multi-trade, multi-agent-concurrent-edit* domain
state, which is a genuinely different shape of problem than code/text agents.
**Build-on hints:** the kernel/add-on contract plus concurrent multi-agent
editing of one shared physical model is close to unexplored territory for
agent tooling — most "multi-agent" projects mean multiple LLM roles, not
multiple agents editing the same CAD-like object graph at once.

## Also scanned, not in the top 10 (for context)

- **JosssphZhou/poki** (164.9/day) — same niche as pinky (#1, iPhone agent
  control) but AGPL-3.0, a meaningfully worse license for building on top of.
- **voyager-so/vork** (252.6/day) — headless 3D/VFX/ray-tracing engine for
  agents, high momentum, but license is `NOASSERTION` (effectively
  all-rights-reserved until clarified) — don't build on it as-is.
- **DeusData/codebase-memory-mcp** (186.8/day) and **microsoft/TokenEconomizer**
  (194.4/day) — solid, MIT/Apache, but cover ground close to #2/#3/#6
  (code intelligence graphs, agent cost control) without a sharply distinct
  angle; mentioned in case novelty finders want more comparables for prior art.
- **DIYgod/pinky** vendor note: do not clone upstream BLA/LASIK or Auto Ontology
  repos into anything we ship — check licenses again at build time, this report
  is not a clearance.

## Themes

1. **Token/compute economy for agents** (rtk, headroom, TokenEconomizer) is
   crowded and still accelerating — three strong, well-funded-looking entrants
   this cycle alone. Hard to be first here; differentiation would need a sharp,
   narrow angle (e.g. provable fidelity under compression, not just ratio).
2. **Agent control of physical/real devices with a human-gated approval layer**
   (pinky, poki, sandbox-mcp) is the freshest theme: the interesting primitive
   isn't "agent drives a phone/PC" (that's table stakes now) but the
   *independent trusted gateway* pattern that pinky and sandbox-mcp both use to
   keep the agent from being the sole judge of its own risky actions.
3. **Deterministic, provenance-tagged knowledge structures as an alternative to
   vector RAG** (graphify's EXTRACTED/INFERRED graph, auto-ontology-mcp's typed
   facts with source quotes) is a second-year-running pattern gaining real
   traction — worth building something that leans on *verifiable* agent
   knowledge rather than another embeddings store.
4. **Physical-world / CAD / BIM tooling opening up to agents** (solidcraft,
   mutinybim) is new and thin — only two real entries, both young, both with
   working MCP surfaces. Low competition, high buildability risk (domain
   complexity is real, not just plumbing).
5. **Anti-agent hardening vs. de-hardening (BLA vs. LASIK)** is a narrow but
   genuinely novel adversarial niche: code specifically designed to blind or
   prompt-inject coding agents during reverse-engineering, and a tool built to
   defeat it structurally. Good material for a security-angle build, clearly
   defensive/legitimate (malware/supply-chain analysis), but very niche.
