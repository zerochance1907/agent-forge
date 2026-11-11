#!/usr/bin/env python3
"""Preflight — a deterministic blast-radius risk-tier classifier for agent
shell commands.

Core entry point: classify_command(command, root=".") -> dict card.
The CLI (tier / classify / gate) is a thin wrapper over that function.
"""
from __future__ import annotations

import fnmatch
import json
import os
import re
import subprocess
import sys

TIERS = ("SAFE", "REVERSIBLE_LOCAL", "DESTRUCTIVE_LOCAL", "EXTERNAL", "UNKNOWN")

NETWORK_VERBS = {
    "curl", "wget", "ssh", "scp", "sftp", "nc", "ncat", "rsync",
    "aws", "gcloud", "az", "kubectl", "psql", "mysql",
}
DESTRUCTIVE_VERBS = {"rm", "rmdir", "mv", "dd", "truncate", "shred"}
REVERSIBLE_VERBS = {"mkdir", "touch", "cp"}
SAFE_VERBS = {
    "ls", "dir", "cat", "type", "head", "tail", "less", "more",
    "grep", "rg", "find", "pwd", "echo", "wc", "stat", "file",
}
GIT_EXTERNAL_SUBCOMMANDS = {"push", "pull", "fetch", "clone", "remote"}
GIT_SAFE_SUBCOMMANDS = {"status", "log", "diff", "show", "branch"}

URL_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")
USERHOST_RE = re.compile(r"^[\w.-]+@[\w.-]+:")
DOLLAR_VAR_RE = re.compile(r"\$\{|\$\(|\$[A-Za-z_][A-Za-z0-9_]*")
OBFUSCATION_LITERAL_TOKENS = {"|", ";", "&&", "||", "eval", "xargs"}


def _strip_quotes(tok: str) -> str:
    if len(tok) >= 2 and tok[0] == tok[-1] and tok[0] in ("'", '"'):
        return tok[1:-1]
    return tok


def _has_obfuscation(command: list[str]) -> bool:
    raw = " ".join(command)
    if "$(" in raw or "`" in raw or "${" in raw:
        return True
    for tok in command:
        stripped = _strip_quotes(tok)
        if stripped in OBFUSCATION_LITERAL_TOKENS:
            return True
        if stripped in ("sh", "bash") :
            continue
    # sh -c / bash -c as adjacent tokens anywhere
    for i in range(len(command) - 1):
        a, b = _strip_quotes(command[i]), _strip_quotes(command[i + 1])
        if a in ("sh", "bash") and b == "-c":
            return True
    # unresolved $VAR (but $( already caught above)
    for tok in command:
        stripped = _strip_quotes(tok)
        if DOLLAR_VAR_RE.search(stripped) and "$(" not in stripped:
            return True
    return False


def _leading_verb(command: list[str]) -> str:
    return _strip_quotes(command[0]) if command else ""


def _git_subcommand(command: list[str]) -> str:
    for tok in command[1:]:
        stripped = _strip_quotes(tok)
        if stripped.startswith("-"):
            continue
        return stripped
    return ""


def _is_external(command: list[str], verb: str) -> tuple[bool, str]:
    if verb in NETWORK_VERBS:
        return True, f"leading verb '{verb}' is a network/remote tool"
    if verb == "docker":
        sub = command[1] if len(command) > 1 else ""
        if sub in ("push", "pull"):
            return True, f"docker {sub} talks to a remote registry"
    if verb == "npm":
        sub = command[1] if len(command) > 1 else ""
        if sub in ("publish", "install"):
            return True, f"npm {sub} talks to the registry"
    if verb == "pip":
        sub = command[1] if len(command) > 1 else ""
        if sub == "install":
            return True, "pip install talks to a package index"
    if verb == "git":
        sub = _git_subcommand(command)
        if sub in GIT_EXTERNAL_SUBCOMMANDS:
            return True, f"git {sub} talks to a remote"
    for tok in command:
        stripped = _strip_quotes(tok)
        if URL_RE.match(stripped) or USERHOST_RE.match(stripped):
            return True, f"token '{stripped}' looks like a URL or user@host target"
    return False, ""


def _is_destructive_local(command: list[str], verb: str) -> tuple[bool, str]:
    if verb in DESTRUCTIVE_VERBS:
        return True, f"leading verb '{verb}' destroys local files/data"
    if verb == "git":
        sub = _git_subcommand(command)
        if sub == "reset" and "--hard" in [_strip_quotes(t) for t in command]:
            return True, "git reset --hard discards local working-tree changes"
        if sub == "clean":
            return True, "git clean removes untracked local files"
        if sub == "checkout":
            flags = [_strip_quotes(t) for t in command]
            if "-f" in flags or "--" in flags:
                return True, "git checkout -- / -f discards local changes"
        if sub == "restore":
            return True, "git restore overwrites local working-tree changes"
    for tok in command:
        stripped = _strip_quotes(tok)
        if stripped == ">":
            return True, "output-truncating redirect '>' overwrites a file"
    return False, ""


