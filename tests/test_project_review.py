import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.project_review import (
    CommandRejectedError,
    exec_review_command,
    read_project_file,
    resolve_repo_path,
)


class TestProjectReview(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_path = Path(self.temp_dir.name).resolve()
        (self.project_path / "src").mkdir()
        (self.project_path / "src" / "demo.py").write_text(
            "line1\nline2\nline3\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_resolve_repo_path_keeps_paths_inside_project(self):
        resolved = resolve_repo_path(self.project_path, "src/demo.py")

        self.assertEqual(resolved, self.project_path / "src" / "demo.py")

    def test_resolve_repo_path_rejects_directory_escape(self):
        with self.assertRaises(ValueError):
            resolve_repo_path(self.project_path, "../outside.py")

    def test_read_project_file_reads_relative_path_from_project_root(self):
        content = read_project_file(self.project_path, "src/demo.py", 1, 2)

        self.assertEqual(content, "line1\nline2\n")

    @patch("tools.project_review.subprocess.run")
    def test_exec_review_command_allows_git_diff(self, run_mock):
        run_mock.return_value = subprocess.CompletedProcess(
            args=["git", "diff", "master"],
            returncode=0,
            stdout="diff output",
            stderr="",
        )

        result = exec_review_command(self.project_path, "git diff master")

        self.assertIn("diff output", result)
        run_mock.assert_called_once()
        self.assertEqual(run_mock.call_args.kwargs["cwd"], self.project_path)
        self.assertFalse(run_mock.call_args.kwargs["shell"])

    def test_exec_review_command_rejects_shell_operators(self):
        with self.assertRaises(CommandRejectedError):
            exec_review_command(self.project_path, "git diff master && git status")

    def test_exec_review_command_rejects_disallowed_git_subcommand(self):
        with self.assertRaises(CommandRejectedError):
            exec_review_command(self.project_path, "git checkout main")


if __name__ == "__main__":
    unittest.main()
