import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import preflight  # noqa: E402


def run_cli(*args, cwd=None):
    """Invoke preflight.py as a subprocess, decoding output as utf-8.

    The CLI's blast-radius card uses non-ASCII glyphs; the subprocess pipe
    must be decoded as utf-8 explicitly or Windows falls back to the
    locale codec and garbles/crashes on them.
    """
    return subprocess.run(
        [sys.executable, str(ROOT / "preflight.py"), *args],
        capture_output=True, text=True, encoding="utf-8", cwd=cwd,
    )

CONSENSUS_FIXTURES = [
    ("read-only-ls", "ls -la", "SAFE"),
    ("read-only-cat", "cat README.md", "SAFE"),
    ("rm-rf", "rm -rf build", "DESTRUCTIVE_LOCAL"),
    ("mv", "mv old.txt new.txt", "DESTRUCTIVE_LOCAL"),
    ("git-reset-hard", "git reset --hard HEAD", "DESTRUCTIVE_LOCAL"),
    ("curl-post", "curl -X POST https://api.example.com/charges", "EXTERNAL"),
    ("git-push", "git push origin main", "EXTERNAL"),
    ("mkdir", "mkdir newdir", "REVERSIBLE_LOCAL"),
    ("unknown-verb", "frobnicate --wild", "UNKNOWN"),
]


@pytest.mark.parametrize("name,cmd,expected", CONSENSUS_FIXTURES, ids=[f[0] for f in CONSENSUS_FIXTURES])
def test_consensus_fixtures_direct(name, cmd, expected):
    tier, _reasons = preflight._classify_tier(cmd.split())
    assert tier == expected


@pytest.mark.parametrize("name,cmd,expected", CONSENSUS_FIXTURES, ids=[f[0] for f in CONSENSUS_FIXTURES])
def test_consensus_fixtures_cli_tier(name, cmd, expected):
    result = run_cli("tier", "--", *cmd.split())
    assert result.stdout == expected + "\n"
    assert result.stdout.strip() == expected
    assert result.returncode == 0


def test_tier_stdout_has_nothing_extra():
    result = run_cli("tier", "--", "ls", "-la")
    assert result.stdout == "SAFE\n"


# --- extra classification coverage beyond the 9 consensus fixtures -------

@pytest.mark.parametrize("cmd,expected", [
    ("echo $(whoami)", "UNKNOWN"),
    ("ls | grep x", "UNKNOWN"),
    ("ls ; rm -rf /", "UNKNOWN"),
    ("ls && rm -rf /", "UNKNOWN"),
    ("ls || rm -rf /", "UNKNOWN"),
    ("bash -c rm -rf /", "UNKNOWN"),
    ("sh -c ls", "UNKNOWN"),
    ("xargs rm", "UNKNOWN"),
    ("echo $HOME", "UNKNOWN"),
    ("eval ls", "UNKNOWN"),
])
def test_obfuscation_always_unknown(cmd, expected):
    tier, _ = preflight._classify_tier(cmd.split())
    assert tier == expected


@pytest.mark.parametrize("cmd,expected", [
    ("git status", "SAFE"),
    ("git log --oneline", "SAFE"),
    ("git diff", "SAFE"),
    ("git branch", "SAFE"),
    ("pwd", "SAFE"),
    ("find . -name x", "SAFE"),
    ("find . -delete", "UNKNOWN"),
    ("find . -exec rm {} ;".replace(";", "\\;"), "UNKNOWN"),
    ("git add .", "REVERSIBLE_LOCAL"),
    ("git commit -m msg", "REVERSIBLE_LOCAL"),
    ("git stash", "REVERSIBLE_LOCAL"),
    ("git checkout -b feature", "REVERSIBLE_LOCAL"),
    ("touch file.txt", "REVERSIBLE_LOCAL"),
    ("cp a.txt b.txt", "REVERSIBLE_LOCAL"),
    ("git clean -fd", "DESTRUCTIVE_LOCAL"),
    ("git checkout -- file.txt", "DESTRUCTIVE_LOCAL"),
    ("git restore file.txt", "DESTRUCTIVE_LOCAL"),
    ("dd if=/dev/zero of=/dev/sda", "DESTRUCTIVE_LOCAL"),
    ("truncate -s 0 file.txt", "DESTRUCTIVE_LOCAL"),
    ("echo hi > file.txt", "DESTRUCTIVE_LOCAL"),
    ("ssh user@example.com", "EXTERNAL"),
    ("scp file.txt user@example.com:/tmp", "EXTERNAL"),
    ("git fetch origin", "EXTERNAL"),
    ("git clone https://example.com/repo.git", "EXTERNAL"),
    ("docker push myimage", "EXTERNAL"),
    ("npm publish", "EXTERNAL"),
    ("pip install requests", "EXTERNAL"),
    ("aws s3 ls", "EXTERNAL"),
    ("kubectl get pods", "EXTERNAL"),
    ("wget https://example.com/file", "EXTERNAL"),
    ("rsync -a src dest", "EXTERNAL"),
], ids=lambda x: x if isinstance(x, str) else "")
def test_broad_tier_table(cmd, expected):
    tier, _ = preflight._classify_tier(cmd.split())
    assert tier == expected


