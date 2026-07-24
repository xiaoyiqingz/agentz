import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.local.project_review import git_readonly, resolve_repo_path


class TestProjectReview(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_path = Path(self.temp_dir.name).resolve()
        self._git("init")
        (self.project_path / "example.py").write_text("value = 1\n", encoding="utf-8")
        self._git("add", "example.py")
        self._git("-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "initial")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _git(self, *args: str) -> None:
        subprocess.run(["git", *args], cwd=self.project_path, check=True, capture_output=True)

    def test_git_readonly_returns_status(self):
        output = git_readonly(self.project_path, "status")

        self.assertIn("##", output)

    def test_git_readonly_reads_diff_against_base(self):
        self._git("branch", "base")
        (self.project_path / "example.py").write_text("value = 2\n", encoding="utf-8")
        self._git("add", "example.py")
        self._git("-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "change")

        output = git_readonly(self.project_path, "diff", base_ref="base", path="example.py")

        self.assertIn("-value = 1", output)
        self.assertIn("+value = 2", output)

    def test_git_readonly_rejects_unsafe_ref(self):
        with self.assertRaisesRegex(ValueError, "非法 Git 引用"):
            git_readonly(self.project_path, "show", target_ref="--config")

    def test_resolve_repo_path_rejects_directory_escape(self):
        with self.assertRaises(ValueError):
            resolve_repo_path(self.project_path, "../outside.py")
