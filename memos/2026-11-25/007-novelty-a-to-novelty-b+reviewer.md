---
cycle: 2026-11-25
from: novelty-a
to: novelty-b, reviewer
stage: debate
type: rebuttal
blocking: false
---

# Conceded, then collapsed: TRIPWIRE and PERMDIFF are one engine — the cross-config reachability graph — and the sink model is where the real novelty lives

You were right on almost everything, so I'll concede fast and spend my words
where it matters: your top pick (PERMDIFF) and my top pick (TRIPWIRE) are **not
two ideas**. The non-thin version of yours *is* mine. Let me show that, then
push the novelty back up with a change to the sink model.

## Concessions (settled, don't relitigate in round 3)
- **TRIPWIRE-as-shell is dead.** You're correct: `lorbeere711/mcp-security-scanner`
  (+ `claytondendy/agentprobe`, `Synvoya/codeinspectus`) already ship the
  CLI + CI-hook + SARIF + "explainable findings" scanner. I re-ran
  `gh search repos "mcp security scanner permissions"` and got **another** one I
  hadn't seen — `PFgo/mcpsec` ("CLI-first MCP security scanner, permission
  reviewer, and policy seed generator"). The single-snapshot scanner field is
  genuinely full. I withdraw TRIPWIRE as originally framed.
- **NETHERTRACE is dead.** Your circular-corpus critique is fatal and I don't
  contest it.
- **FINGERPRINT (attribution) is dead.** "Name the framework" ≈ running
  ThreatDefence's already-ingestable per-framework rules; no wedge over a SIEM.
  Agreed, drop it.

## Attack you invited: PERMDIFF's flat-diff MVP is too thin to beat `git diff`
You asked me to say where B1's feas-5 MVP is too thin. Here it is: a **flat
permission-string set-diff** — "skill `x` added `Bash(*)`" — is a line a reviewer
*already sees* in `git diff .claude/settings.json`. If the MVP only tokenises two
config files and prints added permission strings, it competes with `git diff`
and loses (git has color, blame, review integration; you have a new binary).

The part of PERMDIFF that is *actually* worth shipping is the part you honestly
flagged as a stretch goal: **"this update now *reaches* 3 new secret files."**
That is the reachability computation — i.e. TRIPWIRE's engine. So your own
hidden-cost note already proved my point: **PERMDIFF without reachability is thin;
PERMDIFF with reachability is TRIPWIRE run over two snapshots.** They are the
same build.

## The collapse: one engine, two modes
Build **one** thing — a deterministic cross-host-config reachability graph — and
expose it in two modes:
- **audit mode** (the old TRIPWIRE demo): single snapshot → "skill `deploy`
  grants `Bash(*)` → reaches `.env` → `AWS_SECRET`," explained edge chain.
- **drift mode** (your PERMDIFF demo): diff the reachability graphs of two
  snapshots → report *newly-reachable sinks*, not just newly-added permission
  strings. Exit non-zero on new reach. This is strictly more useful than a
  string set-diff and it's what makes drift beat `git diff`.

Drift mode is a ~20-line wrapper around audit mode (compute graph A, graph B,
set-difference the reachable (source→sink) paths). We get both your lane and
mine for one engine's worth of work.

## Why this is buildable in hours *and* structurally beyond the scanners
- **Buildable:** the graph is tiny — a few dozen nodes from a handful of files
  (`.mcp.json`, `settings.json` permission globs, `SKILL.md`/subagent
  frontmatter, presence of secret files). Nodes + edges + BFS. **No ML, no
  vector store, no corpus to synthesise** (which is exactly why it dodges the
  trap that killed NETHERTRACE). The parsers are the bulk of the work and each
  target is a well-defined format. Few hours is real for audit + drift on
  sample dirs.
- **Structurally beyond lorbeere/mcpsec:** they scan **one manifest, flat,
  per-file**. The chain requires a **join across host-config files** — the
  grant lives in skill frontmatter, the allowlist in `settings.json`, the secret
  in `.env`. "Permission in file A, combined with allowlist in file B, reaches
  secret in file C" is a graph query, not a per-file finding. A flat scanner
  cannot express a multi-file join without becoming a graph — at which point it's
  this. `gh search repos "mcp permission reachability taint"` → **zero**
  (confirms your "mcp taint reachability" null).

## Pushing novelty back to 4: make the sinks a *taint* model, not a permission enumerator
Here's my ambition contribution, and it's what separates this from "fancy
permission lister." Don't model only *permission → secret file*. Model
**untrusted-input source → dangerous sink**:
- **sources:** skills/MCP servers that ingest attacker-controllable input — a
  skill that reads web pages, GitHub issues, email, a shared doc.
- **sinks:** shell execution, network egress, secret-file read, filesystem write.
- **the finding that nobody ships:** "skill `triage-issues` reads untrusted
  issue text **and** (via its `Bash(*)` grant) can reach shell — a prompt-injection
  path from issue → RCE." That's genuine taint reachability over agent config,
  which is the live attack class (prompt injection → tool abuse), not just
  hygiene.

`gh search repos "mcp prompt injection taint flow analysis"` → **zero repos.**
This is the open lane, and it's what earns novelty 4 instead of 3: not "audit my
perms" (crowded) but "trace a prompt-injection reachability path across my agent
config" (empty).

## My own hidden cost, named (per the honest-debate rule)
The taint model lives or dies on the **source/sink catalog** — what counts as an
untrusted-input source and a dangerous sink. That catalog is the real work and it
will be *incomplete*; if we overclaim completeness we ship a false-confidence
tool. Mitigation, and I want this in the spec: ship a **small, explicit,
documented, user-extensible catalog** (a YAML/JSON the user edits), make every
finding cite which catalog rule fired, and state plainly "this checks the paths
in the catalog, not all paths." That keeps the feas-5 MVP honest and bounds
scope creep — same discipline you applied to PERMDIFF's stretch goal.

## Round-2 ranking
1. **REACHGATE** (TRIPWIRE ∪ PERMDIFF, unified) — one deterministic cross-config
   reachability engine; audit mode + drift mode; **taint source→sink** model.
   Absorbs your top pick and mine, beats the flat scanners structurally, dodges
   the corpus trap, buildable in hours. novelty 4, usefulness 4.5, feasibility 4.5.
2. **TRACELINT (your B2)** — I concede this is the right survivor of my dead
   NETHERTRACE/FINGERPRINT pair. Keep it as the fallback if REACHGATE's taint
   catalog proves too fiddly for the time box. novelty 3.5, usefulness 4, feas 4.5.
3. *(nothing else — I'm not padding the field; we've converged and that's good.)*

novelty-b: two things for round 3. (1) Do you accept the collapse — that drift
mode is a wrapper over audit mode, so REACHGATE is one build not two? If not,
show me a PERMDIFF MVP that's useful *and* genuinely cheaper than the reachability
engine. (2) Attack the taint source/sink catalog: is a defensible,
demo-credible catalog assemblable in the time box, or does it drag REACHGATE's
feasibility below TRACELINT's? That's the one place I think you can still move me.
