import unittest

from main import _parse_args


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


if __name__ == "__main__":
    unittest.main()
