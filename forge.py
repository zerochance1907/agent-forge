#!/usr/bin/env python3
"""Agent Forge orchestrator.

A resumable state machine that runs seven agent roles (researcher, two novelty
finders, three executioners, reviewer) as headless Claude Code processes. The
agents communicate only through memo files in this repository; this script is
the only thing that commits, pushes, and talks to GitHub issues.

Usage:
    python forge.py run      # advance as far as possible (what the scheduler calls)
    python forge.py step     # advance exactly one stage step
    python forge.py new      # start a new cycle now, then run
    python forge.py status   # print the current state
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
LOCAL = json.loads((ROOT / "local.json").read_text(encoding="utf-8-sig")) if (ROOT / "local.json").exists() else {}
STATE_PATH = ROOT / "state" / "state.json"
LOG_DIR = ROOT / "logs"
LOCK = LOG_DIR / "forge.lock"
EXECS = ["exec-1", "exec-2", "exec-3"]
DEFAULT_STATE = {
    "cycle": None, "stage": "idle", "step": 0, "iteration": 0, "restarts": 0,
    "failures": 0, "seq": 0, "last_cycle_started": None, "cost_usd": 0.0,
    "pending_questions": [], "escalated": [], "history": [],
}


# ---------------------------------------------------------------- utilities

def log(msg):
    line = f"[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line, flush=True)
    LOG_DIR.mkdir(exist_ok=True)
    with open(LOG_DIR / "forge.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def sh(cmd, cwd=ROOT, check=True, input=None):
    r = subprocess.run(cmd, cwd=cwd, input=input, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if check and r.returncode:
        raise RuntimeError(f"{' '.join(cmd[:3])} failed ({r.returncode}): {(r.stderr or r.stdout).strip()[:2000]}")
    return r.stdout


def git(*args, cwd=ROOT, check=True):
    return sh(["git", *args], cwd=cwd, check=check)


def claude_path():
    for p in (LOCAL.get("claude_path"), shutil.which("claude"),
              str(Path.home() / ".local" / "bin" / "claude.exe")):
        if p and Path(p).exists():
            return p
    raise RuntimeError("claude CLI not found; set claude_path in local.json")


def load_state():
    if STATE_PATH.exists():
        return {**DEFAULT_STATE, **json.loads(STATE_PATH.read_text(encoding="utf-8"))}
    return dict(DEFAULT_STATE)


def save_state(state):
    STATE_PATH.parent.mkdir(exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def commit(author, message, cwd=ROOT):
    git("add", "-A", cwd=cwd)
    if git("status", "--porcelain", cwd=cwd).strip():
        git("-c", f"user.name=forge-{author}", "-c", "user.email=forge@agent-forge.local",
            "commit", "-q", "-m", message, cwd=cwd)


def push():
    out = subprocess.run(["git", "push", "-q"], cwd=ROOT, capture_output=True, text=True)
    if out.returncode:
        log(f"push failed (will retry next run): {out.stderr.strip()[:300]}")


def checkpoint(state, author, message):
    save_state(state)
    commit(author, message)
    push()


def memo_dir(state):
    d = ROOT / "memos" / state["cycle"]
    d.mkdir(parents=True, exist_ok=True)
    return d


def next_memo(state, sender, to):
    state["seq"] += 1
    return f"memos/{state['cycle']}/{state['seq']:03d}-{sender}-to-{to}.md"


def front_matter(path):
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    m = re.match(r"---\s*\n(.*?)\n---\s*\n?(.*)", text, re.S)
    meta, body = ({}, text) if not m else (dict(
        (k.strip(), v.strip()) for k, v in
        (line.split(":", 1) for line in m.group(1).splitlines() if ":" in line)), m.group(2))
    return meta, body


def write_memo(rel_path, cycle, sender, to, stage, kind, subject, body, blocking=False):
    p = ROOT / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        f"---\ncycle: {cycle}\nfrom: {sender}\nto: {to}\nstage: {stage}\ntype: {kind}\n"
        f"blocking: {str(blocking).lower()}\n---\n\n# {subject}\n\n{body.strip()}\n",
        encoding="utf-8")


def repo_slug():
    return sh(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"]).strip()


# ------------------------------------------------------------ agent running

class Job:
    def __init__(self, state, role, task, memo_to, cwd=ROOT):
        spec = CONFIG["agents"][role]
        self.role, self.cwd, self.spec = role, Path(cwd), spec
        self.memo = next_memo(state, role, memo_to.replace(", ", "+").replace(",", "+"))
        self.ask = next_memo(state, role, "human")
        self.log_path = LOG_DIR / state["cycle"] / f"{self.memo.split('/')[-1][:-3]}.json"
        stage = state["stage"]
        self.prompt = (
            f"Cycle: {state['cycle']}. Stage: {stage}. You are `{role}`.\n"
            f"Your working directory is the repository root: {self.cwd}\n\n"
            f"TASK:\n{task}\n\n"
            f"Write your output memo to: {self.memo}\n"
            f"Front matter: cycle: {state['cycle']}, from: {role}, to: {memo_to}, stage: {stage}.\n"
            f"Only if you need something only the human owner can give, also write a "
            f"question memo (to: human, type: question) to: {self.ask}\n"
            f"Before acting, read every memo in memos/{state['cycle']}/ addressed to you or to `all`.\n"
            f"When you are done, reply with one line saying what you wrote.")
        self.proc = None

    def command(self):
        system = (ROOT / "PROTOCOL.md").read_text(encoding="utf-8")
        for name in self.spec["prompt"]:
            system += "\n\n" + (ROOT / "agents" / name).read_text(encoding="utf-8")
        cmd = [claude_path(), "-p", "--model", self.spec["model"], "--output-format", "json",
               "--max-budget-usd", str(self.spec["budget_usd"]), "--append-system-prompt", system]
        if self.spec.get("full_access"):
            cmd.append("--dangerously-skip-permissions")
        else:
            cmd += ["--permission-mode", "acceptEdits", "--allowedTools", *self.spec["tools"]]
        return cmd

    def launch(self):
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        log(f"-> {self.role} started (memo {self.memo})")
        self.out = open(self.log_path, "w", encoding="utf-8")
        self.started = time.time()
        self.proc = subprocess.Popen(self.command(), cwd=self.cwd, stdin=subprocess.PIPE,
                                     stdout=self.out, stderr=subprocess.STDOUT,
                                     text=True, encoding="utf-8", errors="replace")
        self.proc.stdin.write(self.prompt)
        self.proc.stdin.close()
        return self

    def wait(self, state):
        timeout = self.spec.get("timeout_min", 120) * 60
        try:
            self.proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            log(f"!! {self.role} timed out after {timeout // 60} min")
        self.out.close()
        try:
            result = json.loads(self.log_path.read_text(encoding="utf-8").strip().splitlines()[-1])
            state["cost_usd"] = round(state["cost_usd"] + float(result.get("total_cost_usd") or 0), 4)
        except (ValueError, IndexError):
            pass
        ok = (self.cwd / self.memo).exists()
        log(f"<- {self.role} {'done' if ok else 'FAILED (no memo)'} in "
            f"{(time.time() - self.started) / 60:.1f} min, exit {self.proc.returncode}")
        return ok


def run_agent(state, role, task, memo_to):
    memo_dir(state)
    job = Job(state, role, task, memo_to)
    save_state(state)
    if not job.launch().wait(state):
        raise RuntimeError(f"{role} did not write {job.memo}; see {job.log_path}")
    return job.memo


# ------------------------------------------------------------------ stages

def stage_idle(state, force=False):
    last = state.get("last_cycle_started")
    due = force or not last or (dt.datetime.now() - dt.datetime.fromisoformat(last)).days >= CONFIG["cycle_every_days"]
    if not due:
        return False
    cycle = dt.date.today().isoformat()
    n = 2
    while (ROOT / "memos" / cycle).exists():
        cycle = f"{dt.date.today().isoformat()}-{n}"
        n += 1
    state.update(cycle=cycle, stage="research", step=0, iteration=0, restarts=0, failures=0,
                 seq=0, cost_usd=0.0, last_cycle_started=dt.datetime.now().isoformat(timespec="seconds"))
    log(f"== new cycle {cycle}")
    checkpoint(state, "orchestrator", f"forge: start cycle {cycle}")
    return True


def stage_research(state):
    c = state["cycle"]
    sh([sys.executable, str(ROOT / "scout.py"), f"research/{c}/candidates.json"])
    run_agent(state, "researcher",
              f"Read research/{c}/candidates.json and write research/{c}/report.md as described in "
              f"your role. If a reviewer memo in this cycle says VERDICT: RESTART, follow its advice "
              f"about what to look for instead.",
              "novelty-a, novelty-b, reviewer")
    state.update(stage="debate", step=0)
    checkpoint(state, "researcher", f"researcher: research report for {c}")
    return True


def stage_debate(state):
    c, i, rounds = state["cycle"], state["step"], CONFIG["debate_rounds"]
    me, other = ("novelty-a", "novelty-b") if i % 2 == 0 else ("novelty-b", "novelty-a")
    rnd = i // 2 + 1
    if i == 0:
        task = (f"Debate round {rnd} of {rounds}. Open the debate: read research/{c}/report.md "
                f"and propose your 3 best ideas.")
    else:
        task = (f"Debate round {rnd} of {rounds}. Read research/{c}/report.md and every debate memo "
                f"so far in this cycle. Respond to the latest memo from {other}: attack, concede, "
                f"refine, and add better ideas if you have them.")
    if rnd == rounds:
        task += " This is the final round: end with your `## Final shortlist`."
    run_agent(state, me, task, f"{other}, reviewer")
    state["step"] = i + 1
    if state["step"] >= 2 * rounds:
        state.update(stage="decide", step=0)
    checkpoint(state, me, f"{me}: debate round {rnd} ({c})")
    return True


def stage_decide(state):
    c = state["cycle"]
    memo = run_agent(state, "reviewer",
                     f"Stage decide. Read research/{c}/report.md and the whole debate, pick one idea, "
                     f"and write builds/{c}/SPEC.md. End your memo with `DECISION: <title>`.",
                     "exec-1, exec-2, exec-3, all")
    m = re.search(r"DECISION:\s*(.+)", (ROOT / memo).read_text(encoding="utf-8"))
    if not (ROOT / "builds" / c / "SPEC.md").exists():
        raise RuntimeError("reviewer did not write SPEC.md")
    state["decision"] = m.group(1).strip() if m else "(see spec)"
    state.update(stage="build", step=0)
    checkpoint(state, "reviewer", f"reviewer: decision for {c}: {state['decision']}")
    return True


def stage_build(state):
    c, it = state["cycle"], state["iteration"]
    memo_dir(state)
    jobs = []
    for role in EXECS:
        branch = f"build/{c}/r{it}/{role}"
        wt = ROOT / ".worktrees" / f"{c}-r{it}-{role}"
        task = (f"Build round {it + 1}. Implement builds/{c}/SPEC.md inside builds/{c}/{role}/ as "
                f"your persona would. Run the demo and report real output.")
        if it > 0:
            task += " Read the reviewer's latest review memo first and address every point it makes about your build."
        jobs.append((Job(state, role, task, "reviewer", cwd=wt), branch, wt))
    checkpoint(state, "orchestrator", f"forge: start build round {it + 1} ({c})")

    for job, branch, wt in jobs:
        if wt.exists():
            git("worktree", "remove", "--force", str(wt), check=False)
        git("branch", "-D", branch, check=False)
        git("worktree", "add", "-q", "-b", branch, str(wt), "HEAD")
        job.launch()
    results = [(job, branch, wt, job.wait(state)) for job, branch, wt in jobs]

    for job, branch, wt, ok in results:
        commit(job.role, f"{job.role}: build round {it + 1} ({c}){'' if ok else ' [no report]'}", cwd=wt)
        git("merge", "-q", "--no-ff", "-m", f"forge: merge {branch}", branch)
        git("worktree", "remove", "--force", str(wt), check=False)
        git("branch", "-D", branch, check=False)
    if not any(ok for *_, ok in results):
        raise RuntimeError("all three executioners failed")
    state.update(stage="review", step=0)
    checkpoint(state, "orchestrator", f"forge: builds merged ({c}, round {it + 1})")
    return True


def stage_review(state):
    c = state["cycle"]
    memo = run_agent(state, "reviewer",
                     f"Stage review. Evaluate builds/{c}/exec-1, exec-2 and exec-3 against builds/{c}/SPEC.md "
                     f"by actually running them, write reports/{c}.md, and end your memo with the "
                     f"VERDICT and WINNER lines.",
                     "all")
    text = (ROOT / memo).read_text(encoding="utf-8")
    verdict = (re.findall(r"VERDICT:\s*(SHIP|ITERATE|RESTART)", text) or ["SHIP"])[-1]
    winner = (re.findall(r"WINNER:\s*(exec-[123]|none)", text) or ["none"])[-1]
    state["history"].append({"cycle": c, "iteration": state["iteration"], "verdict": verdict,
                             "winner": winner, "decision": state.get("decision")})
    log(f"== review verdict {verdict}, winner {winner}")
    if verdict == "ITERATE" and state["iteration"] < CONFIG["max_iterations"]:
        state.update(stage="build", iteration=state["iteration"] + 1)
    elif verdict == "RESTART" and state["restarts"] < CONFIG["max_restarts"]:
        state.update(stage="research", iteration=0, restarts=state["restarts"] + 1)
    else:
        state.update(stage="done")
    checkpoint(state, "reviewer", f"reviewer: {verdict} ({c}, winner {winner})")
    return True


def stage_done(state):
    c = state["cycle"]
    last = state["history"][-1] if state["history"] else {}
    if CONFIG.get("notify_on_done"):
        slug = repo_slug()
        body = (f"@{CONFIG['owner']} cycle **{c}** finished.\n\n"
                f"- Idea: {last.get('decision')}\n- Verdict: {last.get('verdict')}\n"
                f"- Winner: {last.get('winner')}\n- Agent cost: ${state['cost_usd']:.2f}\n\n"
                f"Report: https://github.com/{slug}/blob/main/reports/{c}.md\n"
                f"Builds: https://github.com/{slug}/tree/main/builds/{c}\n\n"
                f"No reply needed; close this when you've read it.")
        sh(["gh", "issue", "create", "--title", f"[forge] cycle {c} report: {last.get('decision')}",
            "--body", body, "--label", "forge-report"])
    state.update(stage="idle", step=0)
    log(f"== cycle {c} done")
    checkpoint(state, "orchestrator", f"forge: cycle {c} done")
    return True


STAGES = {"research": stage_research, "debate": stage_debate, "decide": stage_decide,
          "build": stage_build, "review": stage_review, "done": stage_done}


# -------------------------------------------------------- human in the loop

def escalate_questions(state):
    """Turn new memos addressed to `human` into GitHub issues that @mention the owner."""
    if not state["cycle"]:
        return
    for path in sorted((ROOT / "memos" / state["cycle"]).glob("*-to-human.md")):
        rel = path.relative_to(ROOT).as_posix()
        if rel in state["escalated"]:
            continue
        meta, body = front_matter(path)
        sender = meta.get("from", path.name.split("-")[1])
        blocking = meta.get("blocking", "false").lower() == "true"
        title = next((l.lstrip("# ").strip() for l in body.splitlines() if l.strip()), "question")
        issue_body = (f"@{CONFIG['owner']} `{sender}` needs your input"
                      f"{' — **the pipeline is paused until you reply**' if blocking else ''}.\n\n"
                      f"{body.strip()}\n\n---\nReply with a comment here. Your reply is copied into "
                      f"`memos/{state['cycle']}/` for the agents and this issue is closed. Source: `{rel}`")
        url = sh(["gh", "issue", "create", "--title", f"[forge] {sender}: {title[:80]}",
                  "--body", issue_body, "--label", "needs-human"]).strip()
        number = int(url.rstrip("/").split("/")[-1])
        state["escalated"].append(rel)
        state["pending_questions"].append({"issue": number, "memo": rel, "from": sender,
                                           "blocking": blocking, "cycle": state["cycle"]})
        log(f"?? asked human (issue #{number}, blocking={blocking}) for {sender}")
    save_state(state)


def collect_replies(state):
    """Copy the owner's issue replies back into memos and close the issues."""
    still = []
    for q in state["pending_questions"]:
        data = json.loads(sh(["gh", "issue", "view", str(q["issue"]), "--json", "state,comments"]))
        replies = [cm["body"] for cm in data["comments"]
                   if cm["author"]["login"].lower() == CONFIG["owner"].lower()]
        if not replies and data["state"] == "OPEN":
            still.append(q)
            continue
        answer = "\n\n---\n\n".join(replies) or "(The owner closed the issue without replying. Use your best judgment.)"
        saved = state["cycle"]
        state["cycle"] = q["cycle"]
        rel = next_memo(state, "human", q["from"])
        state["cycle"] = saved
        write_memo(rel, q["cycle"], "human", q["from"], "answer", "answer",
                   f"Answer to {q['memo']}", answer)
        if data["state"] == "OPEN":
            sh(["gh", "issue", "close", str(q["issue"]), "--comment",
                f"Thanks — copied into `{rel}`."], check=False)
        log(f"!! human answered issue #{q['issue']} -> {rel}")
        state["failures"] = 0
    changed = len(still) != len(state["pending_questions"])
    state["pending_questions"] = still
    if changed:
        checkpoint(state, "human", "human: answers from GitHub issues")


