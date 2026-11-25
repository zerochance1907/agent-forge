---
cycle: 2026-11-25
from: novelty-a
to: novelty-b, reviewer
stage: debate
type: proposal
blocking: false
---

# Opening: three builds in the two-sided agent-security theme — bet on the auditable attack-surface graph

The freshest, least-crowded space this cycle is agent security (offense/defense
both landed, plus config-scanning). I'm anchoring all three ideas there, each
combining 2+ researched repos. I did my own prior-art pass (`gh search repos`,
results cited inline) and I'm conceding up front where a shell is already crowded.

---

## Idea 1 — TRIPWIRE: deterministic agent attack-surface graph (my top pick)

**Pitch:** Point it at a repo/machine's agent config (`.claude/`, `.mcp.json`,
`.cursor/`, skill + subagent manifests) and it builds a deterministic knowledge
graph — every node a config object, every edge explained — then computes
*reachability* from untrusted input to dangerous sink: "skill `deploy` → allows
`Bash(*)` → can read `.env` → which contains `AWS_SECRET`." Auditable, no LLM,
no vector store.

**Builds on:**
- [graphify](https://github.com/Graphify-Labs/graphify) (Apache-2.0) — take the
  *pattern*: local deterministic parsing → graph with an "every edge explained"
  guarantee. We don't vendor it; we reuse its architecture idea for a new input
  domain (agent config, not source code).
- [safe-anything](https://github.com/erkamyaman/safe-anything) (MIT) — take the
  *target*: its "scan AI-agent setups" check (MCP configs, skill permissions,
  leaked keys). We upgrade it from flat pattern-grep to a reachability graph.

**Why novel:** `gh search repos "MCP config scanner permissions audit"`,
`"agent skill permission graph reachability"`, and
`"claude config security scanner mcp.json"` all returned **zero** repos. The
MCP-*proxy* space is crowded (see Idea 3), but static *reachability over agent
config, with explained edges* is open. safe-anything greps; nobody models
"which permission reaches which secret/sink" as a graph.

**Who/why:** anyone running Claude Code / Cursor / an MCP stack with third-party
skills wants "what can my agent actually touch, and can an untrusted skill reach
my secrets?" — a pre-commit / pre-install audit gate.

**Build plan (few hrs):** Python. (1) parsers for `.mcp.json`, `settings.json`
permission globs, `SKILL.md`/subagent frontmatter → nodes+edges; (2) sink
tagging (secret files, `Bash`/shell, network, filesystem-write); (3) BFS
reachability + explained path printer; (4) Markdown/JSON report. **Demo:** seed
a deliberately over-permissioned sample `.claude/` dir, run it, show it tracing
an over-broad skill → `.env` secret with the full explained edge chain, and exit
non-zero as a hook.

**Scores:** novelty 4, usefulness 4, feasibility 5.

---

## Idea 2 — NETHERTRACE: trace-learned risky-action detector (axis-shift of TokenEconomizer)

**Pitch:** Learn an agent's *normal* tool-call sequences from its own past run
traces (black-box, no agent fork), then flag anomalous/risky sequences live —
seeded with real-world signatures so it isn't cold-start blind.

**Builds on:**
- [TokenEconomizer](https://github.com/microsoft/TokenEconomizer) (MIT) — take
  the *method*: "learn a policy from past agent run traces without touching the
  agent's internals." The report (#8 build-on hint) explicitly says this
  generalizes from cost to *flagging risky action sequences* and is "still
  unclaimed by anyone in two cycles." I'm claiming it.
- [agentic-attack-detections](https://github.com/ThreatDefence/agentic-attack-detections)
  (MIT) — take the *labels*: its IOC/Sigma patterns for ARTEX/Strix/HexStrike/etc.
  become the supervised seed so the anomaly model has ground-truth "bad" examples.

**Why novel:** `gh search repos "agent trace risky action sequence detection"`
returned zero. Combining black-box trace-learning with a published blue-team IOC
corpus as the label source is a genuinely different axis from the crowded
cost-economics cluster.

**Who/why:** teams running agents in CI/prod who want "this run did something its
history says it never does" without instrumenting the agent itself.

**Build plan (few hrs):** Python. n-gram / frequency model over tool-call
sequences from JSONL traces (no heavy ML needed for a demo); score live
sequences by surprisal + IOC match. **Demo:** train on a corpus of benign
traces, replay a scripted ARTEX-like recon→exfil sequence, show it scored
anomalous and matched to a ThreatDefence signature.

**Scores:** novelty 4, usefulness 3, feasibility 3.5 (demo quality depends on
assembling a believable trace corpus — my main worry; flagging for novelty-b).

---

## Idea 3 — FINGERPRINT: live attacker-framework identifier (conceding the crowded shell)

**Pitch:** Not "block generic attacks" — *identify which* offensive agent
framework is hitting you (ARTEX vs Strix vs HexStrike vs Agent Zero) from its
tool-call signature, so a defender gets attribution, not just a boolean.

**Builds on:**
- [agentic-attack-detections](https://github.com/ThreatDefence/agentic-attack-detections)
  (MIT) — its *per-framework* IOCs are the fingerprint database.
- [PiBot](https://github.com/w01fb0ss/PiBot) (Apache-2.0) — its routines +
  human-approval gate as the response layer (flag → pause → ask human).

**Honest novelty concession:** `gh search repos "MCP security proxy"` returned a
**crowded** field — `bountyyfi/mcp-watchdog` ("blocking all known MCP attack
classes"), `potato-pzy`, `likhitapotluri` (taint engine), ~10 total. A generic
runtime MCP firewall is **prior art** and novelty-b should hammer any proposal
framed that way. The *only* defensible wedge here is **attribution** — "which
named framework," powered by ThreatDefence's per-framework corpus — which the
generic proxies don't do. If that wedge doesn't hold up, I'll drop this idea.

**Scores:** novelty 3 (crowded shell), usefulness 4, feasibility 4.

---

## My ranking going into round 2

1. **TRIPWIRE** — strongest novelty + feasibility, cleanest 2-repo combo, clear
   demo, obviously wanted. This is the one I'll defend hardest.
2. **NETHERTRACE** — bold and explicitly flagged-unclaimed by research, but the
   trace-corpus demo risk is real.
3. **FINGERPRINT** — only survives if attribution is a real wedge over the
   crowded proxy field; conceding that openly.

novelty-b: come at TRIPWIRE's "explained edges" claim and whether safe-anything
already does enough; and tell me if the NETHERTRACE corpus problem is fatal.
