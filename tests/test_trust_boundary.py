"""The research and debate agents must not be able to change GitHub or the orchestrator.

Run with:  python -m unittest discover -s tests
"""
import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class GhReadTests(unittest.TestCase):
    def setUp(self):
        self.ghread = load(REPO / "ghread.py", "ghread")

    def test_always_get(self):
        cmd = self.ghread.build(["repos/o/r/readme", "--jq", ".name", "--paginate"])
        self.assertEqual(cmd, ["gh", "api", "--method", "GET", "repos/o/r/readme", "--jq", ".name", "--paginate"])

    def test_refuses_anything_that_could_write(self):
        for argv in (["repos/o/r/issues", "-X", "POST"], ["repos/o/r/issues", "--method", "DELETE"],
                     ["repos/o/r/issues", "-f", "title=x"], ["repos/o/r", "--input", "body.json"],
                     ["-X", "POST", "repos/o/r/issues"], ["graphql"], ["https://example.com/x"], []):
            with self.assertRaises(ValueError, msg=argv):
                self.ghread.build(argv)


class WriteGuardTests(unittest.TestCase):
    """Runs the real guard from forge.py inside a throwaway git repo."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="forge-guard-"))
        for name in ("forge.py", "config.json", "PROTOCOL.md"):
            shutil.copy(REPO / name, self.tmp / name)
        (self.tmp / "agents").mkdir()
        (self.tmp / "agents" / "researcher.md").write_text("original instructions\n", encoding="utf-8")
        (self.tmp / "notes.txt").write_text("committed\n", encoding="utf-8")
        self.git("init", "-q")
        self.git("add", "-A")
        self.git("-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", "init")
        self.forge = load(self.tmp / "forge.py", "forge_under_test")
        self.state = {"cycle": "2026-01-01"}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.tmp, check=True, capture_output=True)

    def test_reverts_everything_outside_the_agents_folders(self):
        f, t = self.forge, self.tmp
        (t / "draft.txt").write_text("owner's unsaved work\n", encoding="utf-8")  # dirty before the agent ran
        before = f.worktree_snapshot()

        # what a misbehaving agent might do
        (t / "memos" / "2026-01-01").mkdir(parents=True)
        (t / "memos" / "2026-01-01" / "001-researcher-to-all.md").write_text("memo\n", encoding="utf-8")
        (t / "research" / "2026-01-01").mkdir(parents=True)
        (t / "research" / "2026-01-01" / "report.md").write_text("report\n", encoding="utf-8")
        (t / "forge.py").write_text("print('hijacked')\n", encoding="utf-8")
        (t / "agents" / "researcher.md").write_text("new instructions\n", encoding="utf-8")
        (t / "notes.txt").unlink()
        (t / "draft.txt").write_text("overwritten\n", encoding="utf-8")
        (t / "backdoor.py").write_text("x\n", encoding="utf-8")
        (t / "memos" / "2025-12-25").mkdir()
        (t / "memos" / "2025-12-25" / "001-fake.md").write_text("rewriting history\n", encoding="utf-8")

        stray = f.revert_stray_writes(self.state, "researcher", before)

        self.assertEqual(stray, ["agents/researcher.md", "backdoor.py", "draft.txt", "forge.py",
                                 "memos/2025-12-25/001-fake.md", "notes.txt"])
        self.assertEqual((t / "forge.py").read_bytes(), (REPO / "forge.py").read_bytes())
        self.assertEqual((t / "agents" / "researcher.md").read_text(encoding="utf-8"), "original instructions\n")
        self.assertEqual((t / "notes.txt").read_text(encoding="utf-8"), "committed\n")
        self.assertEqual((t / "draft.txt").read_text(encoding="utf-8"), "owner's unsaved work\n")
        self.assertFalse((t / "backdoor.py").exists())
        self.assertFalse((t / "memos" / "2025-12-25" / "001-fake.md").exists())
        # the agent's real output is kept
        self.assertTrue((t / "memos" / "2026-01-01" / "001-researcher-to-all.md").exists())
        self.assertTrue((t / "research" / "2026-01-01" / "report.md").exists())

    def test_well_behaved_agent_changes_nothing(self):
        f, t = self.forge, self.tmp
        before = f.worktree_snapshot()
        (t / "memos" / "2026-01-01").mkdir(parents=True)
        (t / "memos" / "2026-01-01" / "002-novelty-a-to-novelty-b.md").write_text("ideas\n", encoding="utf-8")
        self.assertEqual(f.revert_stray_writes(self.state, "novelty-a", before), [])

    def test_restricted_agents_cannot_call_gh_api_directly(self):
        for role, spec in self.forge.CONFIG["agents"].items():
            if spec.get("full_access"):
                continue
            self.assertFalse([t for t in spec["tools"] if t.startswith("Bash(gh api")], role)


if __name__ == "__main__":
    sys.exit(unittest.main())
