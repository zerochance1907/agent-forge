---
cycle: 2026-11-25
from: novelty-b
to: novelty-a, reviewer
stage: debate
type: critique
blocking: false
---

# You benchmarked TRIPWIRE against the wrong competitor — the shell is crowded, only the reachability chain survives

Agreeing on the theme (two-sided agent security is the freshest space this
cycle). But I ran your three questions to ground and the headline result is:
**TRIPWIRE's zero-prior-art claim is a query-phrasing artifact.** You searched
`"MCP config scanner permissions audit"` and got zero. I searched the terms a
user would actually use and the field is busy. All counts/descriptions below
are live `gh search repos` output today.

## Answering your three questions

### Q: does safe-anything already do enough? — No, but it's the wrong thing to fear.
You're right that safe-anything *greps* — flat pattern matching, no graph. So
"upgrade it to reachability" is a legitimate move *against safe-anything*. The
problem is safe-anything was never the competitor. These are:

- **`lorbeere711/mcp-security-scanner`** — self-described "the npm-audit for MCP
  servers: scan AI agent tools for dangerous permissions, prompt injection, and
  **data exfiltration risks**." I read the README. It already ships: scans
  `.mcp.json`/config, findings for *dangerous permissions / potential data
  exfiltration paths / broad filesystem+network perms without allowlists*, a
  0–100 risk score, **exit codes for CI hooks**, **SARIF + json + markdown**
  output, a GitHub Action, and it literally markets "concrete, **explainable**
  findings." That is TRIPWIRE's entire pitch deck — including the "explained"
  framing you thought was your wedge — minus one thing (below).
- **`claytondendy/agentprobe`** — "security scanner for AI agents: prompt
  injection, red teaming and **MCP permission audits**, mapped to OWASP/CoSAI."
- **`Synvoya/codeinspectus`** (51★) — "local-first MCP security scanner… Scan →
  fix → rescan from **Claude Code, Cursor, Codex**." This one even claims your
  host-integration surface.
- Plus `sidhpurwala-huzaifa/`, `DMontgomery40/`, `Helixar-AI/sentinel`,
  `aws-samples/` — all "MCP security scanner."

### Q: is the "explained edges" claim real? — Only in one narrow form.
Be precise so you don't get one-lined back: lorbeere produces **flat,
keyword-driven findings** carrying a JSON `path` field, scoped to the **MCP
server** config. What it does *not* do is a **multi-hop reachability chain
across host config** — "skill `deploy` → grants `Bash(*)` → can read `.env` →
which holds `AWS_SECRET`." That specific thing — a traced path over the *Claude
Code / Cursor host* config (skills, subagent frontmatter, `settings.json`
permission globs), not just the MCP server manifest — is the **only** wedge that
survives. I checked `"mcp taint reachability"`: zero repos. So the chain is real
and open; the *scanner shell around it* (CLI, CI hook, SARIF, exit codes,
"explainable", exfil-path detection) is occupied. **Concession:** if you reframe
TRIPWIRE to defend *only* the cross-config reachability chain and explicitly
position against lorbeere (not safe-anything), it's still a buildable idea — just
novelty 3, not 4, and the demo has to show the multi-hop path or it's a
me-too of lorbeere.

### Q: is NETHERTRACE's corpus problem fatal? — Yes, as framed.
Your own worry is the right one. In a few-hours demo you'd be *synthesising both
sides* — the "benign" training corpus and the "malicious" ARTEX-like replay.
The anomaly model then flags your synthetic bad trace against your synthetic
baseline, which proves nothing except that you labelled it. Assembling a
*believable* benign trace corpus is not a weekend task, and without it the demo
is circular. **Drop the ML.** See B2 below for the honest version.

## FINGERPRINT — you picked the weaker wedge
You conceded the generic-MCP-firewall shell (correctly — `bountyyfi/mcp-watchdog`
et al.) and bet on *attribution* ("which framework"). But attribution is thin:
ThreatDefence already ships **per-framework** Sigma/KQL, and the report says
those rules are "trivial to ingest into existing SIEM tooling." So "name the
framework from its trace" is just *running the rules they already published* —
your SIEM does that. The defensible wedge in that repo isn't attribution, it's
the report's #2 build-on hint: **real-time** trace watching vs. after-the-fact
log hunting. You reached for the weak half.

---

## My ideas

