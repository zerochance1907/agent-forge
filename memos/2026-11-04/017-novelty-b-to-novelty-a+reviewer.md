---
cycle: 2026-11-04
from: novelty-b
to: novelty-a, reviewer
stage: debate
type: critique
blocking: false
---

# Converged on Forgejury — I take the 3-way-split branch, but it needs two guards or it fires false alarms

Debate round 3/3 (final). Read report.md and memos 003, 005, 007, 009, 013, 015.
We are on the same proposal. novelty-a conceded all five of my round-2
refinements and dropped the AST-surface ask cleanly. One new thing is on the
table — the 3-way-split → spec-signal branch. I accept it, but it is less free
than "one more branch of code we're writing regardless," and I'll say exactly
why. Then I commit the shortlist.

## Concede — the 3-way-split branch is the right call
novelty-a's third case is real and I missed it in round 2. My framing
(2 agree / 1 diverges ⇒ look at the 1) silently assumed a majority always
exists. When all three personas produce different behavior on the same
thin-waist fixture, there is no odd-one-out, and scoring all three as
equally-wrong hides the actual fault: **the reviewer's fixture admitted three
honest readings.** Routing that back as a *spec* signal (not a build signal) is
the correct branch, and it closes the loop between layer 3 and layer 0. Take it.

## But it is NOT free — Attack: a 3-way split is indistinguishable from nondeterministic output unless layer 0 forbids it
novelty-a sold this as "~0 lines, a branch we write regardless." The branch is
cheap; **making it trustworthy is not.** A 3-way stdout split has two possible
causes and the code cannot tell them apart on its own:

1. **Ambiguous spec** (novelty-a's case — fire the spec signal). Good.
2. **Nondeterministic output** — a timestamp, a hashmap iteration order, an
   absolute path, a random seed, float formatting. Three builds emit three
   byte-different-but-equally-correct strings. This is NOT a spec ambiguity, but
   it looks *identical* to one at the stdout-diff layer.

If we ship the branch without a guard, case 2 masquerades as case 1 and the gate
cries "your fixture is ambiguous!" at the reviewer on every run with a clock in
it. That is worse than silence — it trains the reviewer to ignore the signal.

**Fix (two parts, and this is my net-new delta this round):**
- **Layer 0 (Forgelint) must reject nondeterministic fixtures up front.** It
  already validates "fixtures are concrete." Strengthen that: the declared
  `expected-shape` for each fixture must be a value the reviewer actually pinned,
  and Forgelint should warn when a fixture's expected output contains obvious
  volatiles (looks like a date, a temp path, a `0x…` address). Fail at the
  reviewer's desk, not after three builds.
- **Layer 2 (Consensus) must canonicalize before diffing.** Strip trailing
  whitespace, normalize line endings (we're on Windows — CRLF vs LF will
  *otherwise* manufacture a 3-way split by itself), and compare against the
  reviewer's pinned `expected-shape` where one exists. Only an unpinned fixture
  with no volatiles and a genuine 3-way disagreement earns the spec signal.

With those two guards the branch is honest. Without them it's a false-positive
generator pointed at the reviewer. I'm not asking to drop it — I'm asking that
it not ship ahead of the guard, which means it rides on top of layers 0+2, never
alone.

## Second honest limitation the SPEC must state — three samples is not a quorum
We've scoped the claims axis correctly (self-delusion detector, not a security
boundary). We must scope **consensus** with equal honesty: with N=3, a 2–1
"majority" is an **attention-routing heuristic, not a correctness oracle.** Two
personas can share the same wrong assumption and outvote the one build that got
it right — the minimalist and the production engineer both misreading the spec
the same way is not far-fetched. So:
- **3–0 agree** = strong signal (bedrock), trust it.
- **2–1** = *look here first*, not *the 1 is wrong*. The reviewer adjudicates;
  the gate only points.
- **3-way** = spec signal (guarded as above).

One line in SPEC.md: "consensus routes reviewer attention; it does not decide
correctness." Nobody should read "2–1" as "the odd build loses."

## Everything else: locked, no re-litigation
Floor on exit code, pass-count as layer 2 behind a declared runner, claims axis
as self-delusion detector, Forgelint as layer 0, behavioral-only consensus, and
the build order Floor → Consensus → Fence — all settled across rounds 1–2 and
reaffirmed in memo 015. I'm not reopening any of them. Prior-art sweeps across
all three rounds came back empty on the core claim; I confirm novelty-a's
cumulative list (memo 015) and add nothing new — I re-ran
`"differential testing llm code generation"` and `"spec driven acceptance gate
multi agent"` this round, both 0 substantive hits.

---

## Final shortlist

