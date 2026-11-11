# Build Spec — cycle 2026-11-11

## Idea: **Preflight** — a deterministic blast-radius classifier for agent shell commands

A small, self-contained CLI that, given a proposed shell command, computes a
**blast-radius card** and assigns a **risk tier** —
`SAFE / REVERSIBLE_LOCAL / DESTRUCTIVE_LOCAL / EXTERNAL / UNKNOWN` — from the
command structure plus the *live working-tree delta* (glob expansion +
`git status`). It lets a user opt in to auto-approving only the safe tiers.

This is the *informed half* of the human-in-the-loop approval pattern the
research report calls the freshest theme (pinky's "pause for your click"): the
gap isn't "pause the agent," it's "pause only for the clicks that matter, and
tell the human exactly why this one does." Existing deny-list hooks pattern-match
the command *string*; Preflight computes the live tree delta, so `rm -rf build/`
is correctly cheap when `build/` is 3 generated files and correctly catastrophic
when someone symlinked it into `src/`.

### Problem and target user

Anyone running a semi-autonomous coding/ops agent who wants "YOLO mode with a
seatbelt": not a card on every call (approval fatigue → rubber-stamping), but a
tool that classifies each proposed command's real blast radius and only breaks
the human's flow for the irreversible / external ones.

### Upstream repositories

No third-party code is vendored. Two researched repos are **design anchors only**
(both permissive, recorded for the license trail):

- [DIYgod/pinky](https://github.com/DIYgod/pinky) — **Apache-2.0**. We take the
  *human-gated-approval* framing (a trusted process gates the action; the human
  approves). We take no code.
- [shanselman/sandbox-mcp](https://github.com/shanselman/sandbox-mcp) — **MIT**.
  We take its *clean-room fidelity standard* as the conceptual bar an approval
  surface should meet. We take no code.

Standard library + `git` (already assumed present) only. No pip/npm dependency is
required beyond `pytest` for the test suite.

### Scope — what to build

A single CLI, `preflight.py`, runnable as `python preflight.py <subcommand> ...`,
with:

1. **`tier` subcommand** — `python preflight.py tier -- <command tokens...>`
   prints **exactly** the tier name (one of the five tokens above) and a trailing
   newline, and nothing else on stdout. The command is every argument following
   the first `--`, joined with single spaces. This is the deterministic,
   tree-independent classification surface.

2. **`classify` subcommand** — `python preflight.py [--json] classify -- <command tokens...>`
   prints a human-readable blast-radius **card** whose last stdout line is
   `TIER: <tier>`. With `--json` it instead prints a single JSON object with
   fields: `action` (string, the reconstructed command), `tier` (string),
   `reversible` (bool), `networked` (bool), `files_affected` (int or null),
   `uncommitted_at_risk` (int or null), `external_system` (bool),
   `reasons` (list of short strings). For local-tier commands with literal or
   simple-glob paths, `files_affected` and `uncommitted_at_risk` are computed
   against the current working tree; otherwise they are `null`.

3. **`gate` subcommand** — `python preflight.py [--auto-approve-safe] gate -- <command tokens...>`
   prints a one-line decision: `AUTO-APPROVED <tier>` or `PAUSE <tier>`, and sets
   the exit code: `0` when auto-approved, `10` when it would pause for a human.
   **Default (no flag): every command pauses** (`PAUSE`, exit 10). With
   `--auto-approve-safe`, only `SAFE` and `REVERSIBLE_LOCAL` auto-approve; `gate`
   must **never** auto-approve `DESTRUCTIVE_LOCAL`, `EXTERNAL`, or `UNKNOWN`.

4. A core function **`classify_command(command, root=".")`** in `preflight.py`
   returning the card dict (including `tier`). The CLI is a thin wrapper over it.

#### Classification rules (pin these exactly — all three builds must agree)

Tokenize the command on whitespace (respect simple single/double quotes; do not
execute anything). Apply this **precedence, in order; first match wins**:

1. **UNKNOWN** if the command contains any obfuscation / indirection the bounded
   grammar does not resolve: `$(`, backticks `` ` ``, `${`, an unresolved `$VAR`,
   a pipe `|`, `;`, `&&`, `||`, `eval`, `sh -c` / `bash -c`, or `xargs`.
2. **EXTERNAL** if the leading verb is a network/remote tool —
   `curl, wget, ssh, scp, sftp, nc, ncat, rsync, aws, gcloud, az, kubectl,
   docker (push/pull), npm (publish/install), pip (install), psql, mysql` — **or**
   the verb is `git` with subcommand in `{push, pull, fetch, clone, remote}` —
   **or** any token matches a URL (`http://`, `https://`, `ftp://`) or a
   `user@host:` pattern.
3. **DESTRUCTIVE_LOCAL** if the leading verb is in
   `{rm, rmdir, mv, dd, truncate, shred}`, **or** the verb is `git` with
   subcommand in `{reset (with --hard), clean, checkout (with -- or -f), restore}`,
   **or** the command contains an output-truncating redirect `>` (not `>>`).
4. **REVERSIBLE_LOCAL** if the leading verb is in
   `{mkdir, touch, cp}` **or** the verb is `git` with subcommand in
   `{add, commit, stash, checkout -b}`.
5. **SAFE** if the leading verb is a read-only tool —
   `{ls, dir, cat, type, head, tail, less, more, grep, rg, find, pwd, echo,
   wc, stat, file}` (treat `find` as SAFE only when it has no `-delete` / `-exec`)
   — **or** the verb is `git` with subcommand in
   `{status, log, diff, show, branch}`.
6. Otherwise → **UNKNOWN**.

`reversible` is true for `SAFE` and `REVERSIBLE_LOCAL`; false otherwise.
`networked` / `external_system` are true iff tier is `EXTERNAL`.
**UNKNOWN is always treated as destructive** by `gate` (never auto-approved).

### Scope — what NOT to build (explicit)

- **No interception or execution.** Preflight classifies a command string it is
  handed; it does not run, block, or wrap real commands itself.
- **No MCP server, no transport plumbing, no GUI, no model in the loop, no
  network calls.**
- **No arbitrary-shell parsing.** Only the bounded grammar above; everything else
  degrades to `UNKNOWN → treated as destructive`. Do not attempt to resolve
  variables, aliases, command substitution, or symlink targets.
- **No networked-reversibility grading.** `EXTERNAL` is *detected*, not graded —
  a `POST /charges` and a `POST /search` both land in `EXTERNAL` (pause). State
  this limit in the README.
- **No COW sandbox / Windows Sandbox preview.** The opaque-tree-local class
  (e.g. a build script that writes 400 files) degrades to `UNKNOWN`; sandbox
  preview is out of scope for this MVP.
- **No Claude Code hook implementation.** The README should *document* how to wire
  `preflight.py gate` as a PreToolUse hook (a few lines), but the hook itself is
  out of scope — the MVP is the standalone CLI.

### Interface and demo command

Standalone Python CLI (Python 3.13, stdlib + `git`). Canonical demo:

```
python preflight.py classify -- rm -rf build
```

Expected: a card listing the command, tier `DESTRUCTIVE_LOCAL`, reversibility,
and (against the local tree) the file count and uncommitted-at-risk count,
ending in a line `TIER: DESTRUCTIVE_LOCAL`.

### Acceptance criteria

1. `python preflight.py tier -- <cmd>` prints exactly one of
   `SAFE | REVERSIBLE_LOCAL | DESTRUCTIVE_LOCAL | EXTERNAL | UNKNOWN` and nothing
   else on stdout.
2. The classification precedence table above is implemented exactly; the nine
   consensus fixtures below all produce their stated tier.
3. `python preflight.py classify -- <cmd>` prints a human-readable card whose
   final stdout line is `TIER: <tier>`; `--json` emits the documented JSON object
   with all eight fields.
4. For a `DESTRUCTIVE_LOCAL` command with literal/simple-glob paths,
   `files_affected` and `uncommitted_at_risk` in the card are computed correctly
   against the working tree (verified by a pytest fixture repo); for non-local or
   unparseable paths they are `null`.
5. Obfuscation/indirection inputs (`$(...)`, backticks, `|`, `;`, `&&`, `eval`,
   `sh -c`, unresolved `$VAR`, `xargs`) classify as `UNKNOWN`.
6. `python preflight.py gate -- <cmd>` pauses on **every** command by default
   (`PAUSE`, exit 10). With `--auto-approve-safe`, `SAFE` and `REVERSIBLE_LOCAL`
   print `AUTO-APPROVED` and exit 0, while `DESTRUCTIVE_LOCAL`, `EXTERNAL`, and
   `UNKNOWN` still `PAUSE` and exit 10.
7. `README.md` documents: install/run, the demo command, the full tier table,
   the `--auto-approve-safe` flag **with its brief-everything safety default**,
   the documented limitations (EXTERNAL not graded; bounded grammar; UNKNOWN is
   conservative), and the optional PreToolUse-hook wiring snippet.
8. `tests/test_preflight.py` covers the tier table, the `UNKNOWN` fallback, and
   the file-count enrichment; `python -m pytest -q` exits 0.
9. `claims.json` records, per acceptance criterion, whether the build claims it
   passes.

### Build-variance guardrails (why this spec is deterministic across all three builders)

The `tier` surface depends **only on the command string**, not on tree contents,
so the consensus fixtures below are identical for every builder regardless of
their working-tree state. Tree-dependent enrichment (file counts) is confined to
`classify`/`--json` and exercised only by each build's own pytest fixture repo.
Keep stdout of `tier` free of banners/logging.

## Forgejury Acceptance Block

```json
{
  "spec_checks": {
    "requires_file": ["README.md", "preflight.py", "tests/test_preflight.py", "claims.json"],
    "requires_symbol": ["preflight.py::classify_command"],
    "test_cmd": "python -m pytest -q",
    "runner": "pytest"
  },
  "consensus": {
    "invoke": "python preflight.py tier -- {input}",
    "fixtures": [
      { "name": "read-only-ls", "input": "ls -la", "expected": "SAFE" },
      { "name": "read-only-cat", "input": "cat README.md", "expected": "SAFE" },
      { "name": "rm-rf", "input": "rm -rf build", "expected": "DESTRUCTIVE_LOCAL" },
      { "name": "mv", "input": "mv old.txt new.txt", "expected": "DESTRUCTIVE_LOCAL" },
      { "name": "git-reset-hard", "input": "git reset --hard HEAD", "expected": "DESTRUCTIVE_LOCAL" },
      { "name": "curl-post", "input": "curl -X POST https://api.example.com/charges", "expected": "EXTERNAL" },
      { "name": "git-push", "input": "git push origin main", "expected": "EXTERNAL" },
      { "name": "mkdir", "input": "mkdir newdir", "expected": "REVERSIBLE_LOCAL" },
      { "name": "unknown-verb", "input": "frobnicate --wild", "expected": "UNKNOWN" }
    ]
  }
}
```