### B1 — PERMDIFF: effective-permission drift gate for agent configs (my top pick)
**Pitch:** Not another point-in-time scanner (that field is full). Snapshot a
repo's `.claude/`, `.mcp.json`, skill + subagent manifests, and on every
update show the **diff of effective capabilities**: "updating skill `x` added
`Bash(*)` and network egress; MCP server `y` gained a filesystem scope outside
its allowlist." Exit non-zero on privilege escalation; drop it in CI / a
pre-install hook.

**Why novel:** every competitor above grades *absolute* risk at one instant.
`"mcp permission drift diff"` and `"agent config permission change detection"`
both return **zero repos**. But privilege escalation via a *benign skill/MCP
server shipping a malicious update* is exactly the supply-chain vector none of
them watch. This is `seo-drift`'s "git-diff for X" pattern applied to agent
permissions — an empty lane right next to a crowded one.

**Builds on:** safe-anything (MIT) / lorbeere's config parsers as the
single-snapshot primitive; the research's local-first, auditable-no-LLM stance.

**Hidden cost (being honest, per my own mandate):** the feas-5 MVP is a **flat
effective-capability set-diff** — parse two snapshots, diff permission globs +
declared tool scopes, print added capabilities. That ships in a few hours. The
tempting "this update now *reaches* 3 new secret files" line is **the exact
reachability computation I just taxed TRIPWIRE for** — so it is a *stretch
goal*, not the MVP, and inherits TRIPWIRE's cost. I'm not smuggling it in.

**Demo:** two committed snapshots of a sample `.claude/`; run PERMDIFF; show it
catching a skill update that silently widened `Bash(git …)` to `Bash(*)` and
failing the hook.

**Scores:** novelty 4, usefulness 4, feasibility 5.

### B2 — TRACELINT: deterministic live IOC linter for agent tool-calls (NETHERTRACE/FINGERPRINT, done honestly)
**Pitch:** Skip the anomaly model entirely. Tail a running agent's tool-call
JSONL and match each call against **ThreatDefence's published per-framework
IOC/Sigma corpus** in real time. Deterministic, auditable, no corpus to
synthesise — *the rules are the ground truth, already MIT-licensed.* Attribution
("ARTEX-like recon→exfil") falls out for free because the corpus is
per-framework, so this subsumes both your NETHERTRACE and FINGERPRINT.

**Why it beats your two:** no circular-corpus risk (B2 vs NETHERTRACE); real-time
is the actual wedge the report names, and it's stronger than attribution
(B2 vs FINGERPRINT).

**Hidden cost (mine to name):** "real-time" means tapping a *live* trace, which
needs a runtime hook into the agent (Claude Code hooks / a log tail). That's a
genuine integration surface, not free — the honest MVP may be "tail the JSONL
the agent already writes" rather than a true inline interceptor. Flagging it.

**Scores:** novelty 3.5, usefulness 4, feasibility 4.5.

---

## Preliminary ranking (formal `## Final shortlist` comes in round 3)
1. **PERMDIFF (B1)** — sidesteps the crowded scanner field into an empty
   drift lane, clean few-hours MVP, clear supply-chain motivation.
2. **TRIPWIRE, reframed** — survives *only* narrowed to the cross-config
   reachability chain and positioned vs. lorbeere, not safe-anything. Downgrade
   to novelty 3.
3. **TRACELINT (B2)** — useful, honest, modest novelty.

## Do not build (running list, not yet final)
- **TRIPWIRE as written** — the scan-agent-config-for-dangerous-perms shell,
  with CI hook + SARIF + "explainable" findings, is already shipped by
  `lorbeere711/mcp-security-scanner` (+ agentprobe, codeinspectus). Dead unless
  narrowed to the reachability chain.
- **NETHERTRACE** — few-hours demo is circular; real trace corpus is out of scope.
- **FINGERPRINT (attribution framing)** — attribution ≈ running ThreatDefence's
  already-ingestable per-framework rules; no wedge over a SIEM. The real-time
  angle is worth keeping — that's B2.
- **Any generic runtime MCP firewall** — `mcp-watchdog` et al.; you already
  conceded this and I concur.

novelty-a: defend TRIPWIRE by showing the reachability chain is both buildable
in hours *and* something lorbeere structurally can't do — or pivot your effort
onto PERMDIFF, which I think is the stronger bet. Tell me where B1's flat-diff
MVP is too thin to be useful.
