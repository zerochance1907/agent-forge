---
cycle: 2026-11-11
from: exec-3
to: reviewer
stage: build
type: build-report
blocking: false
---

# exec-3 build report: Preflight, with a blast-radius map that's actually computed, not decorated

Built at `builds/2026-11-11/exec-3/`: `preflight.py`, `tests/test_preflight.py`,
`README.md`, `claims.json`. Stdlib + `git` only, as the spec requires.
`forgejury grade` run from the repo root: **1/1 PASS**, all 6 spec-axis checks
PASS, all 4 claims-axis checks PASS, all 9 consensus fixtures PASS.

## Acceptance criteria

| # | Criterion | Status |
|---|---|---|
| 1 | `tier` prints only the token | Met — `test_tier_stdout_has_nothing_extra` |
| 2 | Precedence table + 9 consensus fixtures | Met — all 9 pass via forgejury, plus 29 extra tier-table cases in `test_broad_tier_table` |
| 3 | `classify` card ends `TIER: <tier>`; `--json` has all 8 fields | Met |
| 4 | File-count enrichment for `DESTRUCTIVE_LOCAL` against working tree | Met — isolated `fixture_repo` pytest fixture (real `git init`, tracked + untracked file), covers whole-dir, single-file, and glob paths |
| 5 | Obfuscation → `UNKNOWN` | Met — 10 cases (`$(...)`, backtick, `|`, `;`, `&&`, `\|\|`, `sh -c`/`bash -c`, `xargs`, `$VAR`, `eval`) |
| 6 | `gate` defaults to pause-everything; `--auto-approve-safe` never touches destructive/external/unknown | Met |
| 7 | README covers install, demo, tier table, flag + safety default, limitations, hook-wiring snippet | Met |
| 8 | `python -m pytest -q` exits 0 | Met — 74 passed |
| 9 | `claims.json` maps acceptance criteria | Met |

I also extended enrichment to `REVERSIBLE_LOCAL` (`mkdir`/`touch`/`cp`) per the
spec's "local-tier" wording in criterion 4's intro paragraph — `uncommitted_at_risk`
is `0` there since creation doesn't put existing work at risk. Git-based local
tiers (`git reset --hard`, `git clean`, etc.) report both fields `null`; scoping
"whole tree" accurately there is explicitly flagged as future work in the README,
not silently skipped.

## The twist (wild-experimentalist persona)

The human-readable card ends with an ASCII "blast radius map" rendered **from
the real card fields**, not a static per-tier icon:
- Local tiers draw a `░` ring sized by `files_affected`, with one `✖` per
  `uncommitted_at_risk` file and one `●` per clean file — more `✖` reads as
  visibly denser danger.
- `EXTERNAL` renders as a ripple leaving the local radius.
- `UNKNOWN` renders as a fog of `?` — refusing to fake a size for the
  unmeasurable case.

It's cosmetic-only and never leaks into `--json` (verified by
`test_classify_json_has_all_eight_fields`, which asserts the exact 8-key set).
Building it surfaced a real cross-platform bug I had to fix: Windows'
default console codec (cp1252) can't print `✖●░🌐`, so `preflight.py` now
reconfigures stdout/stderr to UTF-8 on startup, and the test suite's
subprocess calls decode with explicit `encoding="utf-8"` rather than
inheriting the locale codec. Worth a look by exec-1/exec-2 if they hit mojibake
or `UnicodeEncodeError` on Windows.

I also hit and fixed a correctness bug while wiring the enrichment: `git
status --porcelain` reports paths relative to the **repo root**, not the
caller's cwd — naively joining them against the classify `root` double-prefixes
the path on a non-root working tree and silently reports 0 at-risk files.
Fixed via `git rev-parse --show-toplevel` + absolute-path comparison; covered
by `test_destructive_enrichment_*`.

## Demo

```
$ python preflight.py classify -- rm -rf build
ACTION:  rm -rf build
TIER:    DESTRUCTIVE_LOCAL
REVERSIBLE:  False
NETWORKED:   False
FILES AFFECTED:       2
UNCOMMITTED AT RISK:  2
EXTERNAL SYSTEM:      False
REASONS:
  - leading verb 'rm' destroys local files/data

Blast Radius Map
    ░░░░░░░░░░░░░░░░
    ✖ ✖
    ░░░░░░░░░░░░░░░░
  ✖=2 uncommitted-at-risk   ●=0 tracked/clean

TIER: DESTRUCTIVE_LOCAL
```

```
$ python -m pytest -q
........................................................................ [ 97%]
..                                                                       [100%]
74 passed in 4.23s
```

```
$ python -m forgejury grade builds/2026-11-11/SPEC.md builds/2026-11-11/exec-3
=== Forgejury verdict ===
Summary: 1/1 builds PASS
[exec-3] verdict=PASS
    spec axis:   file:README.md PASS / file:preflight.py PASS /
                 file:tests/test_preflight.py PASS / file:claims.json PASS /
                 symbol:preflight.py::classify_command PASS / test_cmd PASS
    claims axis: files PASS / symbols PASS / test_cmd_exit PASS / tests_passed PASS
=== Consensus (behavioral, stdout-only) ===
  all 9 fixtures: expected-match[exec-3] PASS
```

## Known gaps

- Git-based `DESTRUCTIVE_LOCAL`/`REVERSIBLE_LOCAL` subcommands don't get
  file-count enrichment (documented `null`, not a silent omission).
- `cp` enrichment counts sources only, not whether the destination would
  silently overwrite existing uncommitted work — noted as a simplification,
  not hidden.

## Licenses

No code vendored. Design anchors only: DIYgod/pinky (Apache-2.0),
shanselman/sandbox-mcp (MIT) — both credited in README, no code copied from
either.
