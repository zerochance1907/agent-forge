# Research report — cycle 2026-11-25

`candidates.json` (generated 2026-11-25T10:22Z). No reviewer memo exists yet
this cycle (first stage), so no RESTART guidance to follow.

Mix: 5 from `week`, 5 from `year`. As with last cycle, the raw `week` list
is heavily polluted — see **Excluded as coordinated spam** below before
trusting any `stars_per_day` figure from an unfamiliar owner.

## Top 10

### 1. [BaaRai/ARTEX](https://github.com/BaaRai/ARTEX) — year
**What it does:** Self-hosted, model-agnostic autonomous penetration-testing
system — "Actively maintained... Community continuation of Autumn-27/ARTEX."
Verified real Go codebase: `agent/`, `guard/`, `hardening/`, `intercept/`,
`llmpool/`, `mcphttp/`, `sidequestion/`, `skills/`, full docker-compose
stack, `SECURITY.md`, `RSI.md`. Evidence-backed findings, not just a scanner.
**Why it matters:** offensive agent tooling keeps maturing into production-
grade infra (Docker, MCP server, LLM pooling) rather than one-off scripts.
**License:** AGPL-3.0 — copyleft; a derivative build must stay open or avoid
distributing modified code as a service without complying.
**Run locally:** `docker-compose up`, needs an LLM API key or local model;
moderate setup.
**Build-on hint:** `llmpool`/`llmrec` (routing pentest tasks across multiple
LLMs with recommendation logic) could be stripped out as a standalone
"best model for this security subtask" router, decoupled from the full
pentest harness.

### 2. [ThreatDefence/agentic-attack-detections](https://github.com/ThreatDefence/agentic-attack-detections) — week
**What it does:** Detection rules and IOCs specifically for AI-agent attack
frameworks (ARTEX, Cairn, PentAGI, HexStrike, Strix, Agent Zero, and more) —
KQL hunts for Sentinel/Defender XDR, plus Sigma, Suricata, Zeek, YARA,
Splunk, Elastic, STIX 2.1 formats.
**Why it matters:** the direct blue-team counterpart to #1 — as offensive
agent frameworks multiply, someone has to ship detections for them, and
this is the first repo in two cycles of scouting doing that systematically
rather than generically.
**License:** MIT. **Run locally:** rule files only, trivial to ingest into
existing SIEM tooling — no agent runtime needed.
**Build-on hint:** a thin wrapper that watches a live agent's tool-call
trace and flags it against these IOC patterns in real time (rather than
log-file hunting after the fact) would be a natural, scoped extension.

### 3. [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify) — year
**What it does:** Turns a codebase (plus its docs, SQL schemas, configs,
PDFs) into a queryable knowledge graph via **local deterministic AST
parsing** — explicitly no vector store, every edge explained. Ships as a
`/graphify` skill for Claude Code, Cursor, Codex, Gemini CLI. Verified real
Python project: `graphify/` package, `ARCHITECTURE.md`, `BENCHMARKS.md`,
full pre-commit/CI hygiene, `gemini-extension.json`.
**Why it matters:** most "codebase understanding" tools lean on embeddings
+ vector search (lossy, hard to audit); this is a credible deterministic
alternative with an explained-edges guarantee, which is a real differentiator.
**License:** Apache-2.0. **Run locally:** `uv`-managed Python package,
straightforward, no GPU or vector DB dependency.
**Build-on hint:** the "every edge explained" property is the interesting
surface — a review/audit skill that cites graphify edges as evidence for a
refactor or dependency-risk claim would exploit that directly.

### 4. [koala73/worldmonitor](https://github.com/koala73/worldmonitor) — year
**What it does:** Real-time global intelligence dashboard — AI-powered news
aggregation, geopolitical monitoring and infrastructure tracking in one
situational-awareness UI. Topics include `gemini-cli-extension`, `mcp`,
`osint`, `palantir`.
**Why it matters:** a genuine end-user-facing multi-source monitoring agent
(not dev tooling), and the only OSINT/situational-awareness entry this
cycle with real engagement (91k stars claimed, 284/day) and an active push
today.
**License:** AGPL-3.0 — copyleft, same caveat as ARTEX for any hosted
derivative. **Run locally:** TypeScript app, likely needs several data-
source API keys; moderate-to-heavy setup given scope.
**Build-on hint:** a narrower single-domain monitor (e.g. one industry's
infrastructure/outage tracking) using the same aggregation pattern would be
a much smaller, demoable slice than the full "world" scope.

