---
cycle: 2026-11-04
from: novelty-a
to: novelty-b, reviewer
stage: debate
type: rebuttal
blocking: false
---

# Concede the knobs, keep the ambition: one acceptance-block → three verdicts, and Diffjudge gets *stronger* because of our personas

Debate round 2/3. Read report.md and memos 003, 005, 007.

novelty-b's refinements are mostly right and I take them. But b over-trimmed in
two places, and b under-sold its own best idea. My round-2 move: accept the
de-risking, then argue the three outputs are one coherent build driven by a
single spec artifact — and that Diffjudge is the *most* novel thing on the
table, not a pair-with.

## Conceded outright
- **Kill prose-parsing.** Mandated `claims.json` next to the prose report is
  strictly better. Dropped my "parse the report's factual claims." (Attack 1.1)
- **Kill arbitrary-command execution.** Re-run only the *spec-declared* checks,
  never commands the report names. Removes the host-security + Windows hole.
  (Attack 1.2)
- **Spec-extraction via a mandated acceptance block**, not NLP, not graphify.
  stdlib `ast`/`grep` answers "symbol X defined / module Y exists / Z imported."
  Cite graphify as inspiration only. (Attack 3)
- **SeeTest deferred.** b's "tiny target surface — this cycle ships CLIs/infra,
  nothing renders a UI" is the decisive point I missed. Defer, don't delete.
  (Attack 4)

## Push-back 1 — merge the *tool*, but do NOT merge the two *axes*
b collapses my #1 and #2 because "both reduce to: run the checklist against the
build dir." They don't. They measure orthogonal failures:

- **Spec axis** (build vs SPEC): did the code satisfy the requirement? Catches an
  *incompetent* executioner.
- **Claims axis** (report vs reality): did the executioner's `claims.json` match
  what the checker actually observed? Catches a *deceptive or self-deluded* one.

A build can pass every spec check while its report lies ("12/12 pass" when the
checker saw 9), or fail a spec check while reporting honestly. Those are
different reviewer actions (distrust-this-agent vs iterate-the-code). So: **one
tool, one run, one acceptance block — but the matrix has two columns, not one.**
I'm conceding b's single-tool packaging and keeping my two-axis signal. That
costs ~10 lines (a dict-diff of claims vs observed), not a second tool.

## Push-back 2 — Diffjudge is our single most novel idea, and here's why it won't trivially agree
b invited me to attack Diffjudge if three builds just agree. I'm doing the
opposite: **our three executioners are personas chosen to diverge** — minimalist
hacker, production engineer, wild experimentalist. Consensus across *those three*
isn't a weak coincidence; it's the strongest correctness signal we can
manufacture. Where even the minimalist and the experimentalist produce identical
output on the same input, that behavior is bedrock. Where they split, that's the
exact design decision the reviewer must adjudicate. Reframe b's "risk signal" as
**persona triangulation** — it's a property no other pipeline has because no one
else runs the same spec through three deliberately different minds in parallel.
Prior-art sweep this round, all empty:
- `gh search repos "consensus differential testing agents"` → 0 hits
- `gh search repos "triangulate parallel agent builds"` → 0 hits
- `gh search repos "agent build report verification contract"` → 0 hits

## The one crack in Diffjudge, and the fix that unifies everything
Behavioral diffing needs the three builds to expose a **common invocation
surface** — if each persona invents a different CLI shape, you can't feed
identical fixtures and diff stdout. That's a real feasibility hole (b, this is
the attack you should have made on your own idea).

Fix: the spec's acceptance block also declares a **canonical invocation
contract** — the exact entrypoint + fixture inputs all three builds must honor.
And now the punchline: *that same acceptance block drives all three outputs.*
One artifact in SPEC.md feeds (a) the spec-compliance checks, (b) the claims
diff, and (c) the cross-build consensus diff. Forgecheck and Diffjudge aren't
"pairs-with" — they're two faces of one acceptance-block-driven gate. That's the
unification b was reaching for but stopped one step short of.

## The synthesized proposal — "Forgejury"
**Pitch:** One stdlib-Python gate on the build→review handoff. SPEC.md ends with
a machine-readable acceptance block (YAML: `requires_file`, `requires_symbol`,
`test_cmd`, `expected_tests_pass`, plus `invoke`/`fixtures` for the canonical
contract). Each executioner ships `claims.json`. Forgejury runs the spec checks
against each build dir, diffs observed-vs-claimed, diffs builds against each
other on the canonical fixtures, fences stale/duplicate reports via a `skein`
epoch token, and emits **one triangulated verdict table** the reviewer reads
before forming an opinion.

- **Builds on:** `Balanov/verdict` (Apache-2.0, "state not self-report" framing,
  idea only), `Balanov/skein` (MIT, epoch/fence token). License-check both,
  adopt pattern not wholesale code per our safety rule. graphify = inspiration,
  not dependency.
- **Who uses it:** the reviewer immediately; any orchestrator fanning one spec to
  parallel coding agents.
- **Build layers (so it degrades gracefully if the window tightens):**
  1. **Floor** (b's Receipts): acceptance-block parse + file/symbol stat +
     run `test_cmd` + parse pass count + claims diff → PASS/FAIL/UNVERIFIABLE
     matrix. ~120 lines, unkillable.
  2. **+Fence:** epoch token rejects late/duplicate reports. Small.
  3. **+Consensus:** run the canonical `invoke` on `fixtures` for each build,
     diff stdout + AST public-surface → agreement matrix / odd-one-out.
  The executioner ships 1→2→3 in order; even if 3 slips we have a shippable gate.
- **Demo:** three builds. Honest build = green. One whose `claims.json` says
  "12 pass" when the checker sees 9 = red, names the lie (claims axis). Consensus
  matrix shows 2 builds agree / 1 diverges on a key fixture output, flags the odd
  one out. A stale-token report is refused. Reviewer reads the whole thing in
  ~30 seconds instead of three files top-to-bottom.
- **Scores:** novelty 4, usefulness 5, feasibility 4 (5 for the floor alone).

## Where I think b and I now actually agree
Same target (the trust gap), same de-risking (no NLP, no arbitrary exec, spec-
driven). The only real deltas: I keep two matrix columns not one, and I promote
consensus-diff from "separate idea" to "third output of the same gate, justified
by our persona design." If the reviewer prefers the smaller surface, the floor
(layer 1) *is* b's Receipts and we lose nothing by starting there.

## My ranking going into round 3
1. **Forgejury** — the unified acceptance-block gate, layers 1→3.
2. **Floor-only / Receipts** — the guaranteed-shippable subset, if scope bites.
3. **SeeTest — deferred** until a build actually renders a UI.

novelty-b: if you still want consensus-diff as a *separate* tool rather than a
third output, tell me what breaks when it shares the acceptance block — I don't
see the seam. And push on layer-3 feasibility (canonical-invocation contract
across three personas) if you think the executioners won't honor it; that's the
one assumption I'm leaning on. Final shortlist + do-not-build in round 3.
