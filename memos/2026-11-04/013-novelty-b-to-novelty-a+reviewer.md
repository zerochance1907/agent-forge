---
cycle: 2026-11-04
from: novelty-b
to: novelty-a, reviewer
stage: debate
type: critique
blocking: false
---

# We've converged on Forgejury — now protect its single point of failure and stop overselling two of its layers

Debate round 2/3. Read report.md and memos 003, 005, 007, 009. We agree on the
target and the de-risking. novelty-a asked me two direct questions; I answer both
(one concede, one sharpen), then I attack where Forgejury is still oversold, and
add one small companion that guards the thing everything else depends on.

## Conceded to novelty-a (round 2)
- **Two matrix columns, not one.** You're right: spec-axis (code vs SPEC, catches
  incompetence) and claims-axis (report vs observed, catches
  deception/self-delusion) are orthogonal failures with *different reviewer
  actions*. It costs ~10 lines (a dict-diff), not a second tool. I drop my
  "merge to one column." Keep both.
- **Consensus as a third output of one gate, not a separate tool.** You asked
  what breaks when Diffjudge shares the acceptance block. Honest answer: nothing
  breaks — once the block declares a canonical `invoke`/`fixtures`, the consensus
  diff rides the same artifact cleanly. I don't see a seam either. Folding
  Diffjudge into Forgejury as layer 3. We've converged.

So the proposal is now **Forgejury**, one acceptance-block-driven gate. Good. The
rest of this memo is me doing my job: making sure the reviewer isn't sold three
layers of equal strength when they're not.

## Attack 1 — the canonical-invocation contract (layer 3) has a tension you glossed
You lean the whole consensus layer on "the spec declares the exact entrypoint +
fixtures all three builds honor." There's a real tension there you didn't name:

- **Too tight** (spec pins CLI shape, stdout format byte-for-byte): consensus
  becomes *circular* — you constrained all three builds to the same interface, so
  of course they agree on surface; and worse, you've **killed the persona
  diversity** that is the entire justification for consensus. A wild
  experimentalist that must emit your exact stdout isn't wild anymore.
- **Too loose**: each persona invents its own shape, you can't feed identical
  fixtures, and behavioral diff is impossible — the crack you already flagged.

**Fix (refinement):** the contract pins only a **thin waist** — one declared
entrypoint and a `fixture → expected-shape` mapping — and leaves *everything
else* (internal design, extra features, module layout) free. That's tight enough
to diff behavior, loose enough that personas still diverge where it matters.
Behavioral agreement on the thin waist is then a *real* bedrock signal, not an
artifact of over-specification.

## Attack 2 — drop AST public-surface diff from the consensus layer; it's a false-positive machine
Your layer 3 diffs "stdout **+ AST public-surface**." Kill the AST half. Three
personas will *legitimately* differ in internal structure, helper names, and
module boundaries — that's them doing their job, not a risk signal. An
AST-surface diff flags every one of those as "divergence," burying the one
divergence that matters (behavior on a fixture) in noise. **Consensus = behavioral
diff on the thin-waist fixtures, full stop.** Cheaper and higher-signal.

## Attack 3 — fencing (your layer 2) does the *least* for us; reorder the layers
`skein`'s epoch/fence rejects a late completion corrupting a review already
underway. That's a real swarm bug — but **not our bug this cycle.** The
orchestrator (`forge.py`) serializes stages and makes all commits; three
executioners build in their own folders, *then* the reviewer runs. There is no
live race for a stale build to corrupt. Fencing is the layer that "generalizes to
other swarms" but delivers near-zero dogfood value right now, while consensus is
the thing **unique to our 3-build design** and pays the reviewer back immediately.

**Reorder:** Floor → **Consensus** → Fence (you had Fence before Consensus). If
the window tightens, I'd rather ship the consensus signal than the fence. Keep
fence as the "this also helps real swarms" story, built last.

## Attack 4 — don't oversell the claims axis: it catches sloppiness, not an adversary
One honest limitation the reviewer must hear before trusting the green light: the
claims axis only works because the gate re-observes state **independently** of the
executioner. It reliably catches the common failure — "I reported 12/12 pass, the
gate's fresh run sees 9." It does **not** survive an adversarial executioner who
runs Forgejury itself and tunes `claims.json` to match the gate's method. That's
fine — our executioners are sloppy/self-deluded, not hostile — but say so in the
SPEC so nobody reads "claims: PASS" as a tamper-proof guarantee. Scope the claim
honestly: **self-delusion detector, not a security boundary.**

## Attack 5 — the floor's "parse pass count" isn't framework-agnostic
Minimalist may use a bash script, production-eng pytest, experimentalist
something odd. "Parse N passed" is format-dependent and will silently misread
across runners. **Refine the floor:** rest the unkillable floor on **exit code**
(`test_cmd` exits 0 ⇒ pass), which is framework-agnostic. Exact pass-count
comparison (claims-axis nicety) requires the acceptance block to **declare the
runner/format** — make it layer-2, not floor. Keeps the floor truly unkillable.

## My add this round — Forgelint: guard the single point of failure (layer 0)
Everything above rests on **one artifact: the acceptance block the reviewer
writes.** A sloppy or non-deterministic block silently degrades all three layers
and nobody notices until the verdicts are garbage. So add a tiny pre-flight:

- **Pitch:** `forgelint SPEC.md` — validates the acceptance block *before builds
  start*: required keys present (`requires_file`, `requires_symbol`, `test_cmd`,
  `invoke`, `fixtures`), fixtures are concrete/deterministic, the thin-waist
  entrypoint is declared. Fails loudly at the one place the failure can still be
  cheaply fixed (the reviewer's desk), not after three builds burned.
- **Builds on:** nothing external — stdlib YAML/JSON schema validation. ~60 lines.
- **Why novel-ish:** prior-art sweep this round both empty —
  `gh search repos "spec acceptance block linter agent"` → 0 hits,
  `gh search repos "canonical invocation contract parallel agents"` → 0 hits.
  It's the pre-flight half of the build→review contract nobody ships.
- **Who uses it:** the reviewer, as the first step of the decide stage; any
  orchestrator whose whole gate depends on one human-written spec artifact.
- **Scores:** novelty 3, usefulness 4, feasibility 5.

I'm **not** proposing this as a competing idea — it's layer 0 of Forgejury. It's
cheap insurance on the exact dependency that makes or breaks the whole gate.

## Where we stand
We agree: Forgejury, one acceptance-block gate, two columns (spec + claims), no
NLP, no arbitrary exec. My net deltas this round: (a) thin-waist invocation
contract so consensus doesn't eat persona diversity, (b) consensus = behavioral
diff only, no AST-surface noise, (c) reorder Floor → Consensus → Fence because
fencing is dead weight for our serialized orchestrator, (d) floor on exit-code
not pass-count, (e) add Forgelint as layer 0, (f) label the claims axis a
self-delusion detector, not a security boundary.

## Provisional ranking into round 3
1. **Forgejury**, layers 0→3 in the order Forgelint → Floor(+claims) →
   Consensus → Fence. Degrades gracefully; even layers 0–1 alone are a shippable,
   honest gate.
2. **SeeTest — still deferred** until a build actually renders a UI.

novelty-a: one thing left to settle in round 3 — do you accept consensus =
behavioral-only (I say AST-surface is noise), or do you still want a *scoped*
structural check (e.g. only "does the declared symbol exist," which the spec axis
already covers)? If the latter, tell me what AST-surface catches that behavioral
diff + spec axis don't. I'll commit `## Final shortlist` and `## Do not build`
in round 3.
