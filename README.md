# Agent Forge

**An autonomous, Git-native team of Claude Code agents that scouts GitHub for
the hottest new AI and robotics projects, debates what to build on top of
them, builds it three different ways, and judges the result. Every week, with
no human in the loop unless they ask for one.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![Built on Claude Code](https://img.shields.io/badge/built%20on-Claude%20Code-d97757)

The agents never talk in a chat window. **Their only communication channel is
memo files committed to this repository**, so every idea, argument, decision
and build is versioned, diffable and auditable in `git log`. When they need a
human, they open a GitHub issue and @mention the owner.

```
scout.py ─► researcher ─► novelty-a ⇄ novelty-b (3 rounds) ─► reviewer: decide + SPEC.md
                                                                   │
                       ┌───────────────────────────────────────────┤
                       ▼                  ▼                  ▼
                 exec-1 (minimal)  exec-2 (production)  exec-3 (experimental)
                       └──────────────────┼──────────────────┘
                                          ▼
                        reviewer: run all three ─► SHIP / ITERATE / RESTART
```

## Shipped by Agent Forge

| Cycle | Project | What it is |
|---|---|---|
| 2026-11-04 | [**forgejury**](https://github.com/zerochance1907/forgejury) | A lie detector for AI coding agents: re-checks what a build *claims* against what is actually on disk, and triangulates parallel builds. The full debate, spec and review are in [`memos/2026-11-04/`](memos/2026-11-04) and [`reports/2026-11-04.md`](reports/2026-11-04.md). |

## Why

Most multi-agent demos pass messages in memory and vanish when the process
exits. Agent Forge treats **the repo as the shared brain**:

- **Durable and auditable**: every message is a committed Markdown memo with
  front matter (`from`, `to`, `stage`, `type`). You can replay a whole cycle
  from history.
- **Adversarial by design**: an ambitious novelty finder and a skeptical one
  must defend their ideas against each other and against prior-art searches
  before anything is built.
- **Diversity through personas**: three executioners build the *same* spec as
  a minimalist hacker, a production engineer and a wild experimentalist, in
  isolated Git worktrees. The reviewer actually runs all three and picks one.
- **Bounded**: per-agent dollar budgets, capped debate rounds, at most one
  rebuild and one restart per cycle, and a lock so runs never overlap.
- **Human in the loop only when needed**: questions become GitHub issues;
  replies flow back into the repo as memos.

## The agents

| Agent | Model (default) | Job |
|---|---|---|
| `researcher` | Sonnet | Vets candidates from the GitHub search API (past week + past year, ranked by star velocity) and writes a top-10 report. |
| `novelty-a` | Opus | The ambitious finder: proposes bold ideas that combine researched projects in new ways. |
| `novelty-b` | Opus | The skeptic: hunts prior art and hidden costs, kills weak ideas, proposes pragmatic ones. |
| `exec-1` | Opus | Minimalist hacker: the smallest thing that fully meets the spec. |
| `exec-2` | Opus | Production engineer: CLI, validation, tests, docs. |
| `exec-3` | Opus | Wild experimentalist: meets the spec, then adds a working creative twist. |
| `reviewer` | Opus | Picks the idea, writes the spec with acceptance criteria, runs every build, writes the final report, decides SHIP / ITERATE / RESTART. |

Role prompts live in [`agents/`](agents) and the shared rules in
[`PROTOCOL.md`](PROTOCOL.md).

## How a cycle runs

1. **research**: [`scout.py`](scout.py) queries the GitHub search API across
   AI / robotics topics; the researcher reads READMEs and code and writes
   `research/<cycle>/report.md`.
2. **debate**: novelty-a and novelty-b alternate for `debate_rounds` rounds,
   each ending with a ranked shortlist.
3. **decide**: the reviewer picks one idea and writes `builds/<cycle>/SPEC.md`,
   ending with a machine-checkable acceptance block that
   [Forgejury](https://github.com/zerochance1907/forgejury) lints.
4. **build**: the three executioners build the spec in parallel, each on its
   own branch and worktree, merged back into `main` afterwards. Each one ends
   by writing a `claims.json` saying what it believes it built.
5. **review**: Forgejury grades every build mechanically (spec checks, claims
   vs a fresh run, behavioral consensus) and posts the result as a memo. The
   reviewer starts from it, runs all builds, writes `reports/<cycle>.md`, and
   returns `SHIP`, `ITERATE` (one more build round with feedback) or `RESTART`.
6. **done**: an issue labelled `forge-report` links the owner to the report.

[`forge.py`](forge.py) is a resumable state machine (`state/state.json`). It is
the only process that commits, pushes or touches GitHub issues; agents only
write the memo paths they are given.

## Repository layout

| Path | What lives there |
|---|---|
| `PROTOCOL.md` | Rules every agent follows: memo format, asking the human, safety. |
| `agents/*.md` | Role prompts and executioner personas. |
| `config.json` | Owner, models, per-call budgets, debate rounds, cadence, scout topics. |
| `forge.py` | Orchestrator. |
| `scout.py` | Deterministic GitHub search. |
| `state/state.json` | Current cycle, stage, cost, open questions. |
| `memos/<cycle>/` | Every message between agents, numbered in order. |
| `research/<cycle>/` | Candidate list and research report. |
| `builds/<cycle>/` | `SPEC.md` and the three builds. |
| `reports/<cycle>.md` | The reviewer's final report: the page to read. |

## Quick start

Requirements: Windows, macOS or Linux with Python 3.11+, Git, the
[GitHub CLI](https://cli.github.com/) (`gh auth login`) and
[Claude Code](https://docs.claude.com/en/docs/claude-code) (`claude auth login`), and
Forgejury (`pip install git+https://github.com/zerochance1907/forgejury`).
Without Forgejury the pipeline still runs, just with a reviewer-only review.

```bash
# 1. Use this repo as a template or fork it, then clone your copy
gh repo fork zerochance1907/agent-forge --clone && cd agent-forge

# 2. Set "owner" in config.json to your GitHub username, and reset state
#    (delete memos/, research/, builds/, reports/ contents from the original if present)

# 3. Run a cycle
python forge.py new        # start a cycle and run it as far as it can go
python forge.py status     # where are we?
python forge.py step       # advance exactly one step (debugging)
```

To run it unattended on Windows, `install.ps1 -Repo <you>/agent-forge`
clones the repo to `%USERPROFILE%\agent-forge` and registers an hourly
scheduled task that calls `forge.py run`. On macOS / Linux, a cron entry
works the same way:

```bash
0 * * * * cd ~/agent-forge && python3 forge.py run >> logs/scheduler.log 2>&1
```

## Talking to the agents

When an agent writes a memo addressed to `human`, the orchestrator opens an
issue labelled `needs-human` that @mentions the owner. Reply with a comment;
on the next run the reply is copied into `memos/` as a `from: human` memo and
the issue is closed. Blocking questions pause the pipeline until answered. A
stage that fails twice in a row also asks through an issue.

## Safety

- Executioners and the reviewer run with `--dangerously-skip-permissions`
  because they install packages and run code they cloned. They are told to
  stay inside their worktree, but that is an instruction, not a sandbox: run
  Agent Forge on a machine or VM without secrets you cannot afford to expose.
- The researcher and novelty finders can only read and write files, search
  the web, and run read-only `gh` queries.
- Spending is capped per agent call by `budget_usd` in `config.json`.
- Upstream code is cloned into gitignored `vendor/` folders, never committed,
  and agents must record upstream licenses.

## Contributing

Issues and PRs are welcome, especially new agent roles, better scouting
signals, and sandboxed execution backends (containers, VMs).

## License

[MIT](LICENSE)
