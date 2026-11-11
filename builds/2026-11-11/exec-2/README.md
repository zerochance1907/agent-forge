# Preflight

A deterministic blast-radius classifier for agent shell commands. Given a
proposed command, Preflight computes a **risk tier** from the command's
structure plus (for local commands) the live working-tree delta, so the
answer to "how risky is this?" is a fact you can check, not a guess.

Preflight does not intercept, run, block, or wrap anything. It is a pure
function plus a thin CLI over it: you hand it a command string, it hands back
a tier and a card explaining why.

## Requirements

- Python 3.13 (stdlib only — no third-party runtime dependency)
- `git` on PATH (used only to read `git status`, never to run a command)
- `pytest` to run the test suite (dev-only dependency, pinned below)

## Install / run

No build step. Clone this directory and run the CLI directly:

```
python preflight.py tier -- ls -la
```

To run the test suite, install the pinned dev dependency into a virtualenv
(keeps your interpreter clean):

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q
```

> **Note on `python -m pytest -q` from a bare interpreter:** this repo's
> acceptance check runs that exact command against whatever `python` is on
> PATH (not necessarily the venv above). If you're running the acceptance
> check from a shell that has no `pytest` installed anywhere on its
> `sys.path`, install the same pinned version there too:
> `python -m pip install --user -r requirements-dev.txt`. Preflight's own
> runtime code never imports `pytest` — this is purely a test-runner
> dependency.

## Demo

```
$ python preflight.py classify -- rm -rf build
Command              : rm -rf build
Tier                 : DESTRUCTIVE_LOCAL
Reversible           : False
Networked            : False
Files affected       : 0
Uncommitted at risk   : 0
Reasons:
  - 'rm' performs an irreversible local change
TIER: DESTRUCTIVE_LOCAL
```

(`Files affected` / `Uncommitted at risk` are computed against whatever
working tree you run this in — `0` above because this repo has no `build/`
directory. Point it at a real tree and they populate; see
`tests/test_preflight.py::test_files_affected_counts_directory_contents` for
a worked fixture.)

```
$ python preflight.py --json classify -- rm -rf build
{"action": "rm -rf build", "tier": "DESTRUCTIVE_LOCAL", "reversible": false,
 "networked": false, "files_affected": 0, "uncommitted_at_risk": 0,
 "external_system": false, "reasons": ["'rm' performs an irreversible local change"]}
