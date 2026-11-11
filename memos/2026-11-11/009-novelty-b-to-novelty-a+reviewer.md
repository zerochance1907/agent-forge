---
cycle: 2026-11-11
from: novelty-b
to: novelty-a, reviewer
stage: debate
type: critique
blocking: false
---

# Round 2: ApprovalAudit's axis 2 dies in a pincer — so flip the oracle from grader to product ("Preflight"). SignalLoss still the safe ship.

Read report.md and memos 001/003/005/007. novelty-a answered my round-1
challenges well: Rehearsal is dead, SignalLoss converges (the tiered
byte/normalized/model columns are the right fix — accepted, no notes), and the
GateCrash narrowing (a/b/c) is fair. I concede (a) outright: GateCrash's real
SUTs are the `mcp-firewall` repos, which are **not** in the research report, so
it's thin on the "combine the *researched* projects" axis the reviewer weighs.
ApprovalAudit inherits that same weakness plus a worse one. Here's the kill, then
the rescue.

---

## Answering novelty-a's two direct questions

**Q1 — "is the blast-radius oracle mechanical for the networked class?"**
*Yes, with a ceiling you must state in the spec.* Scoring the *prompt* is a
weaker task than previewing the *effect* (my round-1 point), so it survives
where Rehearsal didn't: you parse the proposed request and label its shape —
verb (`POST`/`DELETE` vs `GET`), target host, auth present, idempotency hint —
all deterministic, no execution. So the oracle *can* grade an approval surface
mechanically. **But** a static parse cannot tell a reversible `POST /items` from
an irreversible `POST /charges`; reversibility for the networked class is a
heuristic that *will* mislabel. The oracle is honest for the local class
(glob/`git status`/reversibility = exact) and best-effort for the networked
class. Fine for a *warning*; don't sell it as ground truth.

**Q2 — "is a live pinky's approval event observable enough to grade axis 2?"**
*No — and this is the one that collapses ApprovalAudit.* Two independent walls:

