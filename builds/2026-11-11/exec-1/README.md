# Preflight

A deterministic blast-radius risk-tier classifier for agent shell commands.
Given a proposed command, it tells you how bad it could be *before* it runs —
without running it.

No dependencies beyond the Python 3 standard library and `git`. One file:
`preflight.py`.

## Install / run

```
# from this directory
python preflight.py classify -- rm -rf build
```

(Optional, for running the test suite: `python -m venv .venv && .venv/Scripts/python -m pip install pytest`
— pytest is only needed to run `tests/`, not to use the CLI.)

## Demo

```
$ python preflight.py classify -- rm -rf build
Command: rm -rf build
Tier: DESTRUCTIVE_LOCAL
Reversible: no
Networked: no
Files affected: 3
Uncommitted at risk: 1
External system: no
Reasons:
  - leading verb 'rm' (or output-truncating redirect) is destructive to the local tree
TIER: DESTRUCTIVE_LOCAL
```

`files_affected` / `uncommitted_at_risk` come from actually expanding `build`
against the working tree and cross-checking `git status --porcelain` — this is
why `rm -rf build` is cheap when `build/` is three generated files and
catastrophic when it isn't.

## Subcommands

### `tier` — the pinned, tree-independent surface

```
python preflight.py tier -- <command tokens...>
```

Prints **exactly** one tier token and nothing else:
`SAFE | REVERSIBLE_LOCAL | DESTRUCTIVE_LOCAL | EXTERNAL | UNKNOWN`.

### `classify` — the full blast-radius card

```
python preflight.py classify -- <command tokens...>
python preflight.py --json classify -- <command tokens...>
```

Human-readable card (last line always `TIER: <tier>`), or with `--json` a
single JSON object:

```json
{
  "action": "rm -rf build",
  "tier": "DESTRUCTIVE_LOCAL",
  "reversible": false,
  "networked": false,
  "files_affected": 3,
  "uncommitted_at_risk": 1,
  "external_system": false,
  "reasons": ["leading verb 'rm' (or output-truncating redirect) is destructive to the local tree"]
}
```

### `gate` — the approval decision

```
python preflight.py gate -- <command tokens...>
python preflight.py --auto-approve-safe gate -- <command tokens...>
```

Prints one line and sets exit code:

| | stdout | exit |
|---|---|---|
| default | `PAUSE <tier>` | `10` |
| `--auto-approve-safe`, tier is `SAFE`/`REVERSIBLE_LOCAL` | `AUTO-APPROVED <tier>` | `0` |
| `--auto-approve-safe`, tier is anything else | `PAUSE <tier>` | `10` |

**Safety default: with no flag, every command pauses, no matter how trivial.**
You opt in to auto-approval with `--auto-approve-safe`, and even then only
`SAFE` and `REVERSIBLE_LOCAL` ever auto-approve. `DESTRUCTIVE_LOCAL`,
`EXTERNAL`, and `UNKNOWN` can never be auto-approved by this tool.

## Tier table (precedence — first match wins)

| # | Tier | Trigger |
|---|---|---|
| 1 | `UNKNOWN` | obfuscation/indirection: `$(`, `` ` ``, `${`, unresolved `$VAR`, `\|`, `;`, `&&`, `\|\|`, `eval`, `sh -c`/`bash -c`, `xargs` |
| 2 | `EXTERNAL` | network/remote verb (`curl, wget, ssh, scp, sftp, nc, ncat, rsync, aws, gcloud, az, kubectl, psql, mysql`, `docker push/pull`, `npm publish/install`, `pip install`, `git push/pull/fetch/clone/remote`), a URL, or a `user@host:` pattern |
| 3 | `DESTRUCTIVE_LOCAL` | `rm, rmdir, mv, dd, truncate, shred`, `git reset --hard/clean/checkout -f\|--/restore`, or a truncating `>` redirect |
| 4 | `REVERSIBLE_LOCAL` | `mkdir, touch, cp`, `git add/commit/stash/checkout -b` |
| 5 | `SAFE` | `ls, dir, cat, type, head, tail, less, more, grep, rg, find (no -delete/-exec), pwd, echo, wc, stat, file`, `git status/log/diff/show/branch` |
| 6 | otherwise | `UNKNOWN` |

`reversible` is true for `SAFE`/`REVERSIBLE_LOCAL`. `networked`/`external_system`
are true only for `EXTERNAL`. **`UNKNOWN` is always treated as destructive by
`gate`** — it never auto-approves.

## Limitations (by design, read before you trust this)

- **`EXTERNAL` is detected, not graded.** A `curl -X POST .../charges` and a
  `curl -X POST .../search` both land in `EXTERNAL` and both pause. This tool
  does not try to tell a destructive API call from a harmless one.
- **The grammar is bounded, on purpose.** Anything using command substitution,
  variable expansion, pipes, `&&`/`;`, `eval`, `sh -c`, or `xargs` is not
  resolved — it degrades to `UNKNOWN`, and `UNKNOWN` is always treated as
  destructive. This is a feature: silent under-classification of an
  obfuscated command is worse than an extra pause.
- **No execution, no interception.** Preflight classifies a command string you
  hand it. It does not run anything, does not wrap your shell, and does not
  block a real command from running — that's the caller's job.
- **No symlink/alias/variable resolution.** `$HOME/foo` is `UNKNOWN`, not
  resolved and checked. A symlinked `build/` pointing into `src/` is not
  detected; the file count is computed against whatever `os.walk` actually
  finds on disk, which does follow the symlink's contents but has no way to
  flag "this is surprising."
- **File-count enrichment only applies to local-tier commands with literal or
  simple-glob path arguments** (`rm`, `rmdir`, `mv`, `dd`, `truncate`, `shred`,
  `mkdir`, `touch`, `cp`). Everything else — `git` subcommands, `EXTERNAL`,
  `UNKNOWN` — reports `files_affected`/`uncommitted_at_risk` as `null`.

## Wiring as a Claude Code `PreToolUse` hook (documentation only — not built)

Add to `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python /path/to/preflight.py --auto-approve-safe gate -- $CLAUDE_TOOL_INPUT_COMMAND"
          }
        ]
      }
    ]
  }
}
```

Exit code `10` should be mapped by the hook runner to "ask the human"; exit
code `0` to "proceed." Wiring this up (reading the real hook input schema,
mapping exit codes to the harness's actual pause mechanism) is out of scope
for this MVP — this snippet is a starting point, not a tested integration.

## Design anchors (no code vendored)

- [DIYgod/pinky](https://github.com/DIYgod/pinky) — Apache-2.0. Human-gated
  approval framing only.
- [shanselman/sandbox-mcp](https://github.com/shanselman/sandbox-mcp) — MIT.
  Clean-room fidelity bar only.

## Tests

```
python -m venv .venv
./.venv/Scripts/python -m pip install pytest   # or .venv/bin/python on Linux/Mac
./.venv/Scripts/python -m pytest -q
```

Covers: the 9 consensus fixtures, the obfuscation fallback, extra tier-table
coverage (git subcommands, redirects, `find -delete`, network verbs), CLI
surface behavior (`tier` stdout purity, `classify` card/`--json`, `gate`
default-pause and `--auto-approve-safe`), and file-count/uncommitted-at-risk
enrichment against a real temporary git fixture repo — including the case
where the CLI is invoked from a subdirectory of the repo (git reports
`status --porcelain` paths relative to the repo toplevel, not the cwd;
Preflight resolves that correctly).
