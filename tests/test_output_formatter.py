import unittest
from unittest.mock import Mock

from output_formatter import SimpleMarkdownFormatter, create_formatter


class TestOutputFormatter(unittest.TestCase):
    def test_simple_formatter_streams_chunks_immediately(self):
        formatter = SimpleMarkdownFormatter(show_stream=True)
        formatter.console = Mock()

        formatter.add_chunk("hello")

        formatter.console.print.assert_called_once_with(
            "hello", end="", markup=False
        )

    def test_simple_formatter_does_not_reprint_full_content_after_streaming(self):
        formatter = SimpleMarkdownFormatter(show_stream=True)
        formatter.console = Mock()

        formatter.add_chunk("hello")
        formatter.render_final()

        self.assertEqual(formatter.console.print.call_count, 2)
        formatter.console.print.assert_any_call("hello", end="", markup=False)
        formatter.console.print.assert_any_call()

    def test_create_formatter_non_live_streams_text(self):
        formatter = create_formatter(use_live=False)

        self.assertIsInstance(formatter.markdown_formatter, SimpleMarkdownFormatter)
        self.assertTrue(formatter.markdown_formatter.show_stream)


if __name__ == "__main__":
    unittest.main()
