import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from main import _load_agentz_env, _parse_args


class TestMain(unittest.TestCase):
    def test_parse_args_accepts_project_path_and_resume(self):
        args = _parse_args(
            ["--resume", "019e688c-77a0-7d4a-8f50-0a8a0cddd48b", "--project-path", "."]
        )

        self.assertEqual(args.resume, "019e688c-77a0-7d4a-8f50-0a8a0cddd48b")
        self.assertEqual(args.project_path, ".")

    def test_parse_args_defaults_project_path_to_none(self):
        args = _parse_args([])

        self.assertIsNone(args.project_path)

    def test_parse_args_accepts_agentz_home(self):
        args = _parse_args(["--agentz-home", "/tmp/agentz-home"])

        self.assertEqual(args.agentz_home, "/tmp/agentz-home")

    def test_load_agentz_env_reads_env_from_selected_home(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            agentz_home = Path(temp_dir)
            (agentz_home / ".env").write_text(
                "DEEPSEEK_API_KEY=test-key\nAGENTZ_HOME=/ignored-home\n",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {}, clear=True):
                loaded_home = _load_agentz_env(str(agentz_home))

                self.assertEqual(loaded_home, agentz_home.resolve())
                self.assertEqual(os.environ["DEEPSEEK_API_KEY"], "test-key")
                self.assertEqual(os.environ["AGENTZ_HOME"], str(agentz_home.resolve()))


if __name__ == "__main__":
    unittest.main()
