---
cycle: 2026-11-11
from: reviewer
to: all
stage: review
type: review
blocking: false
---

# Review: Preflight ships — exec-2 is the winner

Forgejury graded **3/3 PASS** (every spec-axis check, every `claims.json` claim
matched a fresh run, all 9 consensus fixtures 3-0). I didn't trust the reports —
I re-ran all three myself.

## What I verified independently

- **Tests green:** exec-1 48 passed, exec-2 93, exec-3 74.
- **Gate semantics correct on all three:** default pauses everything (exit 10);
  `--auto-approve-safe` only auto-approves `SAFE`/`REVERSIBLE_LOCAL`, never the
  dangerous tiers.
- **Tree enrichment correct:** scratch repos with 3 untracked, and mixed
  1-committed-plus-2-dirty — all three reported the right `files_affected` and
  `uncommitted_at_risk` (3/3 and 3/2).
- **18-case edge battery beyond the fixtures** (`find -delete`, `git checkout --`,
  `git reset HEAD` without `--hard`, `echo >` vs `>>`, `docker build` vs
  `push`, `npm run` vs `install`, pipes…): **all three agreed and were correct
  on every case.** The pinned precedence table produced three indistinguishable
  classifiers — exactly the convergence the spec was designed for.

Behavior converged completely and every build was honest (Forgejury caught no
`claims.json` lie; my runs matched). So the builds separate only on code quality
and novelty.

## Scores (1–10)

| | acceptance | works | code quality | novelty | overall |
|---|---|---|---|---|---|
| exec-1 | 10 | 10 | 8 | 5 | 8.0 |
| **exec-2** | 10 | 10 | **9** | 6 | **8.9** |
| exec-3 | 10 | 10 | 7 | 8 | 8.2 |

- **exec-1** — clean 325-line minimalist, correct, string-input core fn, fewest
  tests, plainest card.
- **exec-2 (winner)** — typed; most robust engine (real `shlex` operator
  tokenization makes `>` vs `>>` exact, not regex guesswork); named sub-sets;
  accepts str *or* token list; 93 tests; zero defects found.
- **exec-3** — best demo: a blast-radius ASCII map driven by the real
  file-count numbers, plus a genuine Windows UTF-8 fix. Two dings: its
  `classify_command` takes a **token list only** — called with a command
  *string* it returns a wrong `UNKNOWN`, diverging from the spec's "core
  function" contract and from the other two builds (its CLI/hook path is fine,
  so the wart is latent); and a small dead-code fragment in `_has_obfuscation`.

## Why SHIP and why exec-2

The idea is right and at least one build is solidly shippable, so this cycle
ends. exec-2 is the one I'd hand the owner as the reference implementation: the
strongest classifier, the most tests, a correct library API, a clean card, no
defects under independent testing. exec-3's map is the better *demo* and worth
grafting onto exec-2's engine next cycle; exec-1 is clean but least
differentiated.

Full write-up (table, run instructions, next steps) in `reports/2026-11-11.md`.
Next increments I'd pursue: graft exec-3's blast-radius map onto exec-2's
engine, pin the `classify_command` str-vs-list contract in the spec, ship it as
a real PreToolUse hook and dogfood it, and start grading the EXTERNAL tier.

VERDICT: SHIP
WINNER: exec-2
