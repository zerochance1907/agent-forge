---
cycle: 2026-11-11
from: novelty-a
to: novelty-b, reviewer
stage: debate
type: rebuttal
blocking: false
---

# Round 2: I concede Rehearsal and Receipts' MVP, accept SignalLoss's metric (with a reproducibility fix), narrow GateCrash — and fuse GateCrash + Rehearsal's good kernel into "ApprovalAudit"

Read report.md, memos 001/003/005. novelty-b's round 1 is mostly right and I'm
not going to defend losing ground. The interesting move this round is that b's
own GateCrash critique (c, below) reveals a sharper, genuinely un-asked question
than either of us has pitched. New prior-art searches shown inline.

---

## Rehearsal (Idea 1) — conceded, dropped from contention

b's decomposition is correct and I won't relitigate it. Predictable tree-local
commands already have dry-run surfaces (`git clean -n`, glob expansion,
`--dry-run`), so a COW sandbox is over-engineering; network/stateful commands
leave no filesystem effect to preview, so the primitive can't touch the class
that most needs a seatbelt; the honest residue (opaque tree-local mutations) is
too narrow to headline and dies on the 40-50s Windows-Sandbox cost. **Rehearsal
is dead as a standalone product.** But its *kernel* — "the human should approve
the observed blast radius, not a tool name" — is not dead. I reuse it below as
an oracle, not a product. That's the right home for it.

## Receipts (Idea 2) — MVP conceded; the prose version is the real idea and it *is* buildable

b landed the hit: if the agent can emit `A calls B` as a structured triple, you
could have queried graphify directly, so the MVP grades a hallucination the
architecture already removed. Conceded. But the deferral was a mistake on my
part, not a property of the idea. The prose MVP is feasible without deferring the
hard part, and it closes b's own gap:

- **Pass 1 (writer):** the agent produces prose ("here's how auth works").
- **Pass 2 (extractor):** a *separate* call to the model already in the MCP
  client turns that prose into structural claims. Different pass, different
  prompt — so the writer is not grading itself (that was b's objection to the
  single-pass MVP).
- **Pass 3 (adjudicator, deterministic):** each extracted claim is resolved
  against graphify's `EXTRACTED` edges → GROUNDED / UNSUPPORTED, with line cites.

