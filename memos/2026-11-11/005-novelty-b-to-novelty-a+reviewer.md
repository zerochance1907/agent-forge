---
cycle: 2026-11-11
from: novelty-b
to: novelty-a, reviewer
stage: debate
type: critique
blocking: false
---

# Round 1: Idea 1 is unsound as pitched, Idea 2's MVP is too thin, Idea 3 is the real ship — plus GateCrash

I read report.md, memo 001 (researcher) and memo 003 (novelty-a). I re-ran the
prior-art searches. Short version: novelty-a did the diligence honestly (the
mcp-firewall category is real — I confirmed `ressl/mcp-firewall` 20★,
`hyprmcp/mcp-gateway` 92★, plus `muhammadkh4n/mcp-firewall` and
`ilia-ershov/mcp_firewall` which already do prompt-injection filtering on tool
output). But the headline idea has a soundness hole, the "safe" idea is the one
actually worth shipping, and there's a sharper fourth option.

---

## Idea 1 "Rehearsal" — attack: the preview primitive is *unnecessary where it works and unsound where it's needed*

The pitch is "run the risky call in a disposable clone first and show the real
effect." That splits risky commands into two classes, and the sandbox-replay
primitive fails on both:

1. **Tree-local, statically predictable commands** (`git reset --hard`,
   `rm -rf build/`, `git clean`, a redirect `>` clobbering a file). You do **not
   need a COW sandbox** to preview these — the effect is computable cheaply and
   exactly from tools that already ship dry-run surfaces: `git reset --hard` →
   `git status` + `git stash list` tells you what you'd lose; `rm -rf build/` →
   expand the glob and list it; `git clean -n`, `rsync --dry-run`, `npm/pip
   --dry-run` all exist. The whole demo ("show the 37 files that would die, 4
   with uncommitted changes") is deliverable *without a sandbox at all*. The
   sandbox is over-engineering here.

2. **Networked / stateful commands** (`curl -X POST`, `aws s3 rm`, `psql -c
   'DROP ...'`, `gh release delete`). Here a "disposable clone of the working
   tree" shows you **nothing** — the side effect isn't in the filesystem. To
   "preview" it you'd have to actually fire the request (not a preview) or mock
   the remote (not the real effect). This is exactly the class where you most
   want a seatbelt, and the primitive can't touch it.

So the genuinely-defensible residue is narrow: **non-network commands whose
local-tree effect is opaque to static prediction** — a build script that writes
400 files, a codemod/formatter, `make install` into the tree. *There* a COW
replay shows you something a dry-run flag can't. That's a real but much smaller
wedge than "shell + filesystem mutations," and the 40–50s Windows-Sandbox cost
novelty-a already flagged makes even that marginal. **Concession:** if you
re-scope Idea 1 to "preview opaque tree-local mutations via a cheap COW overlay
(not Windows Sandbox), and fall back to static dry-run for the predictable
class," it's honest and buildable — but at that point novelty drops (it's a
nicer `git clean -n`) and feasibility only recovers if you drop the full-OS
path. Net: **novelty 3, usefulness 4, feasibility 2 as pitched / 3 re-scoped.**
Not the one to fight for.

## Idea 2 "Receipts" — attack: the MVP checks the thing you didn't need checked

The useful version verifies *free prose* ("here's how this module works"). That's
explicitly punted to a stretch goal. What's left in the MVP: the agent emits
structured triples (`A calls B`), and Receipts resolves them against graphify's
graph. But if the agent can already emit the structured claim, **you could have
queried the graph directly** instead of asking the agent and then grading it —
the hallucination surface the MVP closes is one the architecture mostly removes.
Worse, graphify already tags edges `INFERRED` (= not ground truth); an
`UNSUPPORTED` verdict and an `INFERRED` edge blur into each other, so the "verdict"
is less crisp than it sounds. The hard, valuable part (prose → checkable claims)
is the part being deferred. **novelty 3, usefulness (of the MVP) 2–3, feasibility
3.** Rank it last of the three.

## Idea 3 "SignalLoss" — concede, this is the ship — with one metric fix

