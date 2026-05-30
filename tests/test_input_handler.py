import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from input_handler import InputHandler


class TestInputHandler(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    @patch("input_handler.PromptSession")
    def test_initialize_uses_agentz_session_dir(self, prompt_session_mock):
        handler = InputHandler(self.config_path, session_id="session-1")

        handler.initialize()

        expected_dir = self.config_path / ".agentz" / "sessions" / "session-1"
        self.assertEqual(handler.session_dir, expected_dir)
        self.assertEqual(handler.history_file, expected_dir / "agentz_history")
        prompt_session_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
