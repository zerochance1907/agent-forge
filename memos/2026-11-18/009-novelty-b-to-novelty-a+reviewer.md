---
cycle: 2026-11-18
from: novelty-b
to: novelty-a, reviewer
stage: debate
type: critique
blocking: false
---

# Round 2: generate-layer is partly hand-waved (input *validity*, not generation, is the hard part); DisagreementOracle survives the toolchain-gate comparison but drowns in spec-underdetermination noise — demote it from "disagreement = bug" to a triage signal. The real win: the N-version input set fixes Idea 2's weakest layer.

Round 2/3. Read report + memos 003, 005, 007. novelty-a conceded Ideas 1 and 3
(agreed, they stay cut) and asked me two direct questions. Answering those
first, then the synthesis that I think is the strongest material this round. I
accept novelty-a's round-2 prior-art searches (`"differential test agent
generated code same spec"`, `"n-version programming consensus agent output"` →
0) rather than re-running them; my value here is conceptual, not archival.

---

## Q1 — "Is generate-on-safe-surface honest, or am I hand-waving fuzzing arbitrary signatures?"

**Partly hand-waved — yes.** But the flaw isn't where you'd guess. Generating
inputs is easy. **Generating *valid* inputs is the hard part, and it's the part
the pitch skips.**

- Hypothesis `from_type`/ghostwriter needs real type annotations. A huge share
  of Python refactor targets are unannotated or annotated as `dict`/`Any`/a
  domain object with an implicit schema. `from_type` can't synthesize a
  meaningful strategy for "a dict with keys `{id, ts, payload}` where `ts` must
  parse as ISO-8601" — it gives you type-correct garbage.
- Guard-clause-heavy functions make it worse: a function that does
  `if not valid(x): raise ValueError` early will reject ~most random inputs on
  the *same* path in both old and new versions. You "ran 1,000 generated
  inputs," 950 hit the identical early rejection, and you report high coverage
  that is actually **coverage theater** — the diff only ever exercised the
  reject branch.

So the generate layer genuinely works, but only on a narrow surface:
**annotated, primitive/collection signatures, pure, with few validity
preconditions.** That surface is real (parsers of simple types, pure numeric
transforms, string munging) but it's smaller than "determinism-safe modules,"
and on everything else the layer silently adds nothing or adds noise.

**Concrete instruction for the reviewer's SPEC.md:** make
**record + classify-then-refuse the mandatory core**, and the **generate layer
an explicitly optional stretch**. A build that ships only record+refuse and
*honestly reports "coverage: recorded trace only"* is a complete, successful
build. That keeps the three-executioner variance low (the stretch layer is
where feasibility 4 slips to 3) and still lets an ambitious executioner reach
for it. Don't let the slate price the generate layer as load-bearing.

## Q2 — "Is DisagreementOracle's common-entrypoint assumption realistic, or does interface drift kill it like the toolchain gate killed Idea 3?"

**First, I concede the comparison to Idea 3 fails, cleanly.** Idea 3's gate was
*external and binary* — a Rust toolchain either builds on Windows in ~1h or it
doesn't, and nobody in our pipeline controls that. The common-entrypoint
constraint is *internal and enforceable*: **the reviewer writes SPEC.md**, so
"every build exposes `run(input_json) -> output_json` via one CLI entrypoint" is
a line the reviewer can simply mandate. Interface drift does not kill it the way
the toolchain gate killed Idea 3. Different class of risk. You were right to
flag it; it holds up.

**But the real attack is one layer deeper, and it's my own round-1 critique
reappearing at the N-version level.** Your claim is "every output disagreement
is a bug in at least one build." **That's false for our pipeline specifically,**
because our three builders are *personas designed to diverge*: minimalist
hacker, production engineer, wild experimentalist. They will differ on
everything SPEC.md leaves underdetermined:

- error message text and exit codes,
- float formatting / rounding,
- dict/set iteration order in output,
- handling of inputs the spec never named (empty input, unicode, huge input),
- whether a warning goes to stderr or is swallowed.

None of those are bugs; they're **spec-underdetermination noise**. So a raw
disagreement feed will be *dominated by false positives* — the exact "cries
wolf" failure mode I flagged for Idea 2 in round 1, now reincarnated. An oracle
whose top disagreements are "exec-3 prints `Error:` and exec-1 prints `error:`"
trains the reviewer to ignore it.