### 5. [NguyenQuocDat06-AI/kaggle-shell-mcp](https://github.com/NguyenQuocDat06-AI/kaggle-shell-mcp) — week
**What it does:** Turns Kaggle's free 12-hour dual-T4 GPU notebooks into
live remote terminals and detached job runners for AI agents, exposed over
MCP. Verified real Python package: `src/`, `tests/`, `docs/`,
`ARCHITECTURE.md`, `SECURITY.md`, `pyproject.toml`.
**Why it matters:** a concrete, low-cost answer to "agents need GPU compute
but I don't want to pay for it" — turns a free quota into an MCP-addressable
resource, which is a reusable pattern beyond Kaggle specifically.
**License:** MIT. **Run locally:** needs a Kaggle account/token; otherwise a
normal Python MCP server, light.
**Build-on hint:** the detached-job-runner abstraction (submit now, poll/
reconnect later) is the generalizable part — could be retargeted at other
free-tier compute sources (Colab, HF Spaces) behind the same MCP interface.

### 6. [w01fb0ss/PiBot](https://github.com/w01fb0ss/PiBot) — week
**What it does:** Local-first AI agent *team* for the desktop — multi-agent
group chats, computer use, browser control, MCP, routines and human
approvals, cross-platform (macOS/Windows/Linux/Android). Built on "pi".
Verified real pnpm monorepo: `apps/`, `packages/`, `sdk/`, `design/`,
`patches/`, i18n READMEs (en/ja/zh-CN), full test setup.
**Why it matters:** most personal-agent projects are single-agent chat UIs;
this frames the desktop assistant as a *team* of agents with an approval
gate, which is a more realistic shape for anything that takes real actions.
**License:** Apache-2.0. **Run locally:** pnpm workspace, Electron app,
straightforward dev setup, no cloud dependency required (local-first).
**Build-on hint:** the "routines and approvals" layer (gating what an agent
team can do unsupervised) is the reusable piece — could be extracted as a
standalone approval-gate middleware usable by other multi-agent stacks.

### 7. [erkamyaman/safe-anything](https://github.com/erkamyaman/safe-anything) — week
**What it does:** 100% Rust vulnerability scanner — XSS, SQLi, leaked
secrets, dependency CVEs, and AI-agent-setup misconfigurations. Verified
real repo with CMake/Cargo structure and `banner.svg`-style README, but
genuine `src/`/`include`-equivalent Rust layout (not a binary-only drop).
Same author (`erkamyaman`) shipped `rust-anything` in last cycle's report —
a credible, prolific tool-builder, not a one-off.
**Why it matters:** "scan AI agent setups" (MCP configs, skill permissions,
leaked keys in agent config files) is a narrower, more current framing of
SAST than generic app scanning, and nobody else in two cycles of scouting
has targeted that specifically.
**License:** MIT. **Run locally:** single Rust binary via Cargo, trivial.
**Build-on hint:** the "AI agent setup" check (scanning `.claude`, `.mcp.json`,
skill manifests for overly broad permissions or embedded secrets) is the
freshest piece — a standalone pre-commit hook for agent-config hygiene could
be carved out of just that subsystem.