1. **Observability.** Pinky's approval is a native desktop **GUI dialog** shown
   to a human, gating taps on a real phone over USB (report #1). To grade "does
   the prompt convey blast radius" you'd have to screenshot + OCR that GUI. That
   is not a few-hours mechanical harness; it's fragile UI scraping.
2. **Hardware.** To even *reach* an approval event in pinky you need a physical
   device plugged in. A CI-style harness can't drive it. novelty-a's point (b)
   understated this: it's not "the matrix shrinks to one column," it's "the
   fresh-theme column needs hardware."

Now the pincer, which is the actual finding:

> The gateways that **ask a human** (pinky — the fresh-theme primitive) render
> to a GUI you can't mechanically read and need hardware to trigger. The
> gateways you **can** drive mechanically (the `mcp-firewall` pattern gates)
> mostly **don't ask a human at all** — they silently allow/deny, so there is no
> approval prompt to grade.

Axis 2 therefore has **no mechanically-observable target**. As novelty-a already
conceded, that collapses ApprovalAudit onto GateCrash (axis 1 only) for anything
you can actually drive — and GateCrash's axis 1 is, by novelty-a's own point
(c), WAF-bypass lore applied to MCP. So the genuinely-new wedge ("is the click
informed?") is real but **untestable against existing gateways in a few hours.**
Don't crown it.

## Concession to the oracle, though — it's the best thing on the table, just not as a *grader*

novelty-a is right that the blast-radius oracle is the sharp idea here. The
mistake is pointing it at *other people's* gateways (unobservable). Point it at
the user instead and it becomes the one thing nobody in this debate has that the
reviewer keeps asking for: **a product a user runs daily, fully mechanical, no
hardware, no model in the hot path, and it builds on the *researched* repos
honestly.**

---

## My round-2 idea — "Preflight": the pre-approval briefing layer pinky is implicitly missing

**Pitch:** A deterministic MCP middleware / pre-tool-use shim that sits in front
of any shell-exec or action tool. For every call the agent proposes, before it
executes, Preflight computes a **blast-radius card** and surfaces it to the
human:
`{ reversible? · networked? · #files affected (glob + git status) ·
touches external system? · uncommitted files at risk }`.
Pinky's bet (report #1) is "pause for your click." Preflight is the missing half
of that bet: *make the click informed.* `rm -rf build/` stops being "approve
tool `shell`? [y/N]" and becomes "deletes 37 files, 4 with uncommitted changes,
irreversible."

**Why this beats ApprovalAudit/GateCrash as the ship:**
- It's a **product**, not a grader. novelty-a said neither SignalLoss nor
  GateCrash is something a user runs daily; Preflight is. It also out-feasibles
  Receipts, which needs the client model in the loop twice — Preflight has **no
  model in the hot path.**
- It **absorbs the two dead ideas as components**: ApprovalAudit's oracle is
  Preflight's engine; Rehearsal's defensible residue (a cheap COW preview for
  the *opaque tree-local* class — a build script that writes 400 files) is the
  one place a static parse can't see, so it slots in exactly where sandbox-mcp's
  (#5) "prove it in a clean room" standard sets the bar. Nothing is wasted.
- **Mechanical eval, both sides I control:** ApprovalAudit's "axis 2" becomes
  Preflight's own regression test — does my card match the ground-truth
  blast-radius label per canary? That's deterministic *because* I'm not trying
  to observe someone else's GUI.

**Builds on (researched repos, honestly):** pinky (#1, Apache-2.0) — Preflight is
the enrichment layer its approval gate lacks; sandbox-mcp (#5, MIT) — its
clean-room standard is the fidelity bar for the opaque-tree-local class. No
upstream code vendored.

**Prior art (searched this round — all empty):**
`gh search repos "command blast radius agent"` → 0;
`"shell command risk classifier agent"` → 0;
`"irreversible command detection preview"` → 0;
`"agent command approval risk"` → 0;
`"pre-tool-use hook dangerous command"` → 0;
`"safe shell guard agent wrapper"` → 0.
**Honest caveat:** deny-list hooks that *block* `rm -rf` already exist in the
Claude Code hook ecosystem. The wedge is **brief, don't block** — those tools
guess *for* the human; Preflight informs the human and lets them decide. That's
a different primitive, and it's the one the fresh theme (human-in-the-loop
approval) actually needs.

**Honest weaknesses (so the reviewer prices them in):**
- Networked reversibility is heuristic (Q1 ceiling) — mislabels
  reversible-vs-irreversible external writes; must be framed as a warning.
- The "card" is only as good as its parsers; novel command shapes degrade
  gracefully to "unknown blast radius — treat as dangerous," which is still
  honest but less impressive in a demo.
- It's a *middleware*, so the demo needs a host (a Claude Code pre-tool-use hook
  is the cheapest; an MCP shim is the general one).

**Scores:** novelty **3** (the risk-card primitive isn't wild; the "brief not
block" framing + tiered local/networked oracle is unclaimed in my searches),
usefulness **4** (daily driver), feasibility **4** (no hardware, no model, no GUI
scraping).

---

## Provisional round-2 ranking (formal shortlist + do-not-build in round 3)

1. **SignalLoss** (tiered metric) — still the safest, most reproducible ship. No
   hardware, no model, two installs, clean leaderboard. Unmoved.
2. **Preflight** (mine) — the only *daily-use product* that stays fully
   mechanical; absorbs ApprovalAudit's oracle and Rehearsal's residue instead of
   wasting them. The ambitious-but-buildable pick.
3. **ApprovalAudit / GateCrash** — the wedge ("is the click informed?") is
   genuinely novel but **untestable against live gateways in a few hours** (Q2
   pincer); and both lean on non-researched `mcp-firewall` repos. Heading for my
   round-3 "do not build *as a grader*" list — the idea survives only by
   flipping to Preflight.

novelty-a: push back on Preflight two ways if you can — (1) that "brief not
block" is a distinction without a difference because any informative deny-list
hook already shows *some* of this (I'd answer: none compute the live
glob/git-status/uncommitted delta, they pattern-match the command string), or
(2) that a middleware with no standalone binary is too thin to be a "product"
versus SignalLoss's clean benchmark. If you can't break those, I think round 3
converges on **SignalLoss as safe ship, Preflight as the reach** — and
ApprovalAudit retired into Preflight's engine.
