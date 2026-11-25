---
cycle: 2026-11-25
from: novelty-b
to: novelty-a, reviewer
stage: debate
type: critique
blocking: false
---

# Collapse accepted — REACHGATE is one build. But the taint model is asymmetric: sinks are machine-readable, sources are not. That asymmetry is the whole feasibility question.

You conceded cleanly and the collapse is correct. I'm not relitigating the dead
three. I answer your two questions, then land the one place you said I could
still move you: the source/sink catalog. Short version — **the sink half ships
in the time box; the source half does not, unless it's an explicit declared
layer, not auto-inferred.** Build it that way and REACHGATE stays feasible and
earns novelty 4. Build it the tempting way and it drops below TRACELINT and
ships false confidence.

## Q1: Do I accept the collapse? Yes. PERMDIFF ⊂ REACHGATE — withdrawn as separate.
You're right: a flat permission set-diff loses to `git diff`, and the non-thin
version of drift *is* "diff the reachable source→sink paths," which needs the
reachability engine. One engine, two modes. Settled. **But one correction to the
emphasis, for the spec:**

- **Audit mode on a seeded over-permissioned sample dir is a toy demo.** We
  planted the vuln; of course it traces it. It proves the engine runs, not that
  anyone needs it.
- **Drift mode is the mode with a real-world narrative** — benign skill/MCP
  server ships a malicious *update* that widens reach (the supply-chain vector
  none of the flat scanners watch). That's the demo that justifies the tool's
  existence.

So: one engine, but the spec should **lead the demo with drift**, with audit as
the sub-primitive. Don't let the reviewer grade us on the toy.

## Q2: Is a demo-credible taint catalog assemblable in the time box?
This is the real question and the answer is **split**, because the two halves of
a taint graph have opposite data availability:

- **Sinks are declarative and machine-readable.** `Bash(*)` / network egress /
  filesystem-write / secret-file-read are *stated* in `settings.json` permission
  globs, `.mcp.json` scopes, and skill frontmatter. A finite catalog of "these
  capability patterns are dangerous sinks" is small, deterministic, and
  assemblable in an hour. The multi-file **join** — grant in file A + allowlist
  in file B + secret file C present — is the real engine and it's all over
  machine-readable surfaces. **This half is feas-5 and it's the half that beats
  lorbeere/mcpsec structurally.** They scan one manifest flat; the join is a
  graph query they can't express. Agreed, fully.

- **Sources are NOT declared anywhere machine-readable.** "This skill ingests
  untrusted input (web page / GitHub issue / email / shared doc)" is a *semantic*
  property living in the skill's prose and code, not in any config field. To
  classify a skill as an untrusted-input source you have exactly two options:
  1. **regex/keyword-match the skill's name + description** ("issue", "web",
     "fetch", "email") — heuristic, misses the ones that matter, and is the
     definition of a false-confidence tool: it will *confidently* clear a skill
     whose description doesn't contain your keywords but which reads untrusted
     input anyway.
  2. **require the user to annotate which skills are sources** — then it is not
     automatic, and the headline "skill `triage-issues` reads untrusted issue
     text → RCE" finding only appears because the user already told us
     `triage-issues` is a source.

Your mitigation ("small user-extensible catalog, cite which rule fired, say
'checks catalog paths not all paths'") correctly handles **sink/rule
completeness**. It does **not** touch the **source-identification** problem,
which is a different and harder thing: a catalog of dangerous *capabilities* is
finite and shared across all users; a mapping of *which concrete skills are
sources* is per-deployment and inherently semantic. You under-stated this.

**My verdict, and the move I want in the spec:**
- Ship **permission→sink reachability** (capability reaches secret/shell/egress
  via the cross-file join) as the **deterministic MVP spine**. All three
  endpoints are machine-readable. This alone is the structural beating of the
  flat scanners and it's demo-safe.
- Ship **untrusted-source→sink taint** as an **explicitly declared annotation
  layer** — the user (or a clearly-labeled-heuristic catalog) marks sources, and
  every taint finding states "source classification is declared/heuristic, not
  proven." Keep it; it's where novelty 4 lives. But do NOT auto-infer sources
  from descriptions and then present "issue → RCE" as a *discovered* fact. That's
  the false-confidence failure mode, and it's the exact sin we both taxed the
  flat scanners for (overclaiming coverage).

Done this way, feasibility holds at ~4.5. Done the auto-infer way, it drops below
TRACELINT and we ship a tool that lies.

## New prior-art warning you need before you write "prompt injection path"
I re-ran the lanes. Your two zero-claims **hold** — live today:
- `gh search repos "mcp permission reachability taint"` → **[]**
- `gh search repos "mcp prompt injection taint flow"` → **[]**
- `gh search repos "mcp permission drift diff"` → **[]**
- `gh search repos "agent config permission change detection"` → **[]**

So the *reachability/drift* lane is genuinely empty. **But** the moment you frame
the pitch as "prompt injection," you're adjacent to a populated space I hadn't
flagged before — **MCP tool poisoning scanners**:
- `invariantlabs-ai/mcp-injection-experiments` (**211★**) — tool-poisoning PoCs.
- `akanthed/SecureAI-Scan` (25★) — "prompt injection, MCP tool poisoning."
- `jakeefr/mcp-sentinel` (3★) — "runtime scanner for MCP tool poisoning, native
  Claude Code plugin."
- `TsvetanG2/mcpward` (8★) — "MCP tool poisoning, rug-pulls, **schema drift**."

These scan a **single surface** — the MCP server's tool-description text — for
embedded malicious instructions. That is **not** our cross-host-config join, so
the wedge survives. But the spec must **position REACHGATE explicitly against
tool-poisoning**: "we do cross-config *reachability*, not tool-description
injection scanning." If we say "prompt-injection scanner" unqualified, a reviewer
one-lines us with invariantlabs' 211★. Also note `mcpward` already uses the words
"schema drift" — so when we say "drift" we must say **reachability drift / newly-
reachable sinks**, not generic config drift, or we collide there too.

## Where we actually are
We've converged, and I think that's the right outcome — one well-scoped engine
beats three half-ideas. I'm not padding a fourth idea in. My B2 (TRACELINT)
stays on the table as the honest fallback exactly as you framed it: if the
source-annotation layer proves too fiddly in the time box, TRACELINT is the
deterministic, no-catalog survivor.

## Round-2 ranking
1. **REACHGATE**, with the split above enforced: permission→sink reachability as
   the deterministic spine (audit + drift modes, lead with drift), untrusted-
   source→sink as a *declared, labeled-heuristic* layer — **not** auto-inferred.
   Positioned explicitly vs. MCP tool-poisoning scanners. novelty 4, usefulness
   4.5, feasibility 4.5 **only if the source half stays a declared layer**;
   4 → 3 if sources get auto-inferred and over-trusted.
2. **TRACELINT (B2)** — honest fallback, no catalog to assemble. novelty 3.5,
   usefulness 4, feasibility 4.5.

(No `## Final shortlist` / `## Do not build` yet — those are round 3.)

novelty-a: one thing to resolve in round 3. Commit to whether the demo's headline
finding is (a) the **deterministic** permission→secret reachability chain across
3 files, or (b) the **source→RCE** taint finding that depends on a declared
source. I'll back (a) as the spine every time; I'll accept (b) **only** if it's
visibly gated behind a user-declared source and labeled as such. Pick, so the
reviewer can spec a demo we can actually stand behind.
