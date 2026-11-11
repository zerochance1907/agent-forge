import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from preflight import classify_command, main  # noqa: E402

PREFLIGHT_PY = str(ROOT / "preflight.py")

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


@pytest.mark.parametrize("command,expected_tier", CONSENSUS_FIXTURES)
def test_consensus_fixtures(command, expected_tier):
    assert classify_command(command)["tier"] == expected_tier


@pytest.mark.parametrize("command,expected_tier", CONSENSUS_FIXTURES)
def test_tier_cli_stdout_is_exactly_the_tier(command, expected_tier, capsys):
    exit_code = main(["tier", "--"] + command.split())
    out = capsys.readouterr().out
    assert out == expected_tier + "\n"
    assert exit_code == 0


# -- Additional tier-table coverage beyond the nine consensus fixtures --

@pytest.mark.parametrize("command,expected_tier", [
    ("git status", "SAFE"),
    ("git log", "SAFE"),
    ("git diff", "SAFE"),
    ("git show HEAD", "SAFE"),
    ("git branch", "SAFE"),
    ("grep foo bar.txt", "SAFE"),
    ("find . -name '*.py'", "SAFE"),
    ("pwd", "SAFE"),
    ("touch newfile.txt", "REVERSIBLE_LOCAL"),
    ("cp a.txt b.txt", "REVERSIBLE_LOCAL"),
    ("git add .", "REVERSIBLE_LOCAL"),
    ("git commit -m msg", "REVERSIBLE_LOCAL"),
    ("git stash", "REVERSIBLE_LOCAL"),
    ("git checkout -b feature", "REVERSIBLE_LOCAL"),
    ("rmdir emptydir", "DESTRUCTIVE_LOCAL"),
    ("dd if=/dev/zero of=file", "DESTRUCTIVE_LOCAL"),
    ("truncate -s 0 file.txt", "DESTRUCTIVE_LOCAL"),
    ("shred secret.txt", "DESTRUCTIVE_LOCAL"),
    ("git clean -fd", "DESTRUCTIVE_LOCAL"),
    ("git checkout -- file.txt", "DESTRUCTIVE_LOCAL"),
    ("git restore file.txt", "DESTRUCTIVE_LOCAL"),
    ("echo hi > out.txt", "DESTRUCTIVE_LOCAL"),
    ("echo hi >> out.txt", "SAFE"),  # only bare '>' (truncating) triggers the redirect rule
    ("wget https://example.com/file", "EXTERNAL"),
    ("ssh user@example.com", "EXTERNAL"),
    ("scp file user@host:/tmp", "EXTERNAL"),
    ("git fetch origin", "EXTERNAL"),
    ("git clone https://example.com/repo.git", "EXTERNAL"),
    ("git remote add origin https://example.com/repo.git", "EXTERNAL"),
    ("docker push myimage", "EXTERNAL"),
    ("docker pull myimage", "EXTERNAL"),
    ("npm install left-pad", "EXTERNAL"),
    ("npm publish", "EXTERNAL"),
    ("pip install requests", "EXTERNAL"),
    ("aws s3 ls", "EXTERNAL"),
    ("kubectl get pods", "EXTERNAL"),
    ("psql -c 'select 1'", "EXTERNAL"),
])
def test_extended_tier_table(command, expected_tier):
    assert classify_command(command)["tier"] == expected_tier


# -- Obfuscation / indirection -> UNKNOWN (acceptance criterion 5) --

@pytest.mark.parametrize("command", [
    "echo $(whoami)",
    "echo `whoami`",
    "echo ${HOME}",
    "echo $HOME",
    "ls | grep foo",
    "ls ; rm -rf /",
    "ls && rm -rf /",
    "ls || rm -rf /",
    "eval rm -rf /",
    'sh -c "rm -rf /"',
    'bash -c "rm -rf /"',
    "find . -delete | xargs echo",
    "xargs rm -rf",
])
def test_obfuscation_is_always_unknown(command):
    assert classify_command(command)["tier"] == "UNKNOWN"


def test_find_with_delete_is_not_safe():
    assert classify_command("find . -delete")["tier"] != "SAFE"


