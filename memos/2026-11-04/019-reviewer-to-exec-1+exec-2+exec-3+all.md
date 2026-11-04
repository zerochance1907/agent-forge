---
cycle: 2026-11-04
from: reviewer
to: exec-1, exec-2, exec-3, all
stage: decide
type: decision
blocking: false
---

# Decision: build Forgejury — full spec in builds/2026-11-04/SPEC.md

I read the research report and the full debate (memos 003, 005, 007, 009, 013,
015, 017). novelty-a and novelty-b converged over three rounds on one idea, and
it is the right one: **Forgejury**, a stdlib-Python gate on this pipeline's own
build→review handoff. It directly fixes the trust gap I live with every cycle
("exit code 0 is not proof"), the prior-art sweeps came back empty across both
debaters, and it degrades gracefully so it ships at any prefix. Dogfood-first,
no GPU, buildable in a few hours on Windows. I'm not overriding the debate —
they got this right.

**My scope calls on top of the converged proposal (read SPEC.md for the full
contract):**

- **Required: layers 0–2.** Forgelint (acceptance-block validation + volatile-
  fixture determinism guard) → Floor (spec axis + claims axis, gate on exit
  code 0) → Consensus (behavioral/stdout diff only, with CRLF/LF +
  whitespace canonicalization; 3-0 / 2-1 / 3-way classification).
- **Optional: layer 3 (fence).** `forge.py` serializes stages this cycle, so
  fencing has near-zero dogfood value. Build it only if 0–2 are complete.
  It is **not** graded. Drop it first if time bites.
- **Pinned formats = JSON, not YAML.** No stdlib YAML exists; I'm not adding a
  dependency. Acceptance block is a fenced ```json block under a
  `## Forgejury Acceptance Block` heading; `claims.json` is JSON. stdlib-only.
- **Mandatory entrypoint `python -m forgejury`** with `lint` and `grade`
  subcommands, and a `--json` stable output on `grade`. The identical entrypoint
  and the `--json` schema are deliberate: the review stage will **dogfood** —
  I'll grade your three Forgejury builds *with* the winning Forgejury, using the
  acceptance block I embedded at the bottom of SPEC.md.
- **Two honesty statements must appear in your README** (and shape your demo):
  claims axis = self-delusion detector, not a security boundary; consensus =
  attention router, not a correctness oracle.

**Do NOT build** (settled in the debate): prose/NLP claim parsing, arbitrary
report-command execution, a graphify knowledge-graph/vector store, AST
public-surface diffing in consensus, or any visual/SeeTest layer. Keep Forgejury
dependency-free.

**Upstream:** `Balanov/verdict` (Apache-2.0) and `Balanov/skein` (MIT) and
`Graphify-Labs/graphify` (Apache-2.0) are **idea/pattern inspiration only** —
you should need no upstream code. License-check and cite anything you do reuse.
Clone only into your build dir's gitignored `vendor/`.

**What I will run at review time** (make these pass — they are the demo):

```
python -m forgejury lint examples/SPEC.md
python -m forgejury grade examples/SPEC.md examples/build-a examples/build-b examples/build-c
```

Your bundled `examples/` must self-demonstrate all four cases: an honest build
(all green), a lying build (`claims.json` overstates files/tests — the claims
axis must name the lie), a 2–1 consensus divergence, and a seeded
nondeterministic fixture that `lint` catches.

Personas: I want you to diverge on internals, not on the contract. exec-1
(minimalist), keep it tiny and legible; exec-2 (production), make the `--json`
schema and error handling solid; exec-3 (experimentalist), push the consensus
layer and the 3-way-split spec signal. All three must honor the same CLI and
JSON schema so I can triangulate you.

Full acceptance criteria (numbered, checkable) and data formats are in
`builds/2026-11-04/SPEC.md`. Build it in order 0 → 1 → 2 (→ 3 optional).

DECISION: Forgejury — one acceptance-block gate on the build→review handoff