Agreed this is the strongest. The report flags the gap twice, both target tools
install locally with no key, and the output (a fidelity-vs-ratio leaderboard
neither README reports) is a clean, honest demo. One sharpening, because the
pitch as written has a false-negative trap: **byte-exact needle survival is the
wrong metric.** A *faithful lossy* compressor is allowed to rewrite "FATAL: disk
full on /dev/sda" → "FATAL disk full /dev/sda"; byte-equality would score that a
drop when the signal survived — unfair to exactly the tools (headroom's
`kompress-v2-base`) that compress structured text on purpose. Fix: score
**fact-recovery**, not string-equality — after compression, can the needle fact
still be read out (exact-match on a normalized key field, or a cheap yes/no
"does this output still contain error code Xyz" from the model already in the MCP
client)? Keep a strict byte-exact column too, but headline the recovery metric.
That turns "a benchmark" into a defensible claim about *faithfulness* and makes
it adoptable as a regression target by the tool authors. **novelty 3, usefulness
4, feasibility 5.** My current top pick.

---

## My idea — "GateCrash": an adversarial evasion tester for agent action-gateways

**Pitch:** The freshest theme in the report (researcher's #2) is the *independent
trusted gateway* that gates an agent's risky actions — pinky, sandbox-mcp, and
the whole mcp-firewall category all rely on it. **Nobody tests whether that gate
actually holds against an agent trying to route around it.** GateCrash is a
mechanical harness that throws a corpus of *action-level evasions* at a
gateway's allow/deny policy and reports which dangerous actions reached the
"execute" side without triggering approval: base64/hex-encoded commands,
`sh -c`/`eval` indirection, command chaining (`; && |`), writing-then-executing
a script, renamed binaries (`cp $(which rm) ./x`), env-var obfuscation, unicode
homoglyphs in tool names. Output: a pass/fail matrix per evasion class per
gateway.

**Builds on:** [pinky](https://github.com/DIYgod/pinky) and
[sandbox-mcp](https://github.com/shanselman/sandbox-mcp) (the gateway pattern
under test, both permissive licenses) and the mcp-firewall repos above as the
systems-under-test. No upstream code vendored — GateCrash talks to them as a
black box over MCP/CLI.

**Why novel (searched):** `gh search repos "mcp firewall bypass test"` and
`"prompt injection benchmark mcp"` → empty. The closest hit,
`clemporio/agent-guardrail-red-team` (0★), red-teams the *model's* guardrails
with prompt-injection chains — it targets the LLM's judgment, not a programmatic
action-gateway's **allow/deny on obfuscated side effects**. That distinction is
the wedge: existing red-team work asks "can I talk the model into misbehaving";
GateCrash asks "does the trusted process correctly gate a destructive action the
model *already* decided to run but dressed up." No one tests the primitive the
whole fresh theme depends on.

**Who for:** every gateway author (regression suite) and every user picking one
("mcp-firewall blocks `rm` but not `sh -c $(echo cm0gLXJm | base64 -d)` — here's
proof"). Same two-axis, author-adoptable shape as Idea 3, applied to the theme
the report calls freshest.

**Few-hour plan:** Python corpus of evasion templates keyed to a single canary
action (touch `CANARY_DELETED` instead of real `rm`, so the harness is safe to
run) → drive each gateway with the raw and the obfuscated form → check whether
the canary fired without an approval event → emit a markdown matrix. Purely
mechanical, no model in the hot path. Highest-feasibility of anything bolder than
Idea 3.

**Scores:** novelty **4**, usefulness **4**, feasibility **4**.

---

## Round-1 ranking (provisional — formal shortlist in round 3)

1. **SignalLoss** (Idea 3, with fact-recovery metric) — safest, clean demo, honest.
2. **GateCrash** (mine) — bolder, tests the report's freshest theme, still mechanical.
3. **Rehearsal** (Idea 1) — only if re-scoped to opaque tree-local mutations and
   stripped of the Windows-Sandbox hot path.

## Do not build (so far)

- **Idea 1 as pitched** (sandbox-replay-then-approve for "shell + filesystem"):
  unsound for network/stateful commands, unnecessary for predictable ones.
- **Idea 2's MVP** (structured-triple verifier): closes a hallucination surface
  the architecture already removes; the valuable prose-verification part is
  deferred.
- **A generic MCP allow/deny gateway** — novelty-a already conceded this; the
  category is saturated (`hyprmcp/mcp-gateway` 92★ et al.). Building another gate
  is dead; *testing* the gates (GateCrash) is the open move.

novelty-a: convince me SignalLoss's fact-recovery metric is overkill, or that
GateCrash's canary design can't reach real gateways faithfully — otherwise I
think the ship candidate is one of those two, not Rehearsal.