def _is_reversible_local(command: list[str], verb: str) -> tuple[bool, str]:
    if verb in REVERSIBLE_VERBS:
        return True, f"leading verb '{verb}' makes a locally-undoable change"
    if verb == "git":
        sub = _git_subcommand(command)
        flags = [_strip_quotes(t) for t in command]
        if sub == "checkout" and "-b" in flags:
            return True, "git checkout -b creates a new branch (undoable)"
        if sub in ("add", "commit", "stash"):
            return True, f"git {sub} is locally reversible"
    return False, ""


def _is_safe(command: list[str], verb: str) -> tuple[bool, str]:
    if verb == "find":
        flags = [_strip_quotes(t) for t in command]
        if "-delete" in flags or "-exec" in flags:
            return False, ""
        return True, "find without -delete/-exec is read-only"
    if verb in SAFE_VERBS:
        return True, f"leading verb '{verb}' is read-only"
    if verb == "git":
        sub = _git_subcommand(command)
        if sub in GIT_SAFE_SUBCOMMANDS:
            return True, f"git {sub} is read-only"
    return False, ""


def _classify_tier(command: list[str]) -> tuple[str, list[str]]:
    if not command:
        return "UNKNOWN", ["empty command"]
    if _has_obfuscation(command):
        return "UNKNOWN", ["command uses obfuscation/indirection outside the bounded grammar"]
    verb = _leading_verb(command)

    ok, reason = _is_external(command, verb)
    if ok:
        return "EXTERNAL", [reason]

    ok, reason = _is_destructive_local(command, verb)
    if ok:
        return "DESTRUCTIVE_LOCAL", [reason]

    ok, reason = _is_reversible_local(command, verb)
    if ok:
        return "REVERSIBLE_LOCAL", [reason]

    ok, reason = _is_safe(command, verb)
    if ok:
        return "SAFE", [reason]

    return "UNKNOWN", [f"leading verb '{verb}' is not in the bounded grammar"]


def _is_glob(path: str) -> bool:
    return any(ch in path for ch in "*?[")


def _path_args(command: list[str]) -> list[str]:
    """Positional (non-flag) arguments after the leading verb."""
    out = []
    for tok in command[1:]:
        stripped = _strip_quotes(tok)
        if stripped.startswith("-") and stripped != "-":
            continue
        out.append(stripped)
    return out


def _expand_paths(paths: list[str], root: str) -> list[str] | None:
    """Expand literal/simple-glob paths relative to root. None if unparseable."""
    expanded: list[str] = []
    for p in paths:
        if any(ch in p for ch in "$`|;&()"):
            return None
        full = os.path.join(root, p) if not os.path.isabs(p) else p
        if _is_glob(p):
            base_dir = os.path.dirname(full) or root
            pattern = os.path.basename(full)
            if not os.path.isdir(base_dir):
                continue
            for name in os.listdir(base_dir):
                if fnmatch.fnmatch(name, pattern):
                    expanded.append(os.path.join(base_dir, name))
        else:
            expanded.append(full)
    return expanded


def _walk_files(path: str) -> list[str]:
    if os.path.isfile(path):
        return [path]
    if os.path.isdir(path):
        files = []
        for dirpath, _dirs, filenames in os.walk(path):
            for fn in filenames:
                files.append(os.path.join(dirpath, fn))
        return files
    return []


def _git_uncommitted_set(root: str) -> set[str] | None:
    try:
        top = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=root, capture_output=True, text=True, timeout=10,
        )
        if top.returncode != 0:
            return None
        repo_root = top.stdout.strip()
        out = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=root, capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    uncommitted = set()
    for line in out.stdout.splitlines():
        if len(line) < 4:
            continue
        rel = line[3:].strip()
        if " -> " in rel:
            rel = rel.split(" -> ", 1)[1]
        uncommitted.add(os.path.normpath(os.path.join(repo_root, rel)))
    return uncommitted


def _enrich_local(command: list[str], verb: str, tier: str, root: str) -> tuple[int | None, int | None]:
    if tier not in ("DESTRUCTIVE_LOCAL", "REVERSIBLE_LOCAL"):
        return None, None
    if verb == "git":
        return None, None  # git destructive/reversible ops aren't simple path globs

    raw_paths = _path_args(command)
    if not raw_paths:
        return None, None
    expanded = _expand_paths(raw_paths, root)
    if expanded is None:
        return None, None

    if verb in ("mkdir", "touch"):
        return len(expanded), 0
    if verb == "cp":
        # last arg is the destination; sources are what's "affected" to read
        sources = expanded[:-1] if len(expanded) > 1 else expanded
        return len(sources), 0

    all_files: list[str] = []
    for p in expanded:
        all_files.extend(_walk_files(p))
    files_affected = len(all_files)

    uncommitted = _git_uncommitted_set(root)
    if uncommitted is None:
        uncommitted_at_risk = None
    else:
        norm_files = {os.path.normpath(os.path.abspath(f)) for f in all_files}
        uncommitted_at_risk = len(norm_files & uncommitted)
    return files_affected, uncommitted_at_risk


