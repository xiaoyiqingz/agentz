import tempfile
import unittest
from pathlib import Path

from tools.file_reader import read_file_lines


class TestFileReader(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = Path(self.temp_dir.name) / "demo.py"
        self.file_path.write_text("line1\nline2\nline3\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_reads_requested_line_range(self):
        content = read_file_lines(self.file_path, 1, 2)

        self.assertEqual(content, "line1\nline2\n")

    def test_defaults_to_single_line_when_end_line_is_omitted(self):
        content = read_file_lines(self.file_path, 2)

        self.assertEqual(content, "line2\n")

    def test_raises_for_out_of_range_request(self):
        with self.assertRaises(ValueError):
            read_file_lines(self.file_path, 10, 10)


if __name__ == "__main__":
    unittest.main()
