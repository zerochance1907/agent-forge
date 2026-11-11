#!/usr/bin/env python3
"""Preflight: deterministic blast-radius risk-tier classifier for shell commands.

Usage:
    python preflight.py tier -- <command tokens...>
    python preflight.py [--json] classify -- <command tokens...>
    python preflight.py [--auto-approve-safe] gate -- <command tokens...>

See README.md for the full tier table and the safety defaults.
"""

from __future__ import annotations

import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

TIERS = ("SAFE", "REVERSIBLE_LOCAL", "DESTRUCTIVE_LOCAL", "EXTERNAL", "UNKNOWN")

PUNCTUATION_CHARS = "();<>|&;"

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

GIT_EXTERNAL_SUBS = {"push", "pull", "fetch", "clone", "remote"}
GIT_REVERSIBLE_SUBS = {"add", "commit", "stash"}
GIT_SAFE_SUBS = {"status", "log", "diff", "show", "branch"}

URL_RE = re.compile(r"(https?|ftp)://\S+")
USER_HOST_RE = re.compile(r"^[\w.\-]+@[\w.\-]+:")
DOLLAR_VAR_RE = re.compile(r"\$[A-Za-z_][A-Za-z0-9_]*")
SH_C_RE = re.compile(r"\b(sh|bash)\s+-c\b")
SIMPLE_PATH_RE = re.compile(r"^[A-Za-z0-9_./*?\[\]:\\-]+$")


def _tokenize(command_str: str) -> list[str]:
    """Tokenize respecting simple quotes; shell operators become their own tokens."""
    lexer = shlex.shlex(command_str, posix=True, punctuation_chars=PUNCTUATION_CHARS)
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError:
        # Unbalanced quote etc. -- fall back to naive split, caller treats as UNKNOWN-prone.
        return command_str.split()


def _is_punct(token: str) -> bool:
    return len(token) > 0 and all(c in PUNCTUATION_CHARS for c in token)


def _words(tokens: list[str]) -> list[str]:
    return [t for t in tokens if not _is_punct(t)]


def _obfuscation_reason(command_str: str, tokens: list[str]) -> str | None:
    if "$(" in command_str:
        return "command substitution $(...) is unresolved indirection"
    if "`" in command_str:
        return "backtick command substitution is unresolved indirection"
    if "${" in command_str:
        return "parameter expansion ${...} is unresolved indirection"
    if DOLLAR_VAR_RE.search(command_str):
        return "unresolved $VAR reference"
    for t in tokens:
        if t in ("|", "||", ";", "&&", "&"):
            return f"shell operator '{t}' is outside the bounded grammar"
    if "eval" in tokens:
        return "'eval' is unresolved indirection"
    if "xargs" in tokens:
        return "'xargs' is unresolved indirection"
    if SH_C_RE.search(command_str):
        return "'sh -c'/'bash -c' delegates to an unparsed sub-shell"
    return None


def _is_external(verb: str, sub: str, words: list[str], command_str: str) -> bool:
    if verb in EXTERNAL_VERBS:
        return True
    if verb == "docker" and sub in ("push", "pull"):
        return True
    if verb == "npm" and sub in ("publish", "install"):
        return True
    if verb == "pip" and sub == "install":
        return True
    if verb == "git" and sub in GIT_EXTERNAL_SUBS:
        return True
    for t in words:
        if URL_RE.search(t) or USER_HOST_RE.match(t):
            return True
    return False


def _is_destructive(verb: str, sub: str, words: list[str], tokens: list[str]) -> bool:
    if verb in DESTRUCTIVE_VERBS:
        return True
    if verb == "git":
        if sub == "reset" and "--hard" in words:
            return True
        if sub == "clean":
            return True
        if sub == "checkout" and ("--" in words or "-f" in words):
            return True
        if sub == "restore":
            return True
    if ">" in tokens:
        return True
    return False


def _is_reversible(verb: str, sub: str, words: list[str]) -> bool:
    if verb in REVERSIBLE_VERBS:
        return True
    if verb == "git":
        if sub in GIT_REVERSIBLE_SUBS:
            return True
        if sub == "checkout" and "-b" in words:
            return True
    return False


def _is_safe(verb: str, sub: str, words: list[str]) -> bool:
    if verb == "find":
        return "-delete" not in words and "-exec" not in words
    if verb in SAFE_VERBS:
        return True
    if verb == "git" and sub in GIT_SAFE_SUBS:
        return True
    return False


def _path_args(verb: str, words: list[str]) -> list[str]:
    body = words[1:]
    if verb == "git" and body:
        body = body[1:]
    return [w for w in body if w and not w.startswith("-")]