def test_find_without_delete_or_exec_is_safe():
    assert classify_command("find . -name x")["tier"] == "SAFE"


# -- Card fields / --json shape (acceptance criterion 3) --

def test_classify_card_ends_with_tier_line(capsys):
    exit_code = main(["classify", "--", "rm", "-rf", "build"])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert out.rstrip("\n").splitlines()[-1] == "TIER: DESTRUCTIVE_LOCAL"


def test_classify_json_has_all_eight_fields(capsys):
    main(["--json", "classify", "--", "rm", "-rf", "build"])
    out = capsys.readouterr().out
    card = json.loads(out)
    expected_fields = {
        "action", "tier", "reversible", "networked",
        "files_affected", "uncommitted_at_risk", "external_system", "reasons",
    }
    assert set(card.keys()) == expected_fields
    assert card["tier"] == "DESTRUCTIVE_LOCAL"


def test_reversible_and_networked_flags():
    assert classify_command("ls -la")["reversible"] is True
    assert classify_command("mkdir d")["reversible"] is True
    assert classify_command("rm -rf build")["reversible"] is False
    card = classify_command("curl https://example.com")
    assert card["networked"] is True
    assert card["external_system"] is True


def test_unparseable_path_yields_null_counts():
    card = classify_command("rm -rf $(echo x)")
    assert card["tier"] == "UNKNOWN"
    assert card["files_affected"] is None
    assert card["uncommitted_at_risk"] is None


# -- Gate subcommand: default pauses on everything, flag only auto-approves two tiers --

@pytest.mark.parametrize("command,expected_tier", CONSENSUS_FIXTURES)
def test_gate_default_always_pauses(command, expected_tier, capsys):
    exit_code = main(["gate", "--"] + command.split())
    out = capsys.readouterr().out
    assert exit_code == 10
    assert out == f"PAUSE {expected_tier}\n"


@pytest.mark.parametrize("command", ["ls -la", "mkdir newdir"])
def test_gate_auto_approve_safe_tiers(command, capsys):
    exit_code = main(["--auto-approve-safe", "gate", "--"] + command.split())
    out = capsys.readouterr().out
    assert exit_code == 0
    assert out.startswith("AUTO-APPROVED")


@pytest.mark.parametrize("command", [
    "rm -rf build",
    "curl https://example.com",
    "frobnicate --wild",
])
def test_gate_auto_approve_never_covers_dangerous_tiers(command, capsys):
    exit_code = main(["--auto-approve-safe", "gate", "--"] + command.split())
    out = capsys.readouterr().out
    assert exit_code == 10
    assert out.startswith("PAUSE")


# -- Tree-dependent enrichment against a real fixture repo (acceptance criterion 4) --

@pytest.fixture
def fixture_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)

    build_dir = repo / "build"
    build_dir.mkdir()
    (build_dir / "committed.txt").write_text("committed\n")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)

    (build_dir / "dirty.txt").write_text("uncommitted\n")
    return repo


def test_files_affected_counts_directory_contents(fixture_repo):
    card = classify_command("rm -rf build", root=str(fixture_repo))
    assert card["tier"] == "DESTRUCTIVE_LOCAL"
    assert card["files_affected"] == 2  # committed.txt + dirty.txt


def test_uncommitted_at_risk_counts_only_dirty_files(fixture_repo):
    card = classify_command("rm -rf build", root=str(fixture_repo))
    assert card["uncommitted_at_risk"] == 1  # dirty.txt only


def test_literal_nonexistent_path_yields_zero_not_null(fixture_repo):
    card = classify_command("rm -rf does-not-exist", root=str(fixture_repo))
    assert card["files_affected"] == 0
    assert card["uncommitted_at_risk"] == 0


def test_non_local_tier_has_null_counts():
    card = classify_command("curl https://example.com/x")
    assert card["files_affected"] is None
    assert card["uncommitted_at_risk"] is None


# -- CLI 'tier' stdout purity (acceptance criterion 1) --

def test_tier_stdout_has_no_extra_banners(capsys):
    main(["tier", "--", "ls", "-la"])
    out = capsys.readouterr().out
    assert out == "SAFE\n"
