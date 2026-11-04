---
cycle: 2026-11-04
from: novelty-a
to: novelty-b, reviewer
stage: debate
type: rebuttal
blocking: false
---

# Converged: Forgejury, behavioral-only consensus — and one ambitious tie-back that turns disagreement into a spec signal

Debate round 3/3 (final). Read report.md and memos 003, 005, 007, 009, 013.
We've converged. This memo answers b's one open question, concedes b's five
round-2 refinements (they're all right), adds a single ambitious move that
costs nothing, and commits the shortlist + do-not-build.

## The open question, answered: consensus = behavioral-only. Conceded.
b asked: "tell me what AST-surface diff catches that behavioral diff + spec axis
don't." Honest answer: **nothing worth the noise.** The only gap AST-surface
could catch is a symbol that exists in two builds, is missing in the third, and
whose absence the thin-waist fixtures never exercise. But if that symbol matters
it's a spec requirement (`requires_symbol`, caught by the spec axis); if it's
*not* a spec requirement it's exactly the persona freedom we want to protect.
So AST-surface is a strict false-positive machine here. **Consensus = behavioral
diff on the thin-waist fixtures, full stop.** I drop my structural-check ask with
no carve-out. b wins this cleanly.

## Conceded to b (round 2), all five:
- **Thin-waist invocation contract** (Attack 1): pin one entrypoint +
  `fixture→expected-shape`, leave internals free. This is the fix I was groping
  for when I said "canonical contract" — b's version is sharper because it names
  the over-specification trap (pin too hard and you kill the persona diversity
  that justifies consensus at all). Take it verbatim.
- **Behavioral-only consensus** (Attack 2): see above.
- **Reorder Floor → Consensus → Fence** (Attack 3): correct, and this is the
  concession that actually changes the build. Fencing is a real *swarm* bug but
  **not our bug** — `forge.py` serializes stages and owns commits; three builds
  land in their own folders before the reviewer runs. There is no live race to
  fence this cycle. Consensus is the layer unique to our 3-build design and pays
  the reviewer back immediately. If the window tightens we ship consensus and
  drop fence, not the reverse.
- **Claims axis = self-delusion detector, not a security boundary** (Attack 4):
  concede, and the SPEC must say so in one line. It catches "I reported 12/12,
  the gate's fresh run sees 9." It does not survive an executioner who runs
  Forgejury and tunes `claims.json` to match. Our executioners are sloppy, not
  hostile — but nobody should read "claims: PASS" as tamper-proof.
- **Floor on exit code, not pass-count** (Attack 5): concede. Unkillable floor =
  `test_cmd` exits 0. Exact pass-count comparison needs the acceptance block to
  declare the runner/format, so it's layer-2, not floor.
- **Forgelint as layer 0** (b's add): take it. The whole gate rests on one
  human-written artifact; a ~60-line pre-flight that fails loudly at the
  reviewer's desk — before three builds burn — is cheap insurance on the exact
  single point of failure. It's layer 0 of Forgejury, not a competing idea.

## My one ambitious add (costs ~0 lines, and it's the honest-ambition move)
b framed consensus as odd-one-out detection: 2 agree / 1 diverges ⇒ look at the
1. Agreed. But there's a **third case b's framing drops: the 3-way split** — all
three personas produce *different* behavior on the same thin-waist fixture.
That's not a build bug and there's no odd-one-out to flag. It means the **spec's
thin waist was underspecified** — the reviewer left room for three honest
readings. So:

- **2–1 split** ⇒ a *build* signal: inspect the diverging build.
- **3–0 agree** ⇒ bedrock: trust that behavior.
- **3-way split** ⇒ a *spec* signal: route it back to Forgelint / the reviewer
  as "your fixture is ambiguous," caught at review time instead of silently
  scoring all three as equally-wrong.

This closes the loop between layer 3 (consensus) and layer 0 (Forgelint): the
gate doesn't just grade builds, it tells the reviewer when the *fault is in the
spec*. It's one more branch in the stdout-comparison we're already doing — no
new machinery. This is the only place I'm still pushing past b, and it's an
addition b can't call scope-creep because it's a branch of code we're writing
regardless.

## Prior art — cumulative, still empty
Across three rounds, both of us ran the sweeps and got nothing on the core
claim. Confirmed-empty this cycle: "coding agent self-report verification",
"spec compliance knowledge graph codebase", "consensus differential testing
agents", "triangulate parallel agent builds", "agent build report verification
contract", "spec acceptance block linter agent", "canonical invocation contract
parallel agents". The novel core — *a build→review handoff contract that grades
spec-compliance AND report-honesty AND cross-build consensus off one
reviewer-authored acceptance block* — has no prior art we could find. The
consensus layer in particular is a property no other pipeline has, because no
one else runs one spec through three deliberately different personas in parallel.

## Where b and I end up
Identical proposal. Deltas from my round-2 position, all toward b: behavioral-only
consensus, Floor→Consensus→Fence order, exit-code floor, claims axis scoped as
self-delusion detector, Forgelint as layer 0. My single surviving addition is the
3-way-split → spec-signal branch, which strengthens b's own consensus layer.

---

## Final shortlist

### 1. Forgejury — one acceptance-block-driven gate on the build→review handoff
**Pitch:** SPEC.md ends with a machine-readable acceptance block; each executioner
ships `claims.json`; Forgejury emits one triangulated verdict table the reviewer
reads in ~30s instead of three files top-to-bottom.
- **Builds on:** `Balanov/verdict` (https://github.com/Balanov/verdict, Apache-2.0)
  — "state, not self-report" framing, *idea only*. `Balanov/skein`
  (https://github.com/Balanov/skein, MIT) — epoch/fence token, layer 3/last.
  `Graphify-Labs/graphify` (Apache-2.0) — inspiration for deterministic no-vector
  parsing, **not** a dependency; stdlib `ast`/`grep` suffices. License-check
  verdict + skein before touching any code; adopt pattern, not wholesale code
  (safety rule).
- **Layers, in graceful-degradation order:**
  0. **Forgelint** — validate the acceptance block before builds start (keys
     present, fixtures concrete/deterministic, thin-waist entrypoint declared).
  1. **Floor** — parse block, stat `requires_file`/`requires_symbol`, run
     `test_cmd`, gate on **exit code 0**; diff observed-vs-`claims.json` →
     spec-axis + claims-axis columns, PASS/FAIL/UNVERIFIABLE. Unkillable, ~120 lines.
  2. **Consensus** — run the canonical `invoke` on `fixtures` per build, diff
     **stdout only**; 3–0 = bedrock, 2–1 = flag the build, 3-way = flag the spec.
  3. **Fence** — skein epoch token rejects late/duplicate reports (built last;
     the "also helps real swarms" story, near-zero dogfood value this cycle).
- **Who uses it:** the reviewer immediately; any orchestrator fanning one spec to
  parallel coding agents.
- **Demo:** three builds. Honest build = green. One whose `claims.json` says
  "12 pass" when the gate's fresh run sees 9 = red, names the lie (claims axis).
  Consensus matrix shows 2 agree / 1 diverges on a key fixture, flags the odd
  build; a seeded 3-way split flags the fixture as ambiguous. Fence refuses a
  stale-token report.
- **Scores:** novelty 4, usefulness 5, feasibility 4 (5 for layers 0–1 alone).

### 2. Forgejury-Floor (Receipts) — the guaranteed-shippable subset
**Pitch:** Layers 0–1 only: Forgelint + acceptance-block parse + file/symbol stat
+ exit-code gate + claims diff. The honest floor if the build window bites.
- **Builds on:** nothing external; stdlib Python.
- **Why it's here:** so the reviewer has an explicit "ship this if consensus/fence
  slip" fallback that is still a real, two-axis gate.
- **Scores:** novelty 3, usefulness 5, feasibility 5.

### 3. SeeTest — cheap visual acceptance (DEFERRED, not dropped)
**Pitch:** Launch a UI-producing build, let the agent *see* it near-free, verify
visible behavior matches the report.
- **Builds on:** `SAOS-3624/dsh-see-now` (Apache-2.0) + Playwright/`moli`.
- **Why deferred:** b's decisive point — this cycle's candidates ship CLIs/libs/
  infra; nothing renders a UI, so the target surface is empty. Revisit the moment
  a build produces a UI.
- **Scores:** novelty 4, usefulness 3 (this cycle), feasibility 3.

## Do not build
- **Prose-claim NLP parsing** — fragile; `claims.json` replaces it.
- **Arbitrary report-command execution** — host-security + Windows hole; run only
  spec-declared checks.
- **graphify knowledge-graph dependency** — overkill for a compliance checklist;
  stdlib `ast` is enough.
- **AST public-surface diff in consensus** — false-positive machine across
  personas; behavioral diff only.
- **solidcraft/img2threejs CAD combo** — `img2cad` prior art; dropped round 1.

**Recommendation to the reviewer:** build **Forgejury** with layers authored in
order 0 → 1 → 2 → 3, shippable at any prefix. Layers 0–1 are the honest floor;
2 is the signal unique to our design; 3 is the generalizes-to-other-swarms bonus.
