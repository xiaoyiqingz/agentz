import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from pydantic_ai.messages import (
    FunctionToolCallEvent,
    PartDeltaEvent,
    PartStartEvent,
    TextPart,
    TextPartDelta,
    ToolCallPart,
)
from pydantic_ai.run import AgentRunResultEvent

from core.stream_event_handler import consume_stream_events


class TestStreamEventHandler(unittest.TestCase):
    def test_consume_stream_events_accumulates_text_and_status(self):
        formatter = Mock()
        run_result = SimpleNamespace()

        async def stream():
            yield PartStartEvent(index=0, part=TextPart(content="hello"))
            yield PartDeltaEvent(index=0, delta=TextPartDelta(content_delta=" world"))
            yield FunctionToolCallEvent(
                part=ToolCallPart(tool_name="search_repo", args={"pattern": "x"})
            )
            yield AgentRunResultEvent(result=run_result)

        result = asyncio.run(
            consume_stream_events(
                stream(),
                formatter=formatter,
                tool_status_labels={"search_repo": "正在搜索项目代码"},
            )
        )

        self.assertEqual(result.final_response_text, "hello world")
        self.assertIs(result.run_result, run_result)
        formatter.add_chunk.assert_any_call("hello")
        formatter.add_chunk.assert_any_call(" world")
        formatter.render_if_needed.assert_called()
        formatter.print_status.assert_called_with("正在搜索项目代码")

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


if __name__ == "__main__":
    unittest.main()
