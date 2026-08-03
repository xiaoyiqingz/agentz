from __future__ import annotations

from dataclasses import dataclass
import json
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


_TOOL_DETAIL_KEYS = {
    "git_readonly": (
        "operation",
        "base_ref",
        "target_ref",
        "path",
        "pattern",
        "stat",
    ),
    "read_file": ("path", "offset", "limit"),
    "write_file": ("path", "content", "expected_hash"),
    "edit_file": ("path", "old_text", "new_text", "expected_hash"),
    "create_directory": ("path",),
    "search_files": ("pattern", "path", "include_glob"),
    "find_files": ("pattern", "path"),
    "get_weather": ("city",),
    "duckduckgo_search": ("query",),
}
_DETAIL_LINE_LENGTH = 100
_DETAIL_MAX_LINES = 2


def format_tool_call_detail(tool_name: str, args: Any) -> str | None:
    """Return a compact, non-sensitive summary of the imminent tool call."""
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            return _truncate_detail(args)
    if not isinstance(args, dict) or not args:
        return None

    keys = _TOOL_DETAIL_KEYS.get(tool_name, tuple(args))
    details = [
        f"{key}={_format_tool_arg(key, args[key])}"
        for key in keys
        if key in args and args[key] is not None
    ]
    if not details:
        return None

    lines: list[str] = []
    current_line = ""
    for detail in details:
        candidate = detail if not current_line else f"{current_line} · {detail}"
        if len(candidate) <= _DETAIL_LINE_LENGTH:
            current_line = candidate
            continue
        if current_line:
            lines.append(current_line)
        current_line = detail
        if len(lines) == _DETAIL_MAX_LINES:
            break
    if len(lines) < _DETAIL_MAX_LINES and current_line:
        lines.append(current_line)

    was_truncated = len(lines) == _DETAIL_MAX_LINES and (
        " · ".join(lines) != " · ".join(details)
    )
    return "\n".join(_truncate_detail(line) for line in lines) + (" …" if was_truncated else "")


def _format_tool_arg(key: str, value: Any) -> str:
    if key in {"content", "old_text", "new_text"} and isinstance(value, str):
        return f"<{len(value)} chars>"
    if isinstance(value, str):
        return repr(value)
    return str(value)


def _truncate_detail(value: str) -> str:
    if len(value) <= _DETAIL_LINE_LENGTH:
        return value
    return f"{value[: _DETAIL_LINE_LENGTH - 1]}…"


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
            if detail := format_tool_call_detail(tool_name, event.part.args):
                formatter.print_tool_detail(detail)
            formatter.print_blank_line()
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