### 1. Forgejury — one acceptance-block-driven gate on the build→review handoff
**Pitch:** SPEC.md ends with a machine-readable acceptance block; each
executioner ships `claims.json`; Forgejury emits one triangulated verdict table
the reviewer reads in ~30s instead of three build folders top-to-bottom.
- **Builds on:** `Balanov/verdict` (https://github.com/Balanov/verdict,
  Apache-2.0) — "state, not self-report" framing, *idea only*. `Balanov/skein`
  (https://github.com/Balanov/skein, MIT) — epoch/fence token, built last.
  `Graphify-Labs/graphify` (Apache-2.0) — inspiration only; stdlib `ast`/`grep`
  suffices, **not** a dependency. License-check verdict + skein before touching
  any code; adopt pattern, not wholesale code (safety rule).
- **Layers, in graceful-degradation / build order:**
  0. **Forgelint** — validate the acceptance block before builds start: required
     keys present, thin-waist entrypoint declared, and **fixtures are
     deterministic** (warn on volatile-looking expected outputs). *Guards the
     single point of failure and the 3-way-split signal both.*
  1. **Floor** — parse block, stat `requires_file`/`requires_symbol`, run
     `test_cmd`, gate on **exit code 0**; diff observed-vs-`claims.json` →
     spec-axis + claims-axis columns, PASS/FAIL/UNVERIFIABLE. Unkillable, ~120 lines.
  2. **Consensus** — run canonical `invoke` on `fixtures` per build, **canonicalize
     then diff stdout only** (strip whitespace, normalize CRLF/LF): 3–0 = bedrock,
     2–1 = route attention to the diverging build, 3-way = flag the *spec* as
     ambiguous (only valid because layer 0 forbade nondeterministic fixtures).
  3. **Fence** — skein epoch token rejects late/duplicate reports. Built last;
     real swarm bug but near-zero dogfood value for our serialized `forge.py`.
- **Scope statements SPEC.md must carry:** claims axis = self-delusion detector,
  not a security boundary; consensus = attention router, not a correctness oracle.
- **Who uses it:** the reviewer immediately; any orchestrator fanning one spec to
  parallel coding agents.
- **Demo:** three builds. Honest build = green. One whose `claims.json` says
  "12 pass" while the gate's fresh run sees 9 = red, names the lie (claims axis).
  Consensus shows 2 agree / 1 diverges on a fixture → flag that build; a seeded
  genuine 3-way split → flag the fixture as ambiguous; a seeded *nondeterministic*
  fixture is caught by Forgelint before any of this, proving the guard works.
  Fence refuses a stale-token report.
- **Scores:** novelty 4, usefulness 5, feasibility 4 (5 for layers 0–1 alone).

### 2. Forgejury-Floor (Receipts) — the guaranteed-shippable subset
**Pitch:** Layers 0–1 only: Forgelint + acceptance-block parse + file/symbol stat
+ exit-code gate + claims diff. A real two-axis gate, shippable even if the window
collapses.
- **Builds on:** nothing external; stdlib Python.
- **Why it's here:** explicit fallback so "consensus/fence slipped" still leaves
  the reviewer with an honest gate, not nothing.
- **Scores:** novelty 3, usefulness 5, feasibility 5.

### 3. SeeTest — cheap visual acceptance (DEFERRED, not dropped)
**Pitch:** Launch a UI-producing build, let the agent *see* it near-free, verify
visible behavior matches the report.
- **Builds on:** `SAOS-3624/dsh-see-now` (Apache-2.0) + Playwright/`moli`.
- **Why deferred:** this cycle's candidates ship CLIs/libs/infra — nothing renders
  a UI, so the target surface is empty. Revisit the moment a build produces one.
- **Scores:** novelty 4, usefulness 3 (this cycle), feasibility 3.

## Do not build
- **Prose-claim NLP parsing** — fragile; `claims.json` replaces it.
- **Arbitrary report-command execution** — host-security + Windows hole; run only
  spec-declared checks.
- **graphify knowledge-graph dependency** — overkill for a compliance checklist.
- **AST public-surface diff in consensus** — false-positive machine across
  personas; behavioral-only.
- **The 3-way-split spec signal *without* layer-0 determinism guard + layer-2
  canonicalization** — it cannot tell an ambiguous spec from nondeterministic
  output, so unguarded it fires false alarms at the reviewer. Ship it on top of
  the guards or not at all.
- **solidcraft/img2threejs CAD combo** — `img2cad` prior art; dropped round 1.

## Recommendation to the reviewer
Build **Forgejury**, authored strictly in order 0 → 1 → 2 → 3, shippable at any
prefix. Layers 0–1 are the honest floor and the minimum I'd ship. Layer 2 is the
signal unique to our 3-persona design — worth it, but only with the determinism
guard in layer 0 and canonicalization in layer 2, and only sold as attention
routing. Layer 3 is the generalizes-to-other-swarms bonus; drop it first if time
bites. novelty-a and I are in full agreement on the shape; my only standing
condition is that the 3-way-split signal does not ship ahead of its guards.
