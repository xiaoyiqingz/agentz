import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from pydantic_ai.messages import (
    FunctionToolCallEvent,
    ModelRequest,
    ModelResponse,
    PartDeltaEvent,
    PartStartEvent,
    TextPart,
    TextPartDelta,
    ToolCallPart,
    UserPromptPart,
)
from pydantic_ai.run import AgentRunResultEvent

from core.stream_event_handler import (
    consume_stream_events,
    format_tool_call_detail,
    render_message_history,
)


class TestStreamEventHandler(unittest.TestCase):
    def test_consume_stream_events_accumulates_text_and_status(self):
        formatter = Mock()
        run_result = SimpleNamespace()

        async def stream():
            yield PartStartEvent(index=0, part=TextPart(content="hello"))
            yield PartDeltaEvent(index=0, delta=TextPartDelta(content_delta=" world"))
            yield FunctionToolCallEvent(
                part=ToolCallPart(tool_name="search_files", args={"pattern": "x"})
            )
            yield AgentRunResultEvent(result=run_result)

        result = asyncio.run(
            consume_stream_events(
                stream(),
                formatter=formatter,
                tool_status_labels={"search_files": "正在搜索项目代码"},
            )
        )

        self.assertEqual(result.final_response_text, "hello world")
        self.assertIs(result.run_result, run_result)
        formatter.add_chunk.assert_any_call("hello")
        formatter.add_chunk.assert_any_call(" world")
        formatter.render_if_needed.assert_called()
        formatter.print_status.assert_called_with("正在搜索项目代码")
        formatter.print_tool_detail.assert_called_once_with("pattern='x'")
        formatter.print_blank_line.assert_called_once_with()

    def test_consume_stream_events_falls_back_to_default_tool_status(self):
        formatter = Mock()

        async def stream():
            yield FunctionToolCallEvent(
                part=ToolCallPart(tool_name="unknown_tool", args={"x": 1})
            )

        asyncio.run(
            consume_stream_events(
                stream(),
                formatter=formatter,
                tool_status_labels={},
            )
        )

        formatter.print_status.assert_called_once_with("正在调用工具：unknown_tool")
        formatter.print_tool_detail.assert_called_once_with("x=1")
        formatter.print_blank_line.assert_called_once_with()

    def test_format_tool_call_detail_limits_output_and_hides_file_contents(self):
        detail = format_tool_call_detail(
            "write_file",
            {
                "path": "src/very-long-file-name.py",
                "content": "x" * 500,
                "expected_hash": "abcdef123456",
            },
        )

        self.assertIsNotNone(detail)
        self.assertIn("path='src/very-long-file-name.py'", detail)
        self.assertIn("content=<500 chars>", detail)
        self.assertNotIn("x" * 50, detail)
        self.assertLessEqual(len(detail.splitlines()), 2)

    def test_format_tool_call_detail_shows_git_operation_and_branch(self):
        detail = format_tool_call_detail(
            "git_readonly",
            {"operation": "diff", "base_ref": "master", "target_ref": "HEAD"},
        )

        self.assertEqual(
            detail,
            "operation='diff' · base_ref='master' · target_ref='HEAD'",
        )

    def test_render_message_history_uses_the_normal_user_and_markdown_output(self):
        formatter = Mock()
        messages = [
            ModelRequest(parts=[UserPromptPart(content="历史问题")]),
            ModelResponse(parts=[TextPart(content="历史回答")]),
            ModelResponse(
                parts=[ToolCallPart(tool_name="search_files", args={})]
            ),
        ]

        rendered_turns = render_message_history(messages, formatter)

        self.assertEqual(rendered_turns, 1)
        formatter.print_user_input.assert_called_once_with("历史问题")
        formatter.add_chunk.assert_called_once_with("历史回答")
        formatter.render_final.assert_called_once_with()
        formatter.reset.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
