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

    def test_git_readonly_uses_selected_child_repository(self):
        child_repository = self.project_path / "child"
        child_repository.mkdir()
        subprocess.run(["git", "init"], cwd=child_repository, check=True, capture_output=True)
        (child_repository / "child.py").write_text("child = True\n", encoding="utf-8")
        subprocess.run(["git", "add", "child.py"], cwd=child_repository, check=True, capture_output=True)
        subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "child initial"],
            cwd=child_repository,
            check=True,
            capture_output=True,
        )

        output = git_readonly(self.project_path, "log", repository_path="child")

        self.assertIn("child initial", output)

    def test_git_readonly_accepts_absolute_child_repository_path(self):
        child_repository = self.project_path / "child"
        child_repository.mkdir()
        subprocess.run(["git", "init"], cwd=child_repository, check=True, capture_output=True)

        output = git_readonly(
            self.project_path,
            "status",
            repository_path=child_repository,
        )

        self.assertIn("##", output)

    def test_git_readonly_scopes_file_path_to_selected_repository(self):
        child_repository = self.project_path / "child"
        child_repository.mkdir()
        subprocess.run(["git", "init"], cwd=child_repository, check=True, capture_output=True)
        (child_repository / "child.py").write_text("value = 1\n", encoding="utf-8")
        subprocess.run(["git", "add", "child.py"], cwd=child_repository, check=True, capture_output=True)
        subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "initial"],
            cwd=child_repository,
            check=True,
            capture_output=True,
        )
        (child_repository / "child.py").write_text("value = 2\n", encoding="utf-8")

        output = git_readonly(
            self.project_path,
            "diff",
            repository_path="child",
            path="child.py",
        )

        self.assertIn("-value = 1", output)
        self.assertIn("+value = 2", output)

    def test_git_readonly_rejects_repository_outside_project(self):
        with self.assertRaisesRegex(ValueError, "路径超出当前项目目录"):
            git_readonly(self.project_path, "status", repository_path="../outside")

    def test_git_readonly_rejects_directory_that_is_not_repository_root(self):
        directory = self.project_path / "not-a-repository"
        directory.mkdir()

        with self.assertRaisesRegex(ValueError, "不是 Git 仓库根目录"):
            git_readonly(self.project_path, "status", repository_path="not-a-repository")

    def test_git_readonly_rejects_subdirectory_of_repository_as_repository_path(self):
        directory = self.project_path / "subdirectory"
        directory.mkdir()

        with self.assertRaisesRegex(ValueError, "不是 Git 仓库根目录"):
            git_readonly(self.project_path, "status", repository_path="subdirectory")

    def test_resolve_repo_path_rejects_directory_escape(self):
        with self.assertRaises(ValueError):
            resolve_repo_path(self.project_path, "../outside.py")
