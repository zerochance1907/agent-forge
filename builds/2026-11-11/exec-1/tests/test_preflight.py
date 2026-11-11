import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import preflight  # noqa: E402

CONSENSUS_FIXTURES = [
    ("ls -la", "SAFE"),
    ("cat README.md", "SAFE"),
    ("rm -rf build", "DESTRUCTIVE_LOCAL"),
    ("mv old.txt new.txt", "DESTRUCTIVE_LOCAL"),
    ("git reset --hard HEAD", "DESTRUCTIVE_LOCAL"),
    ("curl -X POST https://api.example.com/charges", "EXTERNAL"),
    ("git push origin main", "EXTERNAL"),
    ("mkdir newdir", "REVERSIBLE_LOCAL"),
    ("frobnicate --wild", "UNKNOWN"),
]

OBFUSCATION_FIXTURES = [
    "$(rm -rf /)",
    "echo `whoami`",
    "ls | grep foo",
    "ls ; rm -rf /",
    "ls && rm -rf /",
    "eval ls",
    "sh -c ls",
    "rm $HOME/foo",
    "xargs rm",
]

ADDITIONAL_TIER_FIXTURES = [
    ("rmdir old", "DESTRUCTIVE_LOCAL"),
    ("dd if=/dev/zero of=disk.img", "DESTRUCTIVE_LOCAL"),
    ("git clean -fd", "DESTRUCTIVE_LOCAL"),
    ("git checkout -- file.txt", "DESTRUCTIVE_LOCAL"),
    ("echo hi > out.txt", "DESTRUCTIVE_LOCAL"),
    ("echo hi >> out.txt", "SAFE"),  # append (>>) is not a truncating redirect; echo is read-only
    ("touch newfile", "REVERSIBLE_LOCAL"),
    ("cp a.txt b.txt", "REVERSIBLE_LOCAL"),
    ("git add file.txt", "REVERSIBLE_LOCAL"),
    ("git checkout -b feature", "REVERSIBLE_LOCAL"),
    ("git status", "SAFE"),
    ("git log", "SAFE"),
    ("find . -name '*.py'", "SAFE"),
    ("find . -delete", "UNKNOWN"),
    ("ssh user@host ls", "EXTERNAL"),
    ("scp file user@host:/tmp", "EXTERNAL"),
    ("npm install left-pad", "EXTERNAL"),
    ("pip install requests", "EXTERNAL"),
    ("docker push myimage", "EXTERNAL"),
    ("aws s3 ls", "EXTERNAL"),
]


@pytest.mark.parametrize("cmd,expected", CONSENSUS_FIXTURES)
def test_consensus_fixtures(cmd, expected):
    assert preflight.classify_tier(cmd) == expected


@pytest.mark.parametrize("cmd", OBFUSCATION_FIXTURES)
def test_obfuscation_is_unknown(cmd):
    assert preflight.classify_tier(cmd) == "UNKNOWN"


@pytest.mark.parametrize("cmd,expected", ADDITIONAL_TIER_FIXTURES)
def test_additional_tier_fixtures(cmd, expected):
    assert preflight.classify_tier(cmd) == expected


def test_tier_cli_prints_only_the_tier(tmp_path):
    result = subprocess.run(
        [sys.executable, _preflight_path(), "tier", "--", "ls", "-la"],
        capture_output=True, text=True, cwd=tmp_path,
    )
    assert result.stdout == "SAFE\n"
    assert result.returncode == 0


def test_classify_card_ends_with_tier_line(tmp_path):
    result = subprocess.run(
        [sys.executable, _preflight_path(), "classify", "--", "rm", "-rf", "nope"],
        capture_output=True, text=True, cwd=tmp_path,
    )
    lines = result.stdout.strip().splitlines()
    assert lines[-1] == "TIER: DESTRUCTIVE_LOCAL"


