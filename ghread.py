"""Read-only GitHub API access for the research and debate agents.

    python ghread.py repos/<owner>/<repo>/readme
    python ghread.py "search/repositories?q=topic:robotics&sort=stars" --jq ".items[].full_name"
    python ghread.py repos/<owner>/<repo>/contents --paginate

`gh api` can also create, change and delete things (`-X POST`, `-f field=...`), and a
tool allow-list can only match the start of a command. These agents get this wrapper
instead: it always sends GET and refuses every option except --jq and --paginate.
"""
import subprocess
import sys


def build(argv):
    """Turn our arguments into a `gh api` command, or raise ValueError."""
    if not argv:
        raise ValueError("usage: python ghread.py <api path> [--jq <filter>] [--paginate]")
    path, rest = argv[0], argv[1:]
    if path.startswith("-"):
        raise ValueError("the first argument must be an API path such as repos/<owner>/<repo>")
    if "://" in path or path.startswith("graphql"):
        raise ValueError("only REST paths on api.github.com are allowed")
    cmd = ["gh", "api", "--method", "GET", path]
    i = 0
    while i < len(rest):
        arg = rest[i]
        if arg in ("--jq", "-q"):
            if i + 1 >= len(rest):
                raise ValueError("--jq needs a filter")
            cmd += ["--jq", rest[i + 1]]
            i += 2
        elif arg == "--paginate":
            cmd.append(arg)
            i += 1
        else:
            raise ValueError(f"option not allowed: {arg} (only --jq and --paginate; this tool is read-only)")
    return cmd


def main(argv):
    try:
        cmd = build(argv)
    except ValueError as e:
        print(f"ghread: {e}", file=sys.stderr)
        return 2
    return subprocess.run(cmd).returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