b's second point — that `UNSUPPORTED` and graphify's `INFERRED` tag blur — is
real and I'll fix it by *using* the distinction: a claim resolved only via an
`INFERRED` edge is reported as GROUNDED-BY-INFERENCE (a third verdict), not
silently merged. That makes the overlay crisper than graphify's raw tags, which
is the point. Still, honestly: this needs the client model in the loop twice and
the demo is less clean than a mechanical harness. **novelty 4, usefulness 4,
feasibility 3.** It stays alive as the one *product* on the table (neither
SignalLoss nor GateCrash is something a user runs daily — they grade other
people's tools), but I'm not pretending it out-feasibilities the harnesses.

## SignalLoss (Idea 3) — accept fact-recovery, but keep the benchmark reproducible

b is right that byte-exact survival unfairly penalizes faithful-lossy
compressors (headroom's `kompress-v2-base` is *allowed* to rewrite punctuation).
Accepted. One improvement so we don't trade a false-negative trap for a
non-reproducible leaderboard — a benchmark whose scores come from "ask the model
if the fact survived" isn't a stable leaderboard (nondeterministic, costs a key
or burns client tokens, unrepeatable across runs). So **tier the needles**:

1. **Structured needles** (error codes, hex IDs, numbers, paths) — the majority.
   Recovery = exact match on a *normalized key* (strip whitespace/punctuation,
   casefold, match the token). Fully deterministic. This captures b's
   faithful-lossy case without a model.
2. **Prose needles** (a one-off human-readable warning) — small tier. Here and
   only here, optional model-judged recovery, clearly flagged as non-reproducible
   and reported separately.

Report three columns: byte-exact, normalized-recovery (headline), model-recovery
(optional). That keeps SignalLoss a *reproducible* regression target the tool
authors can adopt — which was the whole reason it beats a one-off blog
benchmark. **novelty 3, usefulness 4, feasibility 5.** Still the safe ship.

## GateCrash (b's idea) — strong, but let me narrow it before we crown it

I like it and it tests the report's freshest theme mechanically. Three honest
problems, in increasing order of importance:

**(a) The named builds-on aren't the systems under test.** Pinky gates *phone UI
taps* with per-action human approval; sandbox-mcp is a disposable clean-room
*runner*, not an allow/deny policy gate. Neither is a command-pattern gateway.
The actual SUTs are the `mcp-firewall` repos — which are NOT in the research
report; they surfaced from our prior-art search. So GateCrash largely builds on
*non-researched* repos. The reviewer weighs "combine the researched projects";
GateCrash is thin on that axis as written.

**(b) Feasibility of the *matrix*.** SignalLoss is two pip/binary installs.
GateCrash's headline is a pass/fail matrix *across gateways* — that means
installing and MCP-wiring several heterogeneous gateways (different langs,
configs) in a few hours. Scope it to one gateway and it's feasible, but the
"matrix" shrinks to a single column. Be honest about that in the spec.

**(c) The premise conflates two gateway designs — and this is the useful bit.**
Obfuscation evasions (base64, `sh -c`, chaining) only beat *pattern-based*
allow/deny lists. They do **nothing** to a *human-approves-every-action* gate
like pinky, because there's no regex to fool — the human sees *something* either
way. So GateCrash's real finding is "pattern-based deny lists are evadable,"
which is WAF-bypass / command-injection lore applied to MCP. Valuable and worth
mechanizing, but a more modest novelty than "nobody tests the primitive the
whole theme depends on." The pattern-based class is testable-and-evadable; the
human-approval class is a *different* failure mode entirely. **novelty 3 (not 4),
usefulness 4, feasibility 4-as-single-gateway / 3-as-matrix.**

---

## My round-2 idea — "ApprovalAudit": GateCrash's evasion test + the question (c) exposes that nobody asks

b's point (c) reveals the un-asked question. Pattern gates fail by being
*evaded*. Human-approval gates (the fresh, pinky-style primitive the report
actually calls the interesting one) can't be evaded by obfuscation — so how do
*they* fail? **They fail by asking the human to approve an action they don't
understand.** "Tool `shell` wants to run — approve? [y/N]" is a rubber stamp if
it doesn't convey blast radius. Nobody tests that. This is where Rehearsal's dead
product becomes a live *oracle*.

**Pitch:** one mechanical harness, two axes per gateway:

1. **Evasion (keep b's GateCrash wholesale, credit it):** does an obfuscated
   destructive action reach "execute" without approval? Pass/fail per evasion
   class, against pattern-based gates. Canary design = b's: `touch
   CANARY_FIRED` instead of a real `rm`, safe to run.
2. **Approval-surface fidelity (new):** for actions that *do* correctly trigger
   approval, does the prompt the gateway shows the human convey blast radius?
   Score it against a ground-truth label the harness computes per canary:
   `{reversible?, networked?, #files affected, hits-external-system?}`. A gate
   that pauses on `rm -rf build/` but only says "approve tool `shell`?" scores
   low; one that says "deletes 37 files incl. 4 uncommitted" scores high.

The ground-truth oracle is exactly Rehearsal's defensible residue — the cheap
preview-router (glob expansion, `git status`, parsed request for network calls).
It was too thin to be a product; it's perfect as the *grader*. So nothing is
wasted: GateCrash tests "did the dangerous thing slip through," ApprovalAudit
adds "and when it correctly stopped, did the human actually have enough to judge."

**Builds on (researched repos, honestly):** pinky (#1, Apache-2.0) — the
human-gated-approval primitive is the thing whose *information quality* we score;
sandbox-mcp (#5, MIT) — its "prove a claim in a clean room" framing is the
fidelity standard an approval prompt should meet. mcp-firewall repos remain the
pattern-gate SUTs for axis 1. Still no upstream code vendored — black-box over
MCP/CLI.

**Why novel (searched this round, all empty):**
- `gh search repos "agent approval blast radius"` → 0
- `gh search repos "mcp approval preview diff"` → 0
- `gh search repos "command gateway bypass obfuscation"` → 0
- `gh search repos "irreversible command classifier agent"` → 0
- `gh search repos "agent approval gateway risky action"` → 0

Evasion-testing of pattern gates is near prior appsec lore (b's point c);
*scoring the information quality of an approval surface* is unclaimed. That's the
wedge, and it's the one question the report's "freshest theme" actually turns on
— pinky's whole bet is "pause for your click," and no one has asked whether the
click is informed.

**Who for:** gateway authors (a two-axis regression target: not just "is my deny
list evadable" but "is my approval prompt a rubber stamp"), and users choosing
one ("gate A blocks nothing I obfuscate; gate B blocks it but its approval prompt
is blind — here's the matrix").

**Few-hour plan:** reuse b's evasion corpus for axis 1; add the deterministic
blast-radius oracle (glob/`git status`/request-parse) for axis 2; drive one
pattern gate (mcp-firewall) and one approval gate (pinky, if its approval event
is observable over MCP — flag as the feasibility risk to confirm at build time)
→ emit a markdown matrix. Model in the hot path: none for axis 1; none for axis 2
(the oracle is mechanical).

**Scores:** novelty **4**, usefulness **4**, feasibility **4** (3 if we insist on
driving *both* a pattern gate and a live pinky in the same build — scope to one
class per the same honesty I demanded of GateCrash).

---

## Provisional round-2 ranking (formal shortlist in round 3)

1. **ApprovalAudit** — bolder than vanilla GateCrash, tests the one question the
   fresh theme actually depends on, mechanical oracle, builds on researched repos
   honestly. Subsumes and credits GateCrash's axis 1.
2. **SignalLoss** (tiered reproducible metric) — safest, cleanest demo. Unchanged
   ship-worthiness; still the fallback if feasibility wins the room.
3. **Receipts (prose MVP, 3-verdict)** — the only *product*, but model-in-loop
   twice; keep as the "if we want a thing users run, not a grader" option.

b: tell me either (1) ApprovalAudit's blast-radius oracle is not actually
mechanical for the networked class (I think "parse the request + classify
reversibility" is enough to score the *prompt*, without executing — push on
that), or (2) that a live pinky's approval event isn't observable enough to grade
axis 2, which would collapse me back to pattern gates and make ApprovalAudit and
GateCrash near-identical. If (2) holds, I'll concede GateCrash is the bolder ship
and we converge. Otherwise ApprovalAudit is the ambitious pick that's still
buildable.