def _enrich_tree(verb: str, words: list[str], root: str) -> tuple[int | None, int | None]:
    args = _path_args(verb, words)
    if not args:
        return 0, 0
    for a in args:
        if not SIMPLE_PATH_RE.match(a):
            return None, None

    root_path = Path(root)
    matched: set[Path] = set()
    for a in args:
        if any(c in a for c in "*?["):
            hits = list(root_path.glob(a))
        else:
            candidate = root_path / a
            hits = [candidate] if candidate.exists() else []
        for h in hits:
            if h.is_dir():
                matched.update(f for f in h.rglob("*") if f.is_file())
            elif h.exists():
                matched.add(h)

    files_affected = len(matched)

    uncommitted_at_risk = None
    try:
        proc = subprocess.run(
            ["git", "-C", str(root_path), "status", "--porcelain", "-uall"],
            capture_output=True, text=True, timeout=10, check=False,
        )
        if proc.returncode == 0:
            dirty: set[str] = set()
            for line in proc.stdout.splitlines():
                if not line:
                    continue
                path_part = line[3:]
                if " -> " in path_part:
                    path_part = path_part.split(" -> ", 1)[1]
                dirty.add(path_part.strip().strip('"'))
            resolved_dirty = {(Path(root) / d).resolve() for d in dirty}
            uncommitted_at_risk = sum(1 for m in matched if m.resolve() in resolved_dirty)
    except (OSError, subprocess.SubprocessError):
        uncommitted_at_risk = None

    return files_affected, uncommitted_at_risk


def classify_command(command, root: str = ".") -> dict:
    """Classify a shell command string (or token list) and return a blast-radius card."""
    command_str = command if isinstance(command, str) else " ".join(command)
    tokens = _tokenize(command_str)
    words = _words(tokens)
    verb = words[0] if words else ""
    sub = words[1] if len(words) > 1 else ""

    reasons: list[str] = []
    obf = _obfuscation_reason(command_str, tokens)
    if obf is not None:
        tier = "UNKNOWN"
        reasons.append(obf)
    elif _is_external(verb, sub, words, command_str):
        tier = "EXTERNAL"
        reasons.append(f"'{verb}' reaches a networked/remote system")
    elif _is_destructive(verb, sub, words, tokens):
        tier = "DESTRUCTIVE_LOCAL"
        reasons.append(f"'{verb}' performs an irreversible local change")
    elif _is_reversible(verb, sub, words):
        tier = "REVERSIBLE_LOCAL"
        reasons.append(f"'{verb}' performs a locally reversible change")
    elif _is_safe(verb, sub, words):
        tier = "SAFE"
        reasons.append(f"'{verb}' is read-only")
    else:
        tier = "UNKNOWN"
        reasons.append(f"verb '{verb}' is not recognized by the bounded grammar")

    files_affected = None
    uncommitted_at_risk = None
    if tier in ("DESTRUCTIVE_LOCAL", "REVERSIBLE_LOCAL"):
        files_affected, uncommitted_at_risk = _enrich_tree(verb, words, root)

    return {
        "action": command_str,
        "tier": tier,
        "reversible": tier in ("SAFE", "REVERSIBLE_LOCAL"),
        "networked": tier == "EXTERNAL",
        "files_affected": files_affected,
        "uncommitted_at_risk": uncommitted_at_risk,
        "external_system": tier == "EXTERNAL",
        "reasons": reasons,
    }


def _parse_argv(argv: list[str]) -> tuple[str, dict, str]:
    try:
        sep = argv.index("--")
    except ValueError:
        print("error: missing '--' separator before the command", file=sys.stderr)
        sys.exit(2)
    before, after = argv[:sep], argv[sep + 1:]
    flags = {t for t in before if t.startswith("--")}
    subcommand = next((t for t in before if not t.startswith("--")), None)
    if subcommand not in ("tier", "classify", "gate"):
        print(f"error: unknown subcommand {subcommand!r}", file=sys.stderr)
        sys.exit(2)
    command_str = " ".join(after)
    return subcommand, flags, command_str


def _print_card(card: dict) -> None:
    print(f"Command              : {card['action']}")
    print(f"Tier                 : {card['tier']}")
    print(f"Reversible           : {card['reversible']}")
    print(f"Networked            : {card['networked']}")
    print(f"Files affected       : {card['files_affected']}")
    print(f"Uncommitted at risk  : {card['uncommitted_at_risk']}")
    if card["reasons"]:
        print("Reasons:")
        for r in card["reasons"]:
            print(f"  - {r}")
    print(f"TIER: {card['tier']}")


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    subcommand, flags, command_str = _parse_argv(argv)

    if subcommand == "tier":
        card = classify_command(command_str)
        print(card["tier"])
        return 0

    if subcommand == "classify":
        card = classify_command(command_str)
        if "--json" in flags:
            print(json.dumps(card))
        else:
            _print_card(card)
        return 0

    if subcommand == "gate":
        card = classify_command(command_str)
        tier = card["tier"]
        auto_approve = "--auto-approve-safe" in flags
        if auto_approve and tier in ("SAFE", "REVERSIBLE_LOCAL"):
            print(f"AUTO-APPROVED {tier}")
            return 0
        print(f"PAUSE {tier}")
        return 10

    return 2


if __name__ == "__main__":
    sys.exit(main())
