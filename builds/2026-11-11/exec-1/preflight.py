#!/usr/bin/env python3
"""Preflight: deterministic blast-radius risk-tier classifier for shell commands.

python preflight.py tier -- <command tokens...>
python preflight.py [--json] classify -- <command tokens...>
python preflight.py [--auto-approve-safe] gate -- <command tokens...>
"""
import glob
import json
import os
import re
import shlex
import subprocess
import sys

TIERS = ("SAFE", "REVERSIBLE_LOCAL", "DESTRUCTIVE_LOCAL", "EXTERNAL", "UNKNOWN")

EXTERNAL_VERBS = {
    "curl", "wget", "ssh", "scp", "sftp", "nc", "ncat", "rsync",
    "aws", "gcloud", "az", "kubectl", "psql", "mysql",
}
DESTRUCTIVE_VERBS = {"rm", "rmdir", "mv", "dd", "truncate", "shred"}
REVERSIBLE_VERBS = {"mkdir", "touch", "cp"}
SAFE_VERBS = {
    "ls", "dir", "cat", "type", "head", "tail", "less", "more",
    "grep", "rg", "find", "pwd", "echo", "wc", "stat", "file",
}
URL_RE = re.compile(r"\b\w+://")
USER_HOST_RE = re.compile(r"^[\w.-]+@[\w.-]+:")
VAR_RE = re.compile(r"\$[A-Za-z_]")


def tokenize(command):
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def _has_obfuscation(raw, tokens):
    if "$(" in raw or "`" in raw or "${" in raw:
        return True
    if VAR_RE.search(raw):
        return True
    if "|" in raw or ";" in raw or "&&" in raw:
        return True
    lowered = [t.lower() for t in tokens]
    if "eval" in lowered or "xargs" in lowered:
        return True
    if lowered and lowered[0] in ("sh", "bash") and "-c" in lowered:
        return True
    return False


def _is_external(tokens):
    if not tokens:
        return False
    verb = tokens[0].lower()
    if verb in EXTERNAL_VERBS:
        return True
    if verb == "docker" and len(tokens) > 1 and tokens[1] in ("push", "pull"):
        return True
    if verb in ("npm",) and len(tokens) > 1 and tokens[1] in ("publish", "install"):
        return True
    if verb in ("pip", "pip3") and len(tokens) > 1 and tokens[1] == "install":
        return True
    if verb == "git" and len(tokens) > 1 and tokens[1] in ("push", "pull", "fetch", "clone", "remote"):
        return True
    for t in tokens:
        if URL_RE.search(t) or USER_HOST_RE.match(t):
            return True
    return False


def _is_destructive_local(tokens, raw):
    if not tokens:
        return False
    verb = tokens[0].lower()
    if verb in DESTRUCTIVE_VERBS:
        return True
    if verb == "git" and len(tokens) > 1:
        sub = tokens[1]
        if sub == "reset" and "--hard" in tokens:
            return True
        if sub == "clean":
            return True
        if sub == "checkout" and ("--" in tokens or "-f" in tokens):
            return True
        if sub == "restore":
            return True
    if re.search(r"(?<!>)>(?!>)", raw):
        return True
    return False


def _is_reversible_local(tokens):
    if not tokens:
        return False
    verb = tokens[0].lower()
    if verb in REVERSIBLE_VERBS:
        return True
    if verb == "git" and len(tokens) > 1:
        sub = tokens[1]
        if sub in ("add", "commit", "stash"):
            return True
        if sub == "checkout" and "-b" in tokens:
            return True
    return False


def _is_safe(tokens):
    if not tokens:
        return False
    verb = tokens[0].lower()
    if verb == "find":
        return not ("-delete" in tokens or "-exec" in tokens)
    if verb in SAFE_VERBS:
        return True
    if verb == "git" and len(tokens) > 1 and tokens[1] in ("status", "log", "diff", "show", "branch"):
        return True
    return False


def classify_tier(command):
    tokens = tokenize(command)
    if _has_obfuscation(command, tokens):
        return "UNKNOWN"
    if _is_external(tokens):
        return "EXTERNAL"
    if _is_destructive_local(tokens, command):
        return "DESTRUCTIVE_LOCAL"
    if _is_reversible_local(tokens):
        return "REVERSIBLE_LOCAL"
    if _is_safe(tokens):
        return "SAFE"
    return "UNKNOWN"


def _reason_for(tier, tokens):
    verb = tokens[0] if tokens else ""
    if tier == "UNKNOWN":
        return [f"command uses indirection/obfuscation or an unrecognized verb ('{verb}')"]
    if tier == "EXTERNAL":
        return [f"leading verb '{verb}' (or a URL/user@host token) talks to a network/remote system"]
    if tier == "DESTRUCTIVE_LOCAL":
        return [f"leading verb '{verb}' (or output-truncating redirect) is destructive to the local tree"]
    if tier == "REVERSIBLE_LOCAL":
        return [f"leading verb '{verb}' makes a locally reversible change"]
    if tier == "SAFE":
        return [f"leading verb '{verb}' is read-only"]
    return []


_PATH_VERBS = {"rm", "rmdir", "mv", "dd", "truncate", "shred", "mkdir", "touch", "cp"}