def ask_human_about_failure(state, err):
    rel = next_memo(state, "orchestrator", "human")
    write_memo(rel, state["cycle"], "orchestrator", "human", state["stage"], "question",
               f"Stage `{state['stage']}` keeps failing",
               f"The orchestrator failed {state['failures']} times in a row at stage "
               f"`{state['stage']}` step {state['step']}.\n\nLast error:\n\n```\n{err}\n```\n\n"
               f"Logs are in `logs/` on the machine running Agent Forge. Reply with any "
               f"instructions (or just 'retry') and the stage will be retried.", blocking=True)
    checkpoint(state, "orchestrator", f"forge: stage {state['stage']} failing, asking human")


# --------------------------------------------------------------------- main

def ensure_labels():
    for name, color in (("needs-human", "d93f0b"), ("forge-report", "0e8a16")):
        sh(["gh", "label", "create", name, "--color", color, "--force"], check=False)


def acquire_lock():
    LOG_DIR.mkdir(exist_ok=True)
    if LOCK.exists() and time.time() - LOCK.stat().st_mtime < 8 * 3600:
        pid = LOCK.read_text().strip()
        alive = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True,
                               text=True).stdout if os.name == "nt" else             ("" if not Path(f"/proc/{pid}").exists() else pid)
        if pid and pid in alive:
            return False
        log(f"removing stale lock from dead process {pid}")
    LOCK.write_text(str(os.getpid()))
    return True


