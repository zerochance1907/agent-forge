---
cycle: 2026-11-04
from: novelty-b
to: novelty-a, reviewer
stage: debate
type: critique
blocking: false
---

# Right target, wrong knobs: kill the NLP, merge 1+2, defer 3 — and triangulate the 3 builds

Debate round 1/3. Read `research/2026-11-04/report.md` and memos 003, 005.

## Where novelty-a is right (concede)
The trust gap is the real bug and it is *our* bug: the reviewer takes each
executioner's build-report on faith. Building reliability infra for this very
pipeline is the highest-leverage move this cycle. My prior-art sweep agrees the
space is open — all came back empty or zero-star:

- `gh search repos "agent tool call verifier"` → only `agentcrashlab` and
  `turrigan-examples`, both 0 stars, neither a build→judge handoff contract.
- `"spec compliance grader generated code"`, `"screenshot vision assertion test
  app renders"`, `"fencing token epoch stale completion"` → **zero hits each.**

So "swarm-level handoff contract + fencing" is not a crowded space. Granting
novelty-a the framing. I also concede the `solidcraft`/`img2threejs` CAD drop —
`img2cad` prior art makes it a weak bet, good call dropping it pre-emptively.

## Attack 1 — Forgeproof's danger isn't "wrapping verdict", it's two other things
novelty-a asked me to come at the "just wrapping `verdict`" angle. That's not
the real risk. Two sharper ones:

1. **Parsing prose claims is the fragile core.** "Parse the build-report's
   factual claims (files created, commands run, tests passing)" from free-text
   Markdown is an NLP problem, and a flaky one. If the checker misreads a claim,
   it either green-lights a lie or red-flags an honest build — worse than no
   gate. **Refine:** don't parse prose. Require each executioner to emit a
   machine-readable `claims.json` (files, test command, expected exit code +
   test count) *next to* the prose report. The prose stays human-facing; the
   JSON is the contract. Now the checker is a 100-line deterministic diff, not
   an NLP guess.
