---
cycle: 2026-11-11
from: exec-1
to: reviewer
stage: build
type: build-report
blocking: false
---

# Build report: Preflight (exec-1, minimalist hacker)

One file, stdlib-only, zero vendored code. `builds/2026-11-11/exec-1/`:
`preflight.py` (~290 lines), `tests/test_preflight.py` (48 cases), `README.md`,
`claims.json`. No `vendor/`, no third-party runtime dependency — `pytest` is
dev-only, for the test suite.

## Acceptance criteria — met / partial / not met

1. **Met.** `tier` prints exactly the tier token + newline, nothing else.
2. **Met.** Precedence table implemented as ordered `if`-chain
   (`classify_tier`); all 9 consensus fixtures pass under forgejury (see below).
3. **Met.** `classify` card ends in `TIER: <tier>`; `--json` emits all 8 fields.
4. **Met.** `files_affected`/`uncommitted_at_risk` computed for the local-tier
   path verbs (`rm, rmdir, mv, dd, truncate, shred, mkdir, touch, cp`) via glob
   expansion + `git status --porcelain`; `null` for everything else. Caught and
   fixed a real bug here during build: `git status --porcelain` reports paths
   relative to the **repo toplevel**, not the invocation cwd — when Preflight
   runs from a subdirectory of a larger repo (as it will in practice, e.g. this
   very worktree), naively comparing against cwd-relative paths silently
   produced `uncommitted_at_risk: 0` for files that were in fact untracked. Fixed
   by resolving `git rev-parse --show-toplevel` and comparing absolute paths
   against that. Also handled git's collapsing of a wholly-untracked directory
   into a single `dir/` line (prefix match). Regression-tested both the
   repo-root and nested-subdir cases.
5. **Met.** All 9 obfuscation triggers (`$(`, backtick, `${`, pipe, `;`, `&&`,
   `eval`, `sh -c`, unresolved `$VAR`, `xargs`) classify `UNKNOWN`.
6. **Met.** `gate` defaults to `PAUSE <tier>` / exit 10 on everything.
   `--auto-approve-safe` only auto-approves `SAFE`/`REVERSIBLE_LOCAL`;
   `DESTRUCTIVE_LOCAL`/`EXTERNAL`/`UNKNOWN` always pause, flag or not.
7. **Met.** README covers install/run, demo, full tier table, the
   `--auto-approve-safe` flag and its pause-by-default safety law, the three
   documented limitations (EXTERNAL ungraded, bounded grammar, no
   symlink/alias/variable resolution), and the PreToolUse hook-wiring snippet
   (documented, not built, per spec).
8. **Met.** `python -m pytest -q` → 48 passed. Covers the 9 consensus
   fixtures, all 9 obfuscation cases, 20 extra tier-table fixtures (git
   subcommands, redirects, `find -delete`, every EXTERNAL verb family), CLI
   surface (stdout purity, card/JSON, gate exit codes), and file-count
   enrichment against a real temporary git fixture repo from both repo-root and
   nested-subdir cwd.
9. **Met.** `claims.json` maps all 9 criteria, `test_cmd_exit: 0`,
   `tests_passed: 48`.

## Demo (real output)

```
$ python preflight.py classify -- rm -rf build
Command: rm -rf build
Tier: DESTRUCTIVE_LOCAL
Reversible: no
Networked: no
Files affected: 3
Uncommitted at risk: 3
External system: no
Reasons:
  - leading verb 'rm' (or output-truncating redirect) is destructive to the local tree
TIER: DESTRUCTIVE_LOCAL
```

(run against a scratch fixture repo with `build/{a,b,c}.txt` untracked)

```
$ python -m pytest -q
................................................                         [100%]
48 passed in 2.84s
```

## Forgejury (ran it myself before finishing, as instructed)

```
python -m forgejury grade builds/2026-11-11/SPEC.md builds/2026-11-11/exec-1
=== Forgejury verdict ===
Summary: 1/1 builds PASS
[exec-1] verdict=PASS  (all spec-axis and claims-axis checks PASS)
=== Consensus === all 9 fixtures PASS
```

One environment note for the reviewer: `python -m pytest -q` requires `pytest`
on whatever `python` the grading step resolves to — it was **not** preinstalled
in this worktree's system Python, so I ran `pip install --user -q pytest`
before grading. If your grading environment also lacks it globally, the same
step will be needed there; nothing in my build depends on this beyond running
the test suite.

## Known gaps

- File-count enrichment is literal/glob-only, as the spec allows — a path
  behind an unresolved variable or inside a non-local verb (e.g. `git clean`)
  correctly reports `null` rather than guessing.
- `mv`/`cp` count both source and destination argument matches toward
  `files_affected` (doesn't distinguish "being read" from "being destroyed");
  not spelled out further in the spec, didn't gold-plate it.
- No hook implementation (out of scope per spec) — README documents the
  wiring only.

## Licenses

No code vendored. `pinky` (Apache-2.0) and `sandbox-mcp` (MIT) cited in README
as design-anchors-only, per spec.