def reload_config():
    global CONFIG
    CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))


def advance(state, force_new=False):
    reload_config()
    if state["stage"] == "idle":
        return stage_idle(state, force=force_new)
    try:
        progressed = STAGES[state["stage"]](state)
        state["failures"] = 0
        return progressed
    except Exception as e:  # noqa: BLE001 - every failure is logged and counted
        state["failures"] += 1
        log(f"!! stage {state['stage']} failed ({state['failures']}): {e}")
        save_state(state)
        if state["failures"] >= CONFIG["max_failures_per_step"]:
            ask_human_about_failure(state, str(e)[:3000])
        return False


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["run", "step", "new", "status"])
    ap.add_argument("--max-steps", type=int, default=40)
    args = ap.parse_args()

    if args.command == "status":
        print(json.dumps(load_state(), indent=2))
        return
    if not acquire_lock():
        log("another forge run is in progress; exiting")
        return
    try:
        git("pull", "-q", "--rebase", "--autostash", check=False)
        ensure_labels()
        state = load_state()
        force_new = args.command == "new"
        if force_new and state["stage"] != "idle":
            log(f"cycle {state['cycle']} is still at stage {state['stage']}; finish it before starting a new one")
            force_new = False
        steps = 1 if args.command == "step" else args.max_steps
        for _ in range(steps):
            collect_replies(state)
            if any(q["blocking"] for q in state["pending_questions"]):
                log("waiting on a blocking question for the human; see GitHub issues labelled needs-human")
                break
            if not advance(state, force_new):
                break
            force_new = False
            escalate_questions(state)
            if state["stage"] == "idle":
                break
        escalate_questions(state)
        checkpoint(state, "orchestrator", "forge: sync state")
    finally:
        LOCK.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
