import tempfile
import unittest
from pathlib import Path

from core.context.models import SessionMeta
from utils.project_context import resolve_session_project_path


class TestProjectContext(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cwd = Path(self.temp_dir.name).resolve()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_new_session_uses_requested_project_path(self):
        requested = self.cwd / "repo-a"

        resolved, ignored = resolve_session_project_path(
            session_meta=None,
            requested_project_path=requested,
            cwd=self.cwd,
        )

        self.assertEqual(resolved, requested)
        self.assertFalse(ignored)

    def test_new_session_defaults_to_current_working_directory(self):
        resolved, ignored = resolve_session_project_path(
            session_meta=None,
            requested_project_path=None,
            cwd=self.cwd,
        )

        self.assertEqual(resolved, self.cwd)
        self.assertFalse(ignored)

    def test_resume_strictly_restores_meta_project_path(self):
        session_meta = SessionMeta(
            session_id="session-1",
            conversation_id="conversation-1",
            project_path=str(self.cwd / "repo-meta"),
        )

        resolved, ignored = resolve_session_project_path(
            session_meta=session_meta,
            requested_project_path=self.cwd / "repo-cli",
            cwd=self.cwd,
        )

        self.assertEqual(resolved, self.cwd / "repo-meta")
        self.assertTrue(ignored)

    def test_resume_backfills_missing_project_path_with_current_directory(self):
        session_meta = SessionMeta(
            session_id="session-1",
            conversation_id="conversation-1",
        )

        resolved, ignored = resolve_session_project_path(
            session_meta=session_meta,
            requested_project_path=None,
            cwd=self.cwd,
        )

        self.assertEqual(resolved, self.cwd)
        self.assertFalse(ignored)


if __name__ == "__main__":
    unittest.main()