def test_reversible_and_networked_flags():
    card = preflight.classify_command("ls -la".split())
    assert card["reversible"] is True
    assert card["networked"] is False

    card = preflight.classify_command("rm -rf build".split())
    assert card["reversible"] is False

    card = preflight.classify_command("curl https://example.com".split())
    assert card["networked"] is True
    assert card["external_system"] is True


# --- file-count enrichment against a real working tree -------------------

@pytest.fixture
def fixture_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "a@b.c"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=repo, check=True)

    build = repo / "build"
    build.mkdir()
    (build / "tracked.txt").write_text("tracked")
    (build / "untracked.txt").write_text("untracked")

    subprocess.run(["git", "add", "build/tracked.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    # untracked.txt is deliberately left uncommitted
    return repo


def test_destructive_enrichment_counts_files(fixture_repo):
    card = preflight.classify_command("rm -rf build".split(), root=str(fixture_repo))
    assert card["tier"] == "DESTRUCTIVE_LOCAL"
    assert card["files_affected"] == 2
    assert card["uncommitted_at_risk"] == 1


def test_destructive_enrichment_single_file(fixture_repo):
    card = preflight.classify_command("rm build/tracked.txt".split(), root=str(fixture_repo))
    assert card["files_affected"] == 1
    assert card["uncommitted_at_risk"] == 0

    card = preflight.classify_command("rm build/untracked.txt".split(), root=str(fixture_repo))
    assert card["files_affected"] == 1
    assert card["uncommitted_at_risk"] == 1


def test_destructive_enrichment_glob(fixture_repo):
    card = preflight.classify_command("rm build/*.txt".split(), root=str(fixture_repo))
    assert card["files_affected"] == 2
    assert card["uncommitted_at_risk"] == 1


def test_non_local_tier_enrichment_is_null(fixture_repo):
    card = preflight.classify_command("curl https://example.com".split(), root=str(fixture_repo))
    assert card["files_affected"] is None
    assert card["uncommitted_at_risk"] is None

    card = preflight.classify_command("git reset --hard HEAD".split(), root=str(fixture_repo))
    assert card["files_affected"] is None
    assert card["uncommitted_at_risk"] is None

    card = preflight.classify_command("frobnicate --wild".split(), root=str(fixture_repo))
    assert card["files_affected"] is None
    assert card["uncommitted_at_risk"] is None


def test_reversible_local_enrichment(fixture_repo):
    card = preflight.classify_command("mkdir newdir".split(), root=str(fixture_repo))
    assert card["files_affected"] == 1
    assert card["uncommitted_at_risk"] == 0


# --- classify / json / card surface ---------------------------------------

def test_classify_card_last_line_is_tier():
    result = run_cli("classify", "--", "ls", "-la")
    assert result.returncode == 0
    last_line = result.stdout.rstrip("\n").splitlines()[-1]
    assert last_line == "TIER: SAFE"


def test_classify_json_has_all_eight_fields():
    result = run_cli("--json", "classify", "--", "rm", "-rf", "build")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    expected_fields = {
        "action", "tier", "reversible", "networked", "files_affected",
        "uncommitted_at_risk", "external_system", "reasons",
    }
    assert expected_fields <= set(data.keys())
    assert data["tier"] == "DESTRUCTIVE_LOCAL"


# --- gate ------------------------------------------------------------------

def test_gate_default_pauses_on_everything():
    for cmd in ["ls -la", "mkdir newdir", "rm -rf build", "curl https://x.com", "frobnicate --wild"]:
        result = run_cli("gate", "--", *cmd.split())
        assert result.returncode == 10
        assert result.stdout.startswith("PAUSE ")


@pytest.mark.parametrize("cmd,should_auto_approve", [
    ("ls -la", True),
    ("mkdir newdir", True),
    ("rm -rf build", False),
    ("curl https://x.com", False),
    ("frobnicate --wild", False),
])
def test_gate_auto_approve_safe_only_affects_safe_tiers(cmd, should_auto_approve):
    result = run_cli("--auto-approve-safe", "gate", "--", *cmd.split())
    if should_auto_approve:
        assert result.returncode == 0
        assert result.stdout.startswith("AUTO-APPROVED ")
    else:
        assert result.returncode == 10
        assert result.stdout.startswith("PAUSE ")