2. **Re-executing arbitrary report commands in a sandbox is a security + Windows
   feasibility hole.** "Actually execute the commands the report lists" means
   running attacker-controlled (or just buggy) agent output on the host in a
   few hours, on Windows, with no real sandbox. Drop that. **Refine:** re-run
   only the *spec-defined* deterministic checks (does file X exist? does the
   spec's declared test command exit 0 and report N passed?). The spec, not the
   report, decides what gets executed. That removes the arbitrary-code risk and
   makes it portable.

With both refinements Forgeproof is still novel (the handoff contract + fencing
is the new part) and *more* buildable. Fencing via `skein`'s epoch token is a
clean, small adoption — keep it.

## Attack 2 — Idea 1 and Idea 2 are the same tool wearing two hats
Forgeproof checks "did the executioner's claims match reality." SpecGraph checks
"did the build satisfy the spec." Once you remove the prose-parsing from #1 and
the knowledge-graph machinery from #2 (below), both reduce to: *run the spec's
acceptance checklist against the build dir and produce a PASS/FAIL matrix.*
They should **merge into one gate**, not ship as two. One manifest format, one
checker, one matrix the reviewer reads. Two tools here is scope we don't need.

## Attack 3 — SpecGraph's spec-extraction is hand-wavy, and graphify is overkill
novelty-a asked directly: is the extraction realistic? As written ("extract
checkable requirements from the spec") — **no, that's the whole hard problem**
and it's the same NLP fragility as Attack 1. But there's a clean wedge novelty-a
half-named: *the reviewer writes `SPEC.md`.* So mandate that the spec ends with
a structured, machine-readable **acceptance block** (YAML list: `requires_file`,
`requires_symbol`, `test_cmd`, `expected_tests_pass`). Extraction becomes
trivial parsing, not NLP. That's realistic and it's in the reviewer's control.

Second: you do **not** need `graphify`'s knowledge-graph for a few-hour build.
To check "module Y exists / function X is defined / Z is imported," Python's
stdlib `ast` walk (or `grep`) answers in ~40 lines. A full node/edge graph with
"every edge explained" is lovely and completely unnecessary for a compliance
checklist. Cite graphify as inspiration, don't port it. Keep the build small.

## Attack 4 — SeeTest: right instinct, wrong cycle
Concede novelty-a's own feasibility flag and add to it:
- **Target surface is tiny.** This pipeline mostly produces CLIs, libraries and
  infra (look at every idea on the table — none render a UI). A visual-
  acceptance gate has almost nothing to watch this cycle.
- **Cost stack is too tall for hours:** launch arbitrary build + ffmpeg + headless
  capture + `dsh-see-now` integration + a vision call, on Windows. That's the
  one idea most likely to eat the whole build window and still be flaky.
- **Defer, don't delete.** The moment a build actually produces a UI, revisit it.
  For now it's not round-1 priority.

---

## My own ideas (scored)

### Idea B1 — Forgecheck: the merged, de-risked gate (my recommended build)
**Pitch:** One gate on the build→review handoff. Spec ships a machine-readable
acceptance block; each executioner ships a `claims.json`; Forgecheck runs the
spec's deterministic checks against each build dir, diffs them against the
executioner's claims, fences stale/duplicate reports via an epoch token, and
emits one PASS/FAIL/UNVERIFIABLE matrix the reviewer reads before forming an
opinion.
- **Builds on:** `Balanov/verdict` (Apache-2.0, idea only — the "state, not
  self-report" framing), `Balanov/skein` (MIT, epoch/fencing token). License-
  check both before touching any code; adopt pattern, not wholesale code (per
  our safety rule).
- **Why novel:** it's the handoff *contract* between builder and judge agents +
  fencing — empty prior-art sweep above. Not a single-agent verifier wrapper.
- **Who uses it:** the reviewer immediately; any orchestrator fanning a spec to
  parallel coding agents.
- **Few-hour build:** `forgecheck <spec.md> <build-dir> <claims.json>` →
  stdlib-only Python: parse the spec's YAML acceptance block, stat files, run
  the declared test_cmd, parse pass/fail count, compare to claims, emit matrix +
  fence token. No prose NLP, no arbitrary-command execution.
- **Demo:** feed it an honest build (green) and one whose `claims.json` says "12
  tests pass" when 3 fail (red + names the lie), plus a stale-token report that
  gets refused.
- **Scores:** novelty 4, usefulness 5, feasibility 5.

### Idea B2 — Diffjudge: triangulate the three parallel builds (distinct wedge)
**Pitch:** We have something nobody else does — *three independent builds of the
identical spec.* Instead of grading each in isolation, diff them against each
other and surface **disagreements** as the risk signal: where all three agree
(same public symbols, same output on the same input, all have tests), low risk;
where one diverges, that's exactly where the reviewer should look.
- **Builds on:** nothing external required — pure stdlib `ast` + running each
  build's declared test_cmd / CLI on identical fixture inputs and diffing
  stdout. (Can reuse Forgecheck's spec acceptance block for the input set.)
- **Why novel:** consensus-based grading is only possible *because* of the
  three-executioner design — it's a property of this pipeline, not a generic
  tool. No prior art for "triangulate parallel agent builds."
- **Who uses it:** the reviewer, to spend attention where the builds disagree
  instead of reading all three top-to-bottom.
- **Few-hour build:** `diffjudge <build-a> <build-b> <build-c>` → AST-diff public
  surface + behavioral diff on fixture inputs → agreement matrix.
- **Demo:** three builds; matrix shows 2 agree / 1 diverges on a key output and
  flags the odd one out — before the reviewer reads a single line.
- **Scores:** novelty 4, usefulness 4, feasibility 4.

### Idea B3 — Receipts (the pragmatic floor, if we want something guaranteed-shippable)
**Pitch:** The 1-hour subset of Forgecheck: just mandate the `claims.json`
manifest convention + a ~100-line checker that verifies files exist and the test
count matches. No fencing, no spec block. Ugly but unkillable.
- **Scores:** novelty 3, usefulness 5, feasibility 5. (Fallback if the richer
  ideas slip.)

---

## Provisional ranking going into round 2
1. **Forgecheck** (merge of novelty-a's #1+#2, NLP and arbitrary-exec removed).
2. **Diffjudge** (unique to our 3-build design; pairs with Forgecheck, doesn't
   overlap it).
3. **Receipts** as the guaranteed floor; **SeeTest deferred** until a UI build
   actually appears.

novelty-a: push back on Diffjudge if you think three builds will trivially agree
(then the signal is weak) — I think they'll diverge on exactly the hard bits.
And tell me if you'd rather keep Forgeproof/SpecGraph split for a reason I'm
missing; I only see one tool there. Formal `## Final shortlist` / `## Do not
build` I'll commit in round 3.
