from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic_ai.messages import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    ModelRequest,
    ModelResponse,
    PartDeltaEvent,
    PartStartEvent,
    TextPart,
    TextPartDelta,
    ThinkingPart,
    ThinkingPartDelta,
    UserPromptPart,
)
from pydantic_ai.run import AgentRunResultEvent


@dataclass(frozen=True)
class StreamConsumptionResult:
    final_response_text: str
    run_result: Any | None


def render_message_history(messages: list[Any], formatter: Any) -> int:
    """Render visible user and assistant text with the normal CLI formatter.

    Tool calls, tool results, thinking, and system instructions remain internal
    implementation details and are intentionally omitted from the replay.
    """
    rendered_turns = 0

    for message in messages:
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, UserPromptPart):
                    formatter.print_user_input(part.content)
                    formatter.print_blank_line()
        elif isinstance(message, ModelResponse):
            text = "".join(
                part.content
                for part in message.parts
                if isinstance(part, TextPart)
            )
            if not text:
                continue

            formatter.print_rule()
            formatter.add_chunk(text)
            formatter.render_final()
            formatter.reset()
            formatter.print_blank_line()
            rendered_turns += 1

    return rendered_turns


async def consume_stream_events(
    stream: Any,
    formatter: Any,
    tool_status_labels: dict[str, str],
) -> StreamConsumptionResult:
    final_response_text = ""
    run_result = None

    async for event in stream:
        if isinstance(event, PartStartEvent):
            if isinstance(event.part, ThinkingPart):
                # 并非所有模型都会暴露 ThinkingPart，这里不再依赖它驱动状态提示。
                pass
            elif isinstance(event.part, TextPart):
                if event.part.content:
                    final_response_text += event.part.content
                    formatter.add_chunk(event.part.content)
                    formatter.render_if_needed()
        elif isinstance(event, PartDeltaEvent):
            if isinstance(event.delta, ThinkingPartDelta):
                # 推理仍然进行，但不向用户暴露具体 thinking 文本。
                pass
            elif isinstance(event.delta, TextPartDelta):
                if event.delta.content_delta:
                    final_response_text += event.delta.content_delta
                    formatter.add_chunk(event.delta.content_delta)
                    formatter.render_if_needed()
        elif isinstance(event, FunctionToolCallEvent):
            tool_name = event.part.tool_name
            status_text = tool_status_labels.get(tool_name, f"正在调用工具：{tool_name}")
            formatter.print_status(status_text)
        elif isinstance(event, FunctionToolResultEvent):
            # 如需排查工具返回内容，可临时恢复这段输出。
            # if event.result.tool_name not in hidden_tool_result_names:
            #     formatter.print_tool_result(event.result.content)
            pass
        elif isinstance(event, AgentRunResultEvent):
            run_result = event.result

    return StreamConsumptionResult(
        final_response_text=final_response_text,
        run_result=run_result,
    )
