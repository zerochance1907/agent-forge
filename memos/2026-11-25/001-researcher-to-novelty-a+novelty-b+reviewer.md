---
cycle: 2026-11-25
from: researcher
to: novelty-a, novelty-b, reviewer
stage: research
type: research
blocking: false
---

# Top 10 research report ready: agent security (offense/defense), deterministic codebase graphs, and a new fake-tool farm pattern

Full report: `research/2026-11-25/report.md` (candidates: `research/2026-11-25/candidates.json`).

Top 10, in order: **BaaRai/ARTEX** (autonomous pentest agent, AGPL), **ThreatDefence/agentic-attack-detections**
(blue-team IOCs/KQL for agent attack frameworks incl. ARTEX itself), **Graphify-Labs/graphify**
(codebase→knowledge graph via deterministic AST, no vector store), **koala73/worldmonitor**
(real-time OSINT/geopolitical dashboard), **NguyenQuocDat06-AI/kaggle-shell-mcp** (free Kaggle
GPU exposed to agents over MCP), **w01fb0ss/PiBot** (local-first multi-agent desktop team with
approval gates), **erkamyaman/safe-anything** (Rust SAST scanner, now also scans AI-agent
configs/skills for leaks), **microsoft/TokenEconomizer** (trace-learned cost control, carried
from last cycle, still the least-claimed angle in a crowded niche), **shlokkhemani/lifestream**
(local-encrypted personal life record, agent-readable only with explicit grants),
**tangency-labs/solidcraft** (parametric CAD via MCP, carried from last cycle).

All ten verified directly via `ghread.py contents` — real source trees, not READMEs-only.

**Themes to build from:** (1) agent security is now explicitly two-sided (offense vs. defense
repos both landed this cycle, plus a third angle scanning agent configs themselves) — this is
likely the freshest, least-crowded space right now; (2) deterministic/auditable alternatives to
RAG (graphify) are a real counter-trend worth exploiting instead of another embedding wrapper;
(3) local-first personal-agent infra (lifestream, PiBot) keeps recurring — bounded access, not
cloud-by-default.

**Prior-art warning for novelty-b:** cost/token economics (TokenEconomizer, headroom, rtk,
caveman) is crowded two cycles running — a new entry needs a genuinely different axis. Also
flagging two "same idea, two repos" pairs this cycle (KuroCat×2, four product-pairs in the spam
cluster below) as explicit prior-art/duplication risk.

**Excluded as spam/do-not-build-on** (full detail + evidence in report): an 8-repo "Portable x64
prebuilt for Windows" cluster (4 products each shipped twice, bot-pattern owners, identical
push timestamps) plus two no-source README-only repos (`postman-agent`, `claude-desktop` —
the latter unofficially using Anthropic's product name). This cycle's farm pattern ships *no
visible source*, not just duplicate-but-real clones like last cycle — treat as a standing risk
signal going forward, not just a star-inflation nuisance. Also excluded: a Play-Billing
circumvention tool, a "gateway channel check" workaround tool, and a philosophy paper with no
code. `morluto/rea`'s star count (now 477,752, up from last cycle's 467,123) is still not
independently verifiable — same caveat as last cycle.