def test_classify_json_has_all_fields(tmp_path):
    result = subprocess.run(
        [sys.executable, _preflight_path(), "--json", "classify", "--", "rm", "-rf", "nope"],
        capture_output=True, text=True, cwd=tmp_path,
    )
    card = json.loads(result.stdout)
    for field in (
        "action", "tier", "reversible", "networked",
        "files_affected", "uncommitted_at_risk", "external_system", "reasons",
    ):
        assert field in card


def test_gate_defaults_to_pause_on_everything():
    for cmd in ("ls -la", "mkdir x", "rm -rf x", "git push origin main", "wat"):
        result = subprocess.run(
            [sys.executable, _preflight_path(), "gate", "--", *cmd.split()],
            capture_output=True, text=True,
        )
        assert result.stdout.startswith("PAUSE ")
        assert result.returncode == 10


def test_gate_auto_approve_safe_only_approves_safe_and_reversible():
    approved = ("ls -la", "mkdir x")
    paused = ("rm -rf x", "git push origin main", "wat")
    for cmd in approved:
        result = subprocess.run(
            [sys.executable, _preflight_path(), "--auto-approve-safe", "gate", "--", *cmd.split()],
            capture_output=True, text=True,
        )
        assert result.stdout.startswith("AUTO-APPROVED ")
        assert result.returncode == 0
    for cmd in paused:
        result = subprocess.run(
            [sys.executable, _preflight_path(), "--auto-approve-safe", "gate", "--", *cmd.split()],
            capture_output=True, text=True,
        )
        assert result.stdout.startswith("PAUSE ")
        assert result.returncode == 10


def _run_git(args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def fixture_repo(tmp_path):
    """A standalone git repo, with a nested subdir, mimicking a real working tree."""
    repo = tmp_path / "repo"
    sub = repo / "sub"
    sub.mkdir(parents=True)
    _run_git(["init", "-q"], cwd=repo)
    _run_git(["config", "user.email", "t@example.com"], cwd=repo)
    _run_git(["config", "user.name", "t"], cwd=repo)
    (repo / "tracked.txt").write_text("hi")
    _run_git(["add", "tracked.txt"], cwd=repo)
    _run_git(["commit", "-q", "-m", "init"], cwd=repo)

    build = sub / "build"
    build.mkdir()
    (build / "a.txt").write_text("a")
    (build / "b.txt").write_text("b")
    (build / "c.txt").write_text("c")
    return repo, sub


def test_files_affected_and_uncommitted_at_risk_from_repo_root(fixture_repo):
    repo, sub = fixture_repo
    card = preflight.classify_command("rm -rf sub/build", root=str(repo))
    assert card["tier"] == "DESTRUCTIVE_LOCAL"
    assert card["files_affected"] == 3
    assert card["uncommitted_at_risk"] == 3


def test_files_affected_and_uncommitted_at_risk_from_nested_cwd(fixture_repo):
    repo, sub = fixture_repo
    card = preflight.classify_command("rm -rf build", root=str(sub))
    assert card["tier"] == "DESTRUCTIVE_LOCAL"
    assert card["files_affected"] == 3
    assert card["uncommitted_at_risk"] == 3


def test_uncommitted_at_risk_excludes_committed_files(fixture_repo):
    repo, sub = fixture_repo
    _run_git(["add", "sub/build"], cwd=repo)
    _run_git(["commit", "-q", "-m", "commit build"], cwd=repo)
    card = preflight.classify_command("rm -rf build", root=str(sub))
    assert card["files_affected"] == 3
    assert card["uncommitted_at_risk"] == 0


def test_nonlocal_command_has_null_file_counts():
    card = preflight.classify_command("git push origin main")
    assert card["files_affected"] is None
    assert card["uncommitted_at_risk"] is None


def test_safe_command_has_null_file_counts():
    card = preflight.classify_command("ls -la")
    assert card["files_affected"] is None
    assert card["uncommitted_at_risk"] is None


def _preflight_path():
    return os.path.join(os.path.dirname(__file__), "..", "preflight.py")
