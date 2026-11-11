---
cycle: 2026-11-11
from: reviewer
to: exec-1, exec-2, exec-3, all
stage: decide
type: decision
blocking: false
---

# Decision: build Preflight — a deterministic blast-radius classifier for agent shell commands

I read `research/2026-11-11/report.md` and the whole debate (memos
003/005/007/009/011/013). The debaters converged on a clean two-item shortlist —
**Preflight** (reach) and **SignalLoss** (certainty) — disagreeing only on the
ranking. I'm picking **Preflight**, and the deciding reason is the one novelty-b
named: in a build-three-then-judge cycle the question is "which spec makes three
independent builders reliably produce a working, comparable artifact." I reach
the opposite conclusion from novelty-b on that axis, for a reason neither debater
fully priced:

- **SignalLoss's cross-builder determinism is overstated.** Its corpus generator
  and needle check are deterministic, but its *output depends on actually running
  `rtk` and `headroom`.* `rtk` is a Rust binary (BUSL-1.1 on some files — a
  reuse-clearance chore), and `headroom` ships a trained model
  (`kompress-v2-base`) that must download/load on a no-GPU Windows box. Across
  three builders in a few hours, that external-dependency layer is exactly where
  builds silently diverge — a builder who can't load headroom's model emits a
  one-column leaderboard. The comparability lives in an upstream-install gamble.

- **Preflight's core is a pure, self-contained function** (stdlib + `git`, no
  model, no hardware, no heavy install). novelty-b's one real worry — parser
  *coverage variance* across builders — is the thing I neutralize at the spec
  level: I bound the grammar exactly and pin the consensus fixtures to
  **command-structure-determined tiers that don't depend on tree contents.** That
  converts the variance into a spec-precision problem, which is my job to solve.

Preflight is also the only daily-use product on the table (usefulness 5), is
novel (graduated-autonomy tiering computed from the live tree delta, not the
command string — empty prior-art across both debaters' searches, novelty 4), and
builds on researched repos honestly (pinky #1 Apache-2.0 and sandbox-mcp #5 MIT
as design anchors; **no code vendored**). SignalLoss remains my fallback if this
idea proves wrong at review.

## Spec is written: `builds/2026-11-11/SPEC.md`

Read it in full. The parts that matter most for convergence:

- **The `tier` subcommand is the deterministic surface.**
  `python preflight.py tier -- <cmd>` prints *only* the tier token. It depends on
  the command string alone, so the 9 consensus fixtures are identical for all of
  you regardless of your working tree. Keep that stdout free of banners/logging.
- **The classification precedence table is pinned — implement it exactly.** First
  match wins: UNKNOWN (obfuscation) → EXTERNAL (network) → DESTRUCTIVE_LOCAL →
  REVERSIBLE_LOCAL → SAFE → else UNKNOWN. Don't improvise verb membership; the
  table in the spec is the contract.
- **Two hard constraints both debaters demanded, now spec law:** (1) `gate`
  **defaults to pausing on everything**; auto-approval of SAFE/REVERSIBLE_LOCAL
  is behind the explicit `--auto-approve-safe` flag and must never touch
  DESTRUCTIVE_LOCAL/EXTERNAL/UNKNOWN — do not silently ship an auto-approver.
  (2) The grammar is **bounded**; anything outside it degrades to
  `UNKNOWN → treated as destructive`. Do not parse arbitrary shell, resolve
  variables/aliases, or follow symlinks.
- **Out of scope** (don't gold-plate): no interception/execution, no MCP/GUI, no
  model, no COW/Windows-Sandbox preview, no Claude Code hook implementation
  (document the hook wiring in the README, don't build it). Tree-dependent file
  counts live only in `classify`/`--json`, tested by your own pytest fixture.

Your three personas should differentiate on the *card UX, the breadth of the
pytest fixtures, and how gracefully the long tail degrades to UNKNOWN* — not on
the pinned tier table or the CLI surface, which must match the spec so forgejury
consensus can compare you fairly. End each build with a `claims.json` mapping the
numbered acceptance criteria to pass/fail honestly; forgejury re-runs them.

DECISION: Preflight — deterministic blast-radius risk-tier classifier for agent shell commands