### 8. [microsoft/TokenEconomizer](https://github.com/microsoft/TokenEconomizer) — year
**What it does:** "Experience-Driven Black-Box Cost Control for Coding
Agents" — learns a cost-control policy from past agent run traces without
touching the agent's internals. Real Microsoft repo (continuing from last
cycle's report, still active: pushed today).
**Why it matters:** cost/token economics for agents remains one of the
most crowded themes two cycles running (`headroom`, `rtk-ai/rtk`,
`JuliusBrussee/caveman` also present in this cycle's raw data) — anything
new here needs a genuinely different axis, and TokenEconomizer's "learn
from traces, don't fork the agent" framing is still the most portable one.
**License:** MIT. **Run locally:** Python package + a target agent's logs,
moderate.
**Build-on hint:** per last cycle's note, the black-box trace-learning
approach generalizes to axes other than cost (e.g. flagging *risky* action
sequences from traces) — still unclaimed by anyone in two cycles of data.

### 9. [shlokkhemani/lifestream](https://github.com/shlokkhemani/lifestream)  — week
**What it does:** A continuously updated, locally encrypted record of a
person's life (messages, mail, photos, places, health, screen time) on
their own Mac, readable only by agents the owner explicitly chooses.
Small (25 stars) but real TypeScript project, local-first, privacy-framed,
Apache-2.0.
**Why it matters:** "give an agent *bounded, owned* access to personal
context" is a sharper and more trust-preserving framing than most
"personal AI assistant" projects, which usually ship data to a cloud
backend by default.
**License:** Apache-2.0. **Run locally:** macOS-only currently, local
encrypted folder, no cloud account needed.
**Build-on hint:** the access-control model (which agent can read which
slice of the life record) is the part worth generalizing — a cross-platform,
narrower version scoped to one data source (e.g. just messages) would be a
realistic weekend build.

### 10. [tangency-labs/solidcraft](https://github.com/tangency-labs/solidcraft) — year
**What it does:** Open-source parametric 3D CAD application in pure Rust —
desktop, web (wasm), and MCP-automatable. Continuing from last cycle's
report; still actively pushed (today), still the only CAD/geometry entry in
either cycle's dataset.
**Why it matters:** CAD remains a domain agents have barely touched because
geometry kernels are hard; this is still the only credible on-ramp.
**License:** MIT/Apache-2.0 dual (separate `LICENSE-BRAND` for marks).
**Run locally:** Rust toolchain, moderate build, no GPU needed.
**Build-on hint:** unchanged from last cycle — an agent skill that takes a
plain-language part description, drives the MCP server to produce a
parametric model, then renders and self-checks dimensions, is still open.

## Honorable mentions (verified real, didn't make the top 10)

- [EL4CTEO/fast-anything](https://github.com/EL4CTEO/fast-anything) — same
  "-anything" line as `shrink-anything` (also this author, also in raw
  data) and (different author) `erkamyaman/rust-anything` from last cycle.
  Profiles a Python/Node/Ruby app and ports just the hot 5% to Rust via FFI.
  MIT, huge momentum (987/day) but mostly prior art relative to last cycle's
  pick — flagging for novelty-b rather than ranking.
- [Johnson-Durui/ApexCluster](https://github.com/Johnson-Durui/ApexCluster) —
  cross-vendor multi-agent cluster where an architecture layer outputs PRDs
  and prototypes for a separate implementation layer to build against,
  Docker-sandboxed. Real TypeScript repo, MIT. Worth a look if novelty wants
  a "PM-agent hands off to builder-agent" angle.
- [AI4XE/ai4ai](https://github.com/AI4XE/ai4ai) — cross-harness kit for
  letting an agent manage its own runtime status, context renewal and
  self-duplication. Thin but real, MIT.

## Excluded as coordinated spam / do-not-build-on

- **The "Portable x64 prebuilt for Windows" cluster** — 8 near-duplicate
  repos, 4 distinct "products" each shipped twice under different owners:
  `TegevoXi39/ccu-tool` + `SodovaFo7/claude-code-unlimited` (same product,
  "rotate Claude Code sessions"), `CajasiZep76/local-ai-chat-uncensored` +
  `TekihiXac52/unfiltered-ai-chat` (same "uncensored local chat"),
  `Karimk899/free-llm-router` + `ThaoYou30020/llm-router-free` (same
  router), `francoisokada/llm-key-pool` + `aSimmons5907/key-pool-rotator`
  (same key-rotation tool). All C++, all created 2026-11-23/24, all
  `pushed_at` within the same ~1-minute window (21:46-21:47 on 11-24), all
  bot-pattern usernames (random-word + digits). Checked `ccu-tool`
  directly: it does have a real `CMakeLists.txt`/`src`/`include` layout
  (not an empty clone, same as last cycle's Gemini-Config-Checker cluster),
  but ships `banner.svg` + `download_btn.svg` — a templated marketing page,
  not an organic repo. Treat the whole cluster's star counts as farmed and
  do not build on the "unlimited"/"free API key rotation" products
  specifically — rotating other people's free-tier keys across many
  providers is the kind of thing that gets accounts banned or breaches ToS.
- **`Lukcla3889/postman-agent` and `bytebuildsmall/claude-desktop`** — both
  `language: null`, both checked directly, and both have the *identical*
  file skeleton: `CHANGELOG.md`, `LICENSE`, `README.md`, `assets/`, `docs/`
  — no source code at all, just a download-button README. Same farm
  template as the cluster above, just without even the C++ stub.
  `claude-desktop` additionally keyword-stuffs `claude-desktop-*` topic
  variants and is an unofficial third-party app using Anthropic's product
  name with a `NOASSERTION` license — do not build on or redistribute.
- **`wc4440222/google-ai-offer-subscription`** — "query and subscribe
  Google AI hidden offers via Play Billing on **rooted** Android emulator."
  This is a billing-circumvention tool, not a buildable idea.
- **`LIUFelix2004/dsh-workbuddy`** — describes "an automatic workaround for
  the gateway 11128 channel check" to import accounts as model providers.
  The explicit framing as a check-bypass is a ToS-circumvention red flag,
  same category as last cycle's "unlimited free frontier models" entry.
- **`morluto/rea`** — same repo flagged last cycle ("claims 467,123 stars");
  now claims 477,752 stars / 2,119.6 stars/day. Growth is internally
  consistent with last cycle's number but the absolute scale (half a
  million stars on a reverse-engineering CLI) still isn't independently
  verifiable from the API alone. Content looks real; treat its engagement
  numbers with the same skepticism as last cycle.
- **`qianyiai/kurocat` vs `chanke17/KuroCat`** — not flagged as fraud (two
  different languages — TS+Tauri vs C++ native — different owners, each
  with real-looking commit activity through today), but it's the same
  product pitch (Bongo-Cat-alternative desktop pet + OBS overlay) shipped
  twice in the same week. Likely parallel independent builds riding the
  same meme rather than a clone farm; flagging for novelty-b's prior-art
  pass regardless.
- **`MoritzPindorek/Five-Laws-of-AI-Agents`** — a philosophy/policy paper
  (Zenodo DOI, zero topics, no real package), not a buildable codebase.

## Themes

1. **Agent security is now explicitly two-sided.** `BaaRai/ARTEX`
   (offense) and `ThreatDefence/agentic-attack-detections` (defense) sit on
   opposite sides of the same arms race this cycle, and `erkamyaman/
   safe-anything` adds a third angle (scanning agent *configs* themselves
   for leaks/misconfig). This is a maturing, legitimately useful space —
   unlike most of last cycle's crowded "context compression" theme.
2. **Deterministic, auditable alternatives to RAG are showing up.**
   `Graphify-Labs/graphify`'s "no vector store, every edge explained" pitch
   is a direct counter-trend to embedding-everything; worth noting if
   novelty wants to avoid yet another RAG wrapper.
3. **Local-first personal-agent infra keeps recurring** — `lifestream`,
   `PiBot`, and (in the raw data) `replit/amuse` all frame the agent as
   something that runs on the user's own machine with bounded, approved
   access, rather than a cloud service with broad defaults.
4. **Free/idle compute scavenging for agents is a small but repeating
   pattern** — `kaggle-shell-mcp` this cycle, plus `sous-labs/songe`
   ("training engine ... using your idle compute") in the raw `week` data.
5. **Fake-tool template farms have gotten more dangerous, not just more
   numerous.** Last cycle's spam was mostly duplicate-but-real clone repos
   inflating star counts. This cycle's "Portable x64 prebuilt" /
   `claude-desktop` / `postman-agent` cluster ships *no visible source*,
   just README + download assets impersonating well-known tools
   (Claude Desktop, Postman, "unlimited" API routers) — a pattern worth
   treating as a standing risk signal (unverifiable binaries, brand
   impersonation), not just a momentum-inflation nuisance, in every future
   cycle's scouting pass.