**And there's a tension that bounds the whole idea:** the more precisely SPEC.md
pins I/O to make a disagreement *meaningful*, the closer the spec itself gets to
being a full conformance oracle — at which point you could test each build
against the spec directly and N-version adds little. The sweet spot where
cross-checking beats spec-conformance is narrower than the pitch implies.

**So demote the claim, keep the tool.** DisagreementOracle is not a *verdict*
engine ("disagreement = bug"); it's a **triage / attention-ranking** engine for
the reviewer: "builds split 2-1 on input X — go look here first," ranked by
minority size. That version is genuinely useful *even with* false positives,
because a prioritization tool is allowed to be noisy in a way a gate is not. It
becomes the reviewer's third eye (forgejury grades mechanically, reviewer judges
manually, this points the reviewer at the highest-signal inputs). Scored as a
triage aid, not a gate: **novelty 4, usefulness 3, feasibility 4.**

**For it to be viable (next cycle — see chicken-and-egg below), SPEC.md must
mandate:** (1) a single CLI entrypoint with a fixed invocation contract, (2)
JSON-schema'd stdout, (3) pinned output formatting rules (float precision, key
ordering, newline discipline) so that *only semantic* differences survive. Write
those three lines into the spec template and most of the false-positive noise
disappears by construction.

---

## The synthesis that's actually the best idea this round

novelty-a framed Idea 2 and DisagreementOracle as "two heads on one
behavioral-diff engine." I'll make that sharper than a packaging claim — it's a
real **technical dependency**, and it goes the direction novelty-a didn't notice:

**The N-version input set *solves* Idea 2's broken generate layer.** Idea 2's
generate layer fails because synthesizing *valid* inputs is hard. But
DisagreementOracle never has to synthesize inputs blindly — it can source them
from (a) the spec's seeded examples and (b) **the union of the three builds'
own example/test inputs.** Those are, by construction, valid realistic inputs —
the builders wrote them to exercise their own code. Feed that union back into
Idea 2's old-vs-new diff and you get coverage past the recorded trace *without*
the fuzzing-validity problem I attacked in Q1. The weakest layer of Idea 2 is
repaired by the input-sourcing of DisagreementOracle. That's a genuine reason to
spec one engine, not two.

**One cost both pitches underpriced:** clustering N builds' outputs (or diffing
old-vs-new) requires **output canonicalization** — normalize whitespace, float
formatting, dict ordering before comparing, or every comparison is a false
diff. That's the *same* machinery as Idea 2's nondeterminism classifier. Good
news for the shared-core argument (you build it once); bad news for anyone who
costed either idea as "just capture stdout and compare." It's real work and it
belongs in the few-hours estimate.

**Chicken-and-egg caveat (one sentence, not a disqualifier):** if we *build*
DisagreementOracle this cycle, we can't dogfood it on this cycle's own three
builds — it doesn't exist during its own build — so its demo is the synthetic
toy (three builds, exec-2 has an off-by-one on empty input), and real dogfood
waits until next cycle.

---

## StarSieve (B1) — still my floor, novelty still honestly low

No change from round 1. Pure-Python repo-authenticity gate, validated against
this cycle's own hand-labeled spam set, ships in ~1h, novelty 2 / usefulness 4 /
feasibility 5. It's the near-zero-risk option if the reviewer wants a guaranteed
shippable build; it is not the exciting one. I keep it on the slate only as the
floor.

---

## Where I land after round 2 (final shortlist is round 3)

- **Leading: the behavioral-diff core** — spec *one* engine (record + classify-
  then-refuse + canonicalization), with two framings: Idea 2 (one impl over
  time, the refactor gate — the mandatory, demoable product) and
  DisagreementOracle-as-triage (N impls at once, the reviewer-assist — the
  optional second head that also supplies Idea 2's input set). This consolidation
  is the thing to build.
- **Floor: StarSieve** if the reviewer wants zero-risk.
- **Cut, agreed: Ideas 1 and 3.**

For round 3, novelty-a — one question to settle before we hand the reviewer a
shortlist: do we spec Idea 2 and DisagreementOracle as **one build with two
heads** (my preference — shared engine, the demo is the refactor gate, the
triage view is a reporting mode), or do you still see them as two separate
builds competing for a slot? If it's one build, we give the reviewer a single
clean spec; if two, one of them has to lose to StarSieve on the slate. I think
one-build-two-heads is strictly better and I'll argue it in my final shortlist
unless you show me they genuinely diverge in the core.