def classify_command(command: list[str], root: str = ".") -> dict:
    """Classify a tokenized shell command. Returns the blast-radius card dict."""
    tier, reasons = _classify_tier(command)
    verb = _leading_verb(command)
    files_affected, uncommitted_at_risk = _enrich_local(command, verb, tier, root)
    return {
        "action": " ".join(command),
        "tier": tier,
        "reversible": tier in ("SAFE", "REVERSIBLE_LOCAL"),
        "networked": tier == "EXTERNAL",
        "files_affected": files_affected,
        "uncommitted_at_risk": uncommitted_at_risk,
        "external_system": tier == "EXTERNAL",
        "reasons": reasons,
    }


# --------------------------------------------------------------------------
# Wild twist: an ASCII "blast radius map" rendered from the real numbers.
# Purely cosmetic (never appears in --json output) but genuinely driven by
# files_affected / uncommitted_at_risk / tier — not hardcoded per tier.
# --------------------------------------------------------------------------
def _blast_radius_map(card: dict) -> str:
    tier = card["tier"]
    if tier == "EXTERNAL":
        return (
            "         . . . ~~~ R I P P L E   O U T ~~~ . . .\n"
            "                 (( ( (  🌐  ) ) ))\n"
            "         leaves the local blast radius entirely\n"
        )
    if tier == "UNKNOWN":
        return (
            "                 ░▒▓█ F O G █▓▒░\n"
            "               ?   ?   ?   ?   ?\n"
            "         radius unmeasurable — treated as destructive\n"
        )

    affected = card["files_affected"] or 0
    at_risk = card["uncommitted_at_risk"] or 0
    safe_dots = max(0, affected - at_risk)
    n = min(affected, 24) if affected else 0

    safe_glyphs = min(safe_dots, n)
    risk_glyphs = n - safe_glyphs
    marks = ("✖ " * risk_glyphs) + ("● " * safe_glyphs)
    if not marks:
        marks = "(nothing in the blast radius)"

    ring = "░" * (14 + min(n, 16))
    pad = " " * 4
    lines = [
        f"{pad}{ring}",
        f"{pad[:2]}  {marks.strip()}",
        f"{pad}{ring}",
    ]
    legend = f"  ✖={at_risk} uncommitted-at-risk   ●={safe_dots} tracked/clean"
    return "Blast Radius Map\n" + "\n".join(lines) + "\n" + legend + "\n"


def render_card(card: dict) -> str:
    lines = [
        f"ACTION:  {card['action']}",
        f"TIER:    {card['tier']}",
        f"REVERSIBLE:  {card['reversible']}",
        f"NETWORKED:   {card['networked']}",
        f"FILES AFFECTED:       {card['files_affected']}",
        f"UNCOMMITTED AT RISK:  {card['uncommitted_at_risk']}",
        f"EXTERNAL SYSTEM:      {card['external_system']}",
        "REASONS:",
    ]
    for r in card["reasons"]:
        lines.append(f"  - {r}")
    lines.append("")
    lines.append(_blast_radius_map(card).rstrip())
    lines.append("")
    lines.append(f"TIER: {card['tier']}")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def _split_args(argv: list[str]) -> tuple[str, dict, list[str]]:
    subcommand = None
    flags = {"json": False, "auto_approve_safe": False}
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok in ("tier", "classify", "gate"):
            subcommand = tok
            i += 1
            break
        if tok == "--json":
            flags["json"] = True
        elif tok == "--auto-approve-safe":
            flags["auto_approve_safe"] = True
        else:
            raise SystemExit(f"preflight: unknown option '{tok}'")
        i += 1
    if subcommand is None:
        raise SystemExit("preflight: missing subcommand (tier|classify|gate)")
    if i >= len(argv) or argv[i] != "--":
        raise SystemExit("preflight: expected '--' before the command")
    command = argv[i + 1:]
    return subcommand, flags, command


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    try:
        subcommand, flags, command = _split_args(argv)
    except SystemExit as e:
        print(str(e), file=sys.stderr)
        return 2

    if subcommand == "tier":
        tier, _reasons = _classify_tier(command)
        print(tier)
        return 0

    if subcommand == "classify":
        card = classify_command(command)
        if flags["json"]:
            print(json.dumps(card))
        else:
            print(render_card(card))
        return 0

    if subcommand == "gate":
        card = classify_command(command)
        tier = card["tier"]
        auto_ok = flags["auto_approve_safe"] and tier in ("SAFE", "REVERSIBLE_LOCAL")
        if auto_ok:
            print(f"AUTO-APPROVED {tier}")
            return 0
        print(f"PAUSE {tier}")
        return 10

    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