def _matched_paths(root, tokens):
    """Expand non-flag arguments (after the verb) as literal/glob paths."""
    verb = tokens[0].lower() if tokens else ""
    if verb not in _PATH_VERBS:
        return None
    args = [t for t in tokens[1:] if not t.startswith("-")]
    if not args:
        return None
    matched = []
    for a in args:
        pattern = os.path.join(root, a)
        if any(c in a for c in "*?["):
            matched.extend(glob.glob(pattern))
        elif os.path.exists(pattern):
            matched.append(pattern)
    return matched


def _enrich_local(root, tokens):
    """Return (files_affected, uncommitted_at_risk) or (None, None)."""
    matched = _matched_paths(root, tokens)
    if matched is None:
        return None, None

    abs_files = []
    for p in matched:
        if os.path.isdir(p):
            for dirpath, _dirnames, filenames in os.walk(p):
                for f in filenames:
                    abs_files.append(os.path.abspath(os.path.join(dirpath, f)))
        elif os.path.isfile(p):
            abs_files.append(os.path.abspath(p))

    uncommitted, toplevel = _uncommitted_set(root)
    if uncommitted is None:
        return len(abs_files), None

    at_risk = 0
    for af in abs_files:
        rel = os.path.relpath(af, toplevel).replace("\\", "/")
        if _is_uncommitted(rel, uncommitted):
            at_risk += 1
    return len(abs_files), at_risk


def _is_uncommitted(file_rel, uncommitted):
    if file_rel in uncommitted:
        return True
    # git collapses a wholly-untracked directory into a single "dir/" entry
    return any(u.endswith("/") and file_rel.startswith(u) for u in uncommitted)


def _uncommitted_set(root):
    """Uncommitted paths, relative to the repo toplevel (not `root`), plus the toplevel itself."""
    try:
        tl = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=root, capture_output=True, text=True, timeout=5,
        )
        if tl.returncode != 0:
            return None, None
        toplevel = tl.stdout.strip()
        out = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root, capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None, None
    if out.returncode != 0:
        return None, None
    paths = set()
    for line in out.stdout.splitlines():
        if len(line) < 4:
            continue
        rest = line[3:]
        if " -> " in rest:
            rest = rest.split(" -> ", 1)[1]
        paths.add(rest.strip().strip('"').replace("\\", "/"))
    return paths, toplevel


def classify_command(command, root="."):
    tokens = tokenize(command)
    tier = classify_tier(command)

    files_affected = None
    uncommitted_at_risk = None
    if tier in ("DESTRUCTIVE_LOCAL", "REVERSIBLE_LOCAL"):
        files_affected, uncommitted_at_risk = _enrich_local(root, tokens)

    return {
        "action": command,
        "tier": tier,
        "reversible": tier in ("SAFE", "REVERSIBLE_LOCAL"),
        "networked": tier == "EXTERNAL",
        "files_affected": files_affected,
        "uncommitted_at_risk": uncommitted_at_risk,
        "external_system": tier == "EXTERNAL",
        "reasons": _reason_for(tier, tokens),
    }


def _split_argv(argv):
    """Split argv into (leading flags+subcommand, command tokens) on the first '--'."""
    if "--" not in argv:
        raise SystemExit("error: missing '--' separator before the command")
    idx = argv.index("--")
    head, tail = argv[:idx], argv[idx + 1:]
    return head, tail


def _render_card(card):
    lines = [
        f"Command: {card['action']}",
        f"Tier: {card['tier']}",
        f"Reversible: {'yes' if card['reversible'] else 'no'}",
        f"Networked: {'yes' if card['networked'] else 'no'}",
        f"Files affected: {card['files_affected']}",
        f"Uncommitted at risk: {card['uncommitted_at_risk']}",
        f"External system: {'yes' if card['external_system'] else 'no'}",
        "Reasons:",
    ]
    for r in card["reasons"]:
        lines.append(f"  - {r}")
    lines.append(f"TIER: {card['tier']}")
    return "\n".join(lines)


def main(argv):
    if not argv:
        print("usage: preflight.py {tier|classify|gate} [flags] -- <command...>", file=sys.stderr)
        return 2

    head, tail = _split_argv(argv)
    flags = [h for h in head if h.startswith("-")]
    subs = [h for h in head if not h.startswith("-")]
    if len(subs) != 1:
        print("usage: preflight.py {tier|classify|gate} [flags] -- <command...>", file=sys.stderr)
        return 2
    sub = subs[0]
    command = " ".join(tail)

    if sub == "tier":
        print(classify_tier(command))
        return 0

    if sub == "classify":
        card = classify_command(command)
        if "--json" in flags:
            print(json.dumps(card))
        else:
            print(_render_card(card))
        return 0

    if sub == "gate":
        tier = classify_tier(command)
        auto_approve = "--auto-approve-safe" in flags
        if auto_approve and tier in ("SAFE", "REVERSIBLE_LOCAL"):
            print(f"AUTO-APPROVED {tier}")
            return 0
        print(f"PAUSE {tier}")
        return 10

    print(f"unknown subcommand: {sub}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
