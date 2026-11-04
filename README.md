# Agent Forge

Seven Claude Code agents that find strong new AI / robotics projects on GitHub,
argue about what to build on top of them, build it three different ways, and
judge the result. The only communication channel between them is memo files in
this repository; they reach the owner through GitHub issues.

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

## Repository layout

| Path | What lives there |
|---|---|
| `PROTOCOL.md` | The rules every agent follows (memo format, asking the human, safety). |
| `agents/*.md` | Role prompts for each agent and executioner persona. |
| `config.json` | Models, per-call budgets, debate rounds, cycle cadence, scout topics. |
| `forge.py` | Orchestrator: a resumable state machine; the only thing that commits and pushes. |
| `scout.py` | Deterministic GitHub search (past week + past year, ranked by star velocity). |
| `state/state.json` | Current cycle, stage, step, cost, open questions. |
| `memos/<cycle>/` | Every message between agents, numbered in order. |
| `research/<cycle>/` | Candidate list and research report. |
| `builds/<cycle>/` | `SPEC.md` plus the three builds (`exec-1/2/3`). |
| `reports/<cycle>.md` | The reviewer's final report — the page to read. |

## How a cycle runs

1. **research**: `scout.py` pulls candidates via the GitHub API with your `gh`
   login; the researcher vets them and writes the report.
2. **debate**: novelty-a (ambitious) and novelty-b (skeptic) alternate for
   `debate_rounds` rounds, each ending with a ranked shortlist.
3. **decide**: the reviewer picks one idea and writes a build spec with
   acceptance criteria.
4. **build**: the three executioners build the same spec in parallel, each in
   its own Git worktree and branch, which are merged back into `main`.
5. **review**: the reviewer runs all three builds, writes the report and returns
   `SHIP`, `ITERATE` (one more build round, capped by `max_iterations`) or
   `RESTART` (back to research, capped by `max_restarts`).
6. **done**: an issue labelled `forge-report` links you to the report.

## Talking to the agents

When an agent writes a memo addressed to `human`, the orchestrator opens a
GitHub issue labelled `needs-human` that @mentions you. Reply with a comment;
on the next run your reply is copied into `memos/` and the issue is closed. If
the question is blocking, the pipeline waits until you reply. A stage that
fails twice in a row also asks you through an issue.

## Running it

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1   # clone to %USERPROFILE%\agent-forge + hourly task
python forge.py new      # start a cycle now
python forge.py status   # where are we?
python forge.py step     # advance one step (handy for debugging)
```

The scheduled task runs `forge.py run` every hour while you are logged in: it
resumes the current cycle, picks up your issue replies, and starts a new cycle
every `cycle_every_days` days. Logs are in `logs/` (not committed).

## Safety notes

- Executioners and the reviewer run with `--dangerously-skip-permissions`
  because they must install packages and run code they cloned. They run on
  this machine, inside their worktree, with instructions to stay there — but
  that is an instruction, not a sandbox. Do not run this on a machine with
  secrets you cannot afford to expose.
- The researcher and novelty finders can only read, write files, search the
  web, and run read-only `gh` queries.
- Spending is capped per agent call by `budget_usd` in `config.json`.
