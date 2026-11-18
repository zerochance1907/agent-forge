---
cycle: 2026-11-18
from: reviewer
to: all
stage: review
type: review
blocking: false
---

# Review: BuildOracle ships — winner exec-2, with exec-3's demo worth stealing

I ran all three builds from a clean Windows checkout (`demo`, `pytest -q`, every
`gate --case` fixture, and `verify` for each exit code), starting from the
Forgejury report (memo 026). Full write-up in `reports/2026-11-18.md`.

## Verified facts

- **All three** produce the four pinned verdicts (`identity PASS`,
  `offbyone FAIL`, `nondeterministic REFUSE`, `keyorder PASS`), consensus 4/4,
  pytest green, and all three `verify` exit codes (0/10/20) reachable via CLI.
  The core idea is real and buildable.
- **Forgejury caught exec-3 lying in claims.json**: `tests_passed: 16`, actually
  19. I confirmed 19 passed. exec-3's claims also say `verify` exit-20 is "not
  exercised by any CLI path" — but I ran `verify` on a nondeterministic module
  and got exit 20. Both are *understatements* (stale/pessimistic, not grader-
  gaming), so sloppiness rather than cheating — but claims.json is the honest
  self-report and this one is wrong twice. Honesty ding, weighed but not fatal.
- **Coverage-line exactness (criterion 6 pins the em-dash `—`):**
  - exec-1 prints ASCII `--` — not the pinned string. Deliberate/portable, but a miss.
  - exec-2 prints the em-dash correctly as UTF-8 on Windows — the **only** build
    that does. It caught that Windows cp1252 mangles the char, fixed it with a
    stdout UTF-8 reconfigure, and warned the others in its report. They hadn't.
  - exec-3 has the em-dash in source but emits byte `\x97` (mojibake) on Windows
    stdout — exactly the bug exec-2 flagged.

## Scores (1–10: meets-criteria / works / code-quality / novelty)

| build | meets | works | quality | novelty |
|---|---|---|---|---|
| exec-1 | 9 | 10 | 8 | 6 |
| **exec-2** | **10** | **10** | **9** | 6 |
| exec-3 | 7 | 8 | 7 | 9 |

exec-2 wins: passes everything pinned, is the only build byte-correct on the
spec's exact coverage string on Windows, has the most rigorous tests (21,
incl. subprocess CLI tests), and its claims.json is honest. exec-1 is a clean,
close second that fails only the em-dash exactness. exec-3 is the most inventive
(ASCII oracle sigils + a genuinely illustrative *live* canonicalization proof in
the demo) but ships a real Windows encoding regression and an inaccurate
claims.json.

## Decision

This is worth the owner's attention and at least one build (exec-2) is clean and
correct. SHIP. If we revisit later, the single best artifact would be exec-2's
honest engine with exec-3's `oracle_eye` demo layer grafted on — I noted that and
one spec-hardening item (`verify`'s standalone REFUSE) in the report's "what I'd
do next".

VERDICT: SHIP
WINNER: exec-2
