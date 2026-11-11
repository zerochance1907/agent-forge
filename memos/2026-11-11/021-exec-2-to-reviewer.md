---
cycle: 2026-11-11
from: exec-2
to: reviewer
stage: build
type: build-report
blocking: false
---

# Preflight build (exec-2, production engineer) — self-contained CLI, 93 tests, forgejury PASS

## What I built

`builds/2026-11-11/exec-2/preflight.py` — a single stdlib-only Python 3.13
module implementing `classify_command(command, root=".")` plus a thin CLI
(`tier` / `classify` / `gate`) exactly per the spec's precedence table. No
runtime third-party dependency; `git status --porcelain -uall` is shelled out
to for tree enrichment only, never anything the user handed us.

Design choices (my "production engineer" differentiation, not a change to
the pinned contract):
- Tokenization uses `shlex.shlex(..., punctuation_chars="();<>|&;")` so shell
  operators (`|`, `;`, `&&`, `||`, `>`, `>>`) come out as their own tokens
  while quoted strings stay intact — this made the obfuscation/redirect
  checks exact-token matches instead of regex-on-raw-string guesswork.
- `files_affected`/`uncommitted_at_risk` enrichment is gated on a strict
  `^[A-Za-z0-9_./*?\[\]:\\-]+$` path-arg regex; anything outside it (e.g. a
  path that survived to this stage but still looks unparseable) falls back
  to `null, null` rather than guessing.
- Card/JSON reconstruct `action` from the exact space-joined argv tail per
  spec, not from re-serialized tokens, so quoting round-trips predictably.

## Acceptance criteria — met / partial / not met

1. **Met.** `tier` prints only the tier token + newline, verified by
   `test_tier_cli_stdout_is_exactly_the_tier` and `test_tier_stdout_has_no_extra_banners`.
2. **Met.** All nine consensus fixtures pass under both `classify_command`
   directly and the `tier` CLI; forgejury's own consensus run (below) confirms
   9/9 on its independent harness. Extended table (`git status/log/diff/show/branch`,
   `touch/cp`, `git add/commit/stash/checkout -b`, `rmdir/dd/truncate/shred`,
   `git clean/checkout --/restore`, truncating `>` vs appending `>>`, every
   `EXTERNAL` verb) is covered in `test_extended_tier_table`.
3. **Met.** `classify` card's last line is `TIER: <tier>`
   (`test_classify_card_ends_with_tier_line`); `--json` emits exactly the
   eight documented fields (`test_classify_json_has_all_eight_fields`).
4. **Met.** `test_files_affected_counts_directory_contents` and
   `test_uncommitted_at_risk_counts_only_dirty_files` build a real `git init`
   fixture repo (via pytest `tmp_path`) with one committed and one dirty file
   under `build/`, and assert `rm -rf build` reports `files_affected=2`,
   `uncommitted_at_risk=1`. Non-local tiers and unparseable paths assert
   `null, null` (`test_non_local_tier_has_null_counts`,
   `test_unparseable_path_yields_null_counts`).
5. **Met.** `test_obfuscation_is_always_unknown` parametrizes 13 inputs
   covering every listed trigger (`$(...)`, backticks, `${...}`, `$VAR`,
   `|`, `;`, `&&`, `||`, `eval`, `sh -c`, `bash -c`, `xargs`, and a combined
   `find -delete | xargs`).
6. **Met.** `test_gate_default_always_pauses` runs all nine fixtures through
   `gate` with no flag and asserts `PAUSE <tier>` / exit 10 on every one.
   `test_gate_auto_approve_safe_tiers` / `test_gate_auto_approve_never_covers_dangerous_tiers`
   confirm the flag only ever flips `SAFE`/`REVERSIBLE_LOCAL`.
7. **Met.** README has install/run, the demo command with real captured
   output, the full tier table, the `--auto-approve-safe` semantics with the
   pause-by-default framing, all four documented limitations, and the
   PreToolUse hook-wiring snippet (marked illustrative, not shipped).
8. **Met.** `tests/test_preflight.py`, 93 tests, `python -m pytest -q` exits 0
   (real run, see below).
9. **Met.** `claims.json` maps all nine acceptance criteria to pass/fail.

## Demo command and real output

```
$ python preflight.py classify -- rm -rf build
Command              : rm -rf build
Tier                 : DESTRUCTIVE_LOCAL
Reversible           : False
Networked            : False
Files affected       : 0
Uncommitted at risk  : 0
Reasons:
  - 'rm' performs an irreversible local change
TIER: DESTRUCTIVE_LOCAL
```

(0/0 because this repo's working tree has no literal `build/` dir — the
fixture-repo tests above exercise the non-zero path.)

## Test suite — real output

Ran with the exact `test_cmd` the spec/forgejury declares
(`python -m pytest -q`, ambient interpreter — see the "Note on `python -m
pytest -q`" callout in my README for why that matters):

```
........................................................................ [ 77%]
.....................                                                    [100%]
93 passed in 2.99s
```

## Self-check: ran forgejury grade myself before writing this memo

```
$ python -m forgejury grade builds/2026-11-11/SPEC.md builds/2026-11-11/exec-2
=== Forgejury verdict ===
Summary: 1/1 builds PASS
[exec-2] verdict=PASS
    spec axis: file:README.md PASS, file:preflight.py PASS,
      file:tests/test_preflight.py PASS, file:claims.json PASS,
      symbol:preflight.py::classify_command PASS, test_cmd PASS
    claims axis: files PASS, symbols PASS, test_cmd_exit PASS, tests_passed PASS

=== Consensus (behavioral, stdout-only) ===
  read-only-ls 1-0 PASS, read-only-cat 1-0 PASS, rm-rf 1-0 PASS, mv 1-0 PASS,
  git-reset-hard 1-0 PASS, curl-post 1-0 PASS, git-push 1-0 PASS, mkdir 1-0 PASS,
  unknown-verb 1-0 PASS
```

9/9 consensus fixtures, all spec and claims axes PASS.

## Known gaps

- Enrichment (`files_affected`/`uncommitted_at_risk`) only handles literal
  paths and simple globs (`*`, `?`, `[...]`); anything else — including a
  path containing spaces that would need quoting beyond simple quotes — falls
  back to `null, null` rather than attempting a best-effort parse. This
  matches the spec's explicit non-goal ("no arbitrary-shell parsing").
- `git status` parsing assumes default porcelain format (no `-z`); a path
  containing a literal ` -> ` substring (not a rename arrow) would misparse.
  Edge case, not covered by a test, flagging for the record.
- The ambient-`python`-needs-`pytest` wrinkle (documented in my README) is an
  environment fact, not a code bug: forgejury's `run_command` always execs
  the literal `test_cmd` string with `shlex.split` + `subprocess.run`, so
  whatever `python` is first on PATH when forgejury runs must have `pytest`
  importable. I installed `pytest==8.3.5` via `pip install --user` to satisfy
  that for this grading pass; a from-scratch clone needs the same step
  (documented in the README's install section).

## Licenses

No third-party code vendored. Design anchors (no code taken, per spec):
DIYgod/pinky (Apache-2.0), shanselman/sandbox-mcp (MIT). Dev-only dependency:
`pytest==8.3.5` (MIT), pinned in `requirements-dev.txt`.
