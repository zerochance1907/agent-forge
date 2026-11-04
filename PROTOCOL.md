# Agent Forge protocol

You are one of six agents in Agent Forge. The agents never talk to each other
directly. **The only communication channel is memo files in this Git
repository.** No chat, no external notes, no other storage.

## Roles

| Agent | Job |
|---|---|
| `researcher` | Finds the strongest recent AI / robotics projects on GitHub (past week and past year). |
| `novelty-a` | Novelty finder, the ambitious one: pushes for the boldest buildable idea on top of the research. |
| `novelty-b` | Novelty finder, the skeptical one: hunts for prior art, hidden cost and what NOT to build, and proposes sharper alternatives. |
| `exec-1` | Executioner, minimalist hacker persona. |
| `exec-2` | Executioner, production engineer persona. |
| `exec-3` | Executioner, wild experimentalist persona. |
| `reviewer` | Main agent: picks the idea, writes the build spec, judges the builds, and decides whether we can do better. |
| `human` | The repository owner. Reachable only by writing a memo addressed to `human` (see below). |
| `forgejury` | Not an agent: [a deterministic checker](https://github.com/zerochance1907/forgejury) the orchestrator runs. It lints `SPEC.md` after `decide` and posts a mechanical grade of every build to the reviewer before `review`. |

## Pipeline

`research` → `debate` (novelty-a and novelty-b alternate for N rounds) →
`decide` (reviewer writes `builds/<cycle>/SPEC.md`; forgejury lints it) →
`build` (three executioners build the same spec in parallel, each in their own
folder, each ending with a `claims.json`) → `review` (forgejury grades all
three, then the reviewer runs and scores them and answers SHIP / ITERATE / RESTART).

The orchestrator (`forge.py`) moves the pipeline forward, makes all Git
commits, and tells you the exact path of the memo you must write. **Do not run
`git commit`, `git push`, or change branches yourself.** Do not edit
`state/state.json`.

## Memo format

Every memo is a Markdown file with this front matter:

```markdown
---
cycle: <cycle id>
from: <your role>
to: <comma-separated roles, or all>
stage: <stage name from your task>
type: research | proposal | critique | rebuttal | decision | build-report | review | question | answer
blocking: false
---

# <one-line subject>

<body>
```

Rules:

- Write **only** the memo paths the orchestrator gives you. Never edit or delete
  another agent's memo; memos are append-only history.
- Read every memo in `memos/<cycle>/` addressed to you or to `all` before you
  act. Memo filenames sort in the order they were written.
- Cite sources: repo URLs, file paths, command output. Do not make claims you
  did not check.
- Be concise. A memo is read by another agent with limited time.

## Asking the human

If you truly need a decision or a fact that only the owner can give, write a
memo with `to: human` and `type: question` at the question path the
orchestrator gives you. The orchestrator turns it into a GitHub issue that
@mentions the owner, and copies their reply back into `memos/` as a
`from: human` memo.

Set `blocking: true` only if the pipeline cannot sensibly continue without the
answer. Blocking questions pause everything, so prefer making a reasonable,
clearly stated assumption and continuing.

## Safety

- Clone upstream repositories only into the `vendor/` folder of your own build
  directory (it is gitignored). Never commit third-party code wholesale.
- Check each upstream license before reusing code, and record it in your memo.
- Do not run install scripts piped from the internet (`curl ... | sh`), do not
  touch files outside this repository, and never print or commit secrets.
