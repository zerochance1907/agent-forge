# Preflight

A deterministic blast-radius risk-tier classifier for agent shell commands.
Given a proposed command, Preflight tells you what tier of trouble it is in —
**before** anything runs — by looking at the command's structure *and* the
live working-tree delta (`git status` + glob expansion), not just a
pattern-match on the command string.

Design anchors (no code vendored):
[DIYgod/pinky](https://github.com/DIYgod/pinky) (Apache-2.0) for the
human-gated-approval framing, and
[shanselman/sandbox-mcp](https://github.com/shanselman/sandbox-mcp) (MIT) for
the clean-room fidelity bar. Preflight itself is stdlib + `git` only — no
third-party dependency except `pytest` for the test suite.

## Install / run

Requires Python 3.13 and `git` on `PATH`. No install step for the CLI itself:

```bash
python preflight.py tier -- rm -rf build
```

To run the tests, pytest must be importable by whichever `python` you use.
Either rely on a `pytest` already on your system `python`, or create an
isolated environment:

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install pytest   # Windows
# .venv/bin/python -m pip install pytest          # macOS/Linux
python -m pytest -q
```

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

(The exact file/uncommitted counts depend on what's actually in `build/` and
`git status` in your tree — that's the point: the same `rm -rf build` is
cheap when `build/` holds 3 generated files and alarming when it holds your
unsaved edits.)

## The blast-radius map (the wild bit)

The human-readable card ends with a small ASCII visualization generated
*from the real numbers*, not a static icon per tier:

- **Local tiers** (`DESTRUCTIVE_LOCAL` / `REVERSIBLE_LOCAL`): a ring of `░`
  sized by how many files are affected, containing one `✖` per
  uncommitted-at-risk file and one `●` per clean/tracked file. More `✖` →
  visually denser danger.
- **`EXTERNAL`**: a ripple diagram — it never had a local radius to measure,
  so it's rendered as leaving the local blast radius entirely.
- **`UNKNOWN`**: a fog bank of `?` — the point is that the size is
  *unmeasurable*, so the card refuses to pretend otherwise.

This never appears in `--json` output — the JSON schema is exactly the eight
documented fields, machine-stable regardless of terminal flourishes.

## Tier table (first match wins)

| # | Tier | Trigger |
|---|------|---------|
| 1 | `UNKNOWN` | obfuscation/indirection the bounded grammar can't resolve: `$(`, backticks, `${`, unresolved `$VAR`, `\|`, `;`, `&&`, `\|\|`, `eval`, `sh -c`/`bash -c`, `xargs` |
| 2 | `EXTERNAL` | network/remote verb (`curl, wget, ssh, scp, sftp, nc, ncat, rsync, aws, gcloud, az, kubectl, docker push/pull, npm publish/install, pip install, psql, mysql`), or `git push/pull/fetch/clone/remote`, or a URL / `user@host:` token |
| 3 | `DESTRUCTIVE_LOCAL` | `rm, rmdir, mv, dd, truncate, shred`; `git reset --hard`, `git clean`, `git checkout -- /-f`, `git restore`; a truncating `>` redirect |
| 4 | `REVERSIBLE_LOCAL` | `mkdir, touch, cp`; `git add, commit, stash, checkout -b` |
| 5 | `SAFE` | read-only tools (`ls, dir, cat, type, head, tail, less, more, grep, rg, find*, pwd, echo, wc, stat, file`); `git status/log/diff/show/branch`. (`find` is `SAFE` only without `-delete`/`-exec`.) |
| 6 | `UNKNOWN` | anything else |

`reversible` = true for `SAFE` / `REVERSIBLE_LOCAL`. `networked` /
`external_system` = true iff tier is `EXTERNAL`. **`UNKNOWN` is always
treated as destructive by `gate` — it is never auto-approved.**

## Subcommands

- `python preflight.py tier -- <cmd...>` — prints exactly the tier token and
  nothing else on stdout. Depends only on the command string.
- `python preflight.py [--json] classify -- <cmd...>` — prints the full card;
  last stdout line is always `TIER: <tier>`. With `--json`, prints one JSON
  object: `action, tier, reversible, networked, files_affected,
  uncommitted_at_risk, external_system, reasons`.
- `python preflight.py [--auto-approve-safe] gate -- <cmd...>` — prints
  `AUTO-APPROVED <tier>` (exit 0) or `PAUSE <tier>` (exit 10).
  **Default: every command pauses.** With `--auto-approve-safe`, only `SAFE`
  and `REVERSIBLE_LOCAL` auto-approve — `DESTRUCTIVE_LOCAL`, `EXTERNAL`, and
  `UNKNOWN` always pause, flag or no flag.

## Known limitations (by design, not oversight)

- **Bounded grammar only.** No variable resolution, no alias expansion, no
  symlink-target following, no real shell parsing. Anything outside the
  pinned grammar degrades to `UNKNOWN`, which `gate` treats as destructive.
- **`EXTERNAL` is detected, not graded.** A `POST /charges` and a
  `POST /search` both land in `EXTERNAL` and both pause — Preflight does not
  attempt to assess how bad a given network call is.
- **No interception or execution.** Preflight classifies a command string
  you hand it; it never runs, blocks, or wraps a real command.
- **File-count enrichment is literal/glob-path only.** It covers
  `rm/rmdir/mv/dd/truncate/shred` sources and `mkdir/touch/cp` targets
  against the working tree. Git-based local tiers (`git reset --hard`,
  `git clean`, etc.) report `files_affected`/`uncommitted_at_risk` as `null`
  — scoping "whole tree" accurately there is future work, not this MVP.
- **No COW / Windows Sandbox preview.** Opaque local scripts (e.g. a build
  step that writes 400 files) degrade to `UNKNOWN` rather than being
  simulated.

## Wiring into a Claude Code `PreToolUse` hook (documentation only — not built)

Preflight is a standalone CLI; it does not ship a hook. To gate `Bash` tool
calls with it, a `PreToolUse` hook could run:

```bash
#!/usr/bin/env bash
# .claude/hooks/preflight-gate.sh
cmd=$(jq -r '.tool_input.command' <<<"$CLAUDE_HOOK_INPUT")
python preflight.py --auto-approve-safe gate -- $cmd
if [ $? -eq 10 ]; then
  echo '{"decision": "ask"}'
else
  echo '{"decision": "allow"}'
fi
```

Exit code `10` from `gate` maps to "pause for human," exit `0` maps to
"auto-approved" — the hook script above is illustrative, not shipped.