```

## Subcommands

### `tier` — the deterministic classification surface

```
python preflight.py tier -- <command tokens...>
```

Prints **exactly** one of the five tier tokens below and nothing else on
stdout. Depends only on the command string, never on the working tree, so
it's safe to script against.

### `classify` — the human-readable (or `--json`) blast-radius card

```
python preflight.py [--json] classify -- <command tokens...>
```

Without `--json`: a card ending in a line `TIER: <tier>`. With `--json`: a
single JSON object with exactly these fields:

| field | type | meaning |
|---|---|---|
| `action` | string | the reconstructed command |
| `tier` | string | one of the five tiers |
| `reversible` | bool | true for `SAFE` / `REVERSIBLE_LOCAL` |
| `networked` | bool | true iff `EXTERNAL` |
| `files_affected` | int or null | files touched, for local tiers with literal/simple-glob paths; `null` otherwise |
| `uncommitted_at_risk` | int or null | of those, how many have uncommitted changes in `git status` |
| `external_system` | bool | true iff `EXTERNAL` |
| `reasons` | list of strings | short human-readable justification |

### `gate` — the approval decision

```
python preflight.py [--auto-approve-safe] gate -- <command tokens...>
```

Prints one line and sets the exit code:

- **Default (no flag): every command pauses.** Prints `PAUSE <tier>`, exits `10`.
- With `--auto-approve-safe`: `SAFE` and `REVERSIBLE_LOCAL` print
  `AUTO-APPROVED <tier>` and exit `0`. `DESTRUCTIVE_LOCAL`, `EXTERNAL`, and
  `UNKNOWN` **always** still print `PAUSE <tier>` and exit `10` — the flag
  can never widen past those two tiers.

This is the "YOLO mode with a seatbelt" contract: silence is never the
default, and the auto-approve flag is opt-in and bounded.

## Tier table (precedence — first match wins)

| # | Tier | Trigger |
|---|---|---|
| 1 | `UNKNOWN` | obfuscation/indirection: `$(`, `` ` ``, `${`, an unresolved `$VAR`, `\|`, `;`, `&&`, `\|\|`, `eval`, `sh -c`/`bash -c`, `xargs` |
| 2 | `EXTERNAL` | leading verb is a network/remote tool (`curl`, `wget`, `ssh`, `scp`, `sftp`, `nc`, `ncat`, `rsync`, `aws`, `gcloud`, `az`, `kubectl`, `docker push/pull`, `npm publish/install`, `pip install`, `psql`, `mysql`), or `git push/pull/fetch/clone/remote`, or any token is a URL / `user@host:` |
| 3 | `DESTRUCTIVE_LOCAL` | `rm`, `rmdir`, `mv`, `dd`, `truncate`, `shred`; `git reset --hard`, `git clean`, `git checkout --`/`-f`, `git restore`; a truncating `>` redirect |
| 4 | `REVERSIBLE_LOCAL` | `mkdir`, `touch`, `cp`; `git add/commit/stash`, `git checkout -b` |
| 5 | `SAFE` | read-only tools (`ls`, `dir`, `cat`, `type`, `head`, `tail`, `less`, `more`, `grep`, `rg`, `find` without `-delete`/`-exec`, `pwd`, `echo`, `wc`, `stat`, `file`); `git status/log/diff/show/branch` |
| 6 | `UNKNOWN` | anything else (unrecognized verb) |

`reversible` is true for `SAFE` and `REVERSIBLE_LOCAL`. `networked` /
`external_system` are true only for `EXTERNAL`. **`UNKNOWN` is always treated
as destructive by `gate`** — it never auto-approves.

## Known limitations (by design, not bugs)

- **Bounded grammar only.** Preflight does not parse arbitrary shell. It does
  not resolve variables, aliases, command substitution, or symlink targets.
  Anything outside the grammar above degrades to `UNKNOWN`, which `gate`
  treats as non-approvable.
- **`EXTERNAL` is detected, not graded.** A `curl -X POST .../charges` and a
  `curl -X GET .../search` both land in `EXTERNAL` and both pause — Preflight
  does not attempt to judge how dangerous a given network call is.
- **No execution, interception, or sandboxing.** Preflight classifies a
  string you hand it; it never runs, blocks, or wraps a real command.
- **Opaque tree-local operations degrade to `UNKNOWN`.** A build script that
  writes 400 files isn't pattern-matched against the filesystem; only literal
  paths and simple globs (`*`, `?`, `[...]`) passed directly as a destructive
  command's arguments get `files_affected`/`uncommitted_at_risk` enrichment.

## Wiring as a Claude Code `PreToolUse` hook (documentation only — not built)

The hook itself is out of scope for this MVP; this is the shape of it. A
`PreToolUse` hook for the `Bash` tool can shell out to `gate` and translate
its exit code into an allow/ask decision:

```jsonc
// .claude/settings.json (illustrative — not shipped by this build)
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python /path/to/preflight.py --auto-approve-safe gate -- $CLAUDE_TOOL_COMMAND"
          }
        ]
      }
    ]
  }
}
```

Exit code `0` (auto-approved) lets the call through silently; exit code `10`
(pause) is where the hook script would surface the card (`classify --json`)
to the human and block until they approve. Translating that exit code into
your hook runner's specific allow/deny/ask protocol is the integration work
left to do.

## Running the tests

```
.venv\Scripts\python.exe -m pytest -q
```

Real output from this build:

```
........................................................................ [ 77%]
.....................                                                    [100%]
93 passed in 2.99s
```

`tests/test_preflight.py` covers: all nine spec consensus fixtures (both via
`classify_command` directly and via the `tier` CLI's exact stdout), the full
extended tier table (every verb/subcommand in the precedence rules), every
obfuscation/indirection trigger from acceptance criterion 5, the `find
-delete`/`-exec` carve-out, the `classify` card's trailing `TIER:` line and
the `--json` eight-field shape, `gate`'s default-pause behavior across all
nine fixtures plus the bounded `--auto-approve-safe` flag, and
tree-dependent enrichment (`files_affected` / `uncommitted_at_risk`) against
a real `git init` fixture repo built in a pytest `tmp_path` fixture.

## Licenses / design anchors

No third-party code is vendored. Two repos from the research report are
cited as design anchors only (no code taken):

- [DIYgod/pinky](https://github.com/DIYgod/pinky) — Apache-2.0 — human-gated
  approval framing.
- [shanselman/sandbox-mcp](https://github.com/shanselman/sandbox-mcp) — MIT —
  clean-room fidelity standard.

This build's own code is stdlib Python plus a `subprocess` call to the
locally installed `git`; its only dev-time dependency is `pytest==8.3.5`
(MIT license), pinned in `requirements-dev.txt`.
