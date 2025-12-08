from typing import AsyncIterable
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import (
    ModelMessage,
    SystemPromptPart,
    ThinkingPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
    RetryPromptPart,
    AgentStreamEvent,
    PartStartEvent,
    PartDeltaEvent,
    ThinkingPartDelta,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    BuiltinToolCallEvent,
    BuiltinToolResultEvent,
)
import logfire
import os
from pathlib import Path
from httpx import AsyncClient
from dataclasses import dataclass
from input_handler import InputHandler
from tools.coder import generate, modify
from models.qwen import model_qwen
from prompts.prompt import get_smart_assistant_prompt
from tools.code_patcher import apply_patch
from tools.code_reader import read_file_lines
from tools.tools_registry import get_all_tools
from output_formatter import create_formatter
from commands.builtin_commands import process_builtin_command, CommandType

# Planning Design 模式相关导入
from planning.orchestrator import PlanningOrchestrator
from planning.specialized_agents import Deps as PlanningDeps

# 配置 logfire 将日志输出到文件而不是控制台
logfire.configure()
logfire.instrument_pydantic_ai()

# 读取 Planning 模式配置
USE_PLANNING_MODE = os.getenv("USE_PLANNING_MODE", "false").lower() == "true"
PLANNING_MAX_ITERATIONS = int(os.getenv("PLANNING_MAX_ITERATIONS", "1"))


@dataclass
class Deps:
    client: AsyncClient


# 获取所有工具列表
tools_list = get_all_tools()

# 创建 Agent 实例
agent_kwargs = {
    "model": model_qwen,
    "deps_type": Deps,
    "system_prompt": get_smart_assistant_prompt(),  # 启用智能助手提示词，控制工具使用策略
}
if tools_list:
    agent_kwargs["tools"] = tools_list

agent = Agent(**agent_kwargs)


async def event_stream_handler(
    ctx: RunContext,
    event_stream: AsyncIterable[AgentStreamEvent],
):
    """处理流式事件的处理器函数"""
    # 流式处理事件
    thinking_content = ""
    thinking_started = False

    async for event in event_stream:
        if isinstance(event, PartStartEvent):
            if isinstance(event.part, ThinkingPart):
                thinking_started = True
                thinking_content = event.part.content
                print()  # 换行
                print(f"🤔 Thinking：{thinking_content}", end="", flush=True)
            # elif isinstance(event.part, ToolCallPart):
            #     if thinking_started:
            #         print()  # 换行
            #         thinking_started = False
            #     print(f"🔧 调用tool：{event.part.tool_name}")
        elif isinstance(event, PartDeltaEvent):
            if isinstance(event.delta, ThinkingPartDelta) and thinking_started:
                if event.delta.content_delta:
                    thinking_content += event.delta.content_delta
                    print(event.delta.content_delta, end="", flush=True)
        elif isinstance(event, FunctionToolCallEvent):
            if thinking_started:
                print()  # 换行
                thinking_started = False
            print(f"🔧 调用tool：{event.part.tool_name}")
        elif isinstance(event, FunctionToolResultEvent):
            if thinking_started:
                print()  # 换行
                thinking_started = False
            print(f"📤 tool返回：{event.result.content}")
        elif isinstance(event, BuiltinToolCallEvent):
            if thinking_started:
                print()  # 换行
                thinking_started = False
            print(f"🔧 调用内置tool：{event.part.tool_name}")
        elif isinstance(event, BuiltinToolResultEvent):
            if thinking_started:
                print()  # 换行
                thinking_started = False
            print(f"📤 内置tool返回：{event.result.content}")

    # 流式显示文本内容
    if thinking_started:
        print()  # 换行
        thinking_started = False


def process_history_messages(result, formatter):
    """处理历史消息，根据消息类型进行格式化输出"""
    # 处理历史消息
    for message in result.new_messages():
        for call in message.parts:
            if isinstance(call, ToolCallPart):
                formatter.print_tool_call(call.tool_name)
            elif isinstance(call, ToolReturnPart):
                formatter.print_tool_result(call.content)
            elif isinstance(call, SystemPromptPart):
                formatter.print_system_prompt(call.content)
            elif isinstance(call, UserPromptPart):
                formatter.print_user_input(call.content)
            elif isinstance(call, ThinkingPart):
                # 什么也不做，因为已经在 event_stream_handler 中处理了，此处打印只会在Think全部完成后打印内容，太慢
                pass
            elif isinstance(call, RetryPromptPart):
                # 处理重试提示，显示重试信息
                retry_info = f"🔄 重试工具：{call.tool_name or '未知'}"
                if isinstance(call.content, str):
                    formatter.console.print(f"[dim]{retry_info} - {call.content}[/dim]")
                else:
                    formatter.console.print(f"[dim]{retry_info}[/dim]")
            else:
                formatter.print_unknown(type(call))


async def stream_and_render_text(result, formatter):
    """流式显示文本内容，使用 rich 美化输出"""
    formatter.print_blank_line()
    formatter.print_rule()

    async for message in result.stream_text(delta=True):
        formatter.add_chunk(message)
        formatter.render_if_needed()
    # 最终渲染所有剩余内容
    formatter.render_final()
    # 重置格式化器缓冲区，避免下次对话时重复显示
    formatter.reset()


def handle_builtin_command_result(command_type, result, user_input, input_handler):
    """
    处理内置命令的结果

    返回: (should_break, should_continue, updated_user_input)
    - should_break: 是否应该退出循环
    - should_continue: 是否应该跳过后续处理（continue）
    - updated_user_input: 更新后的用户输入
    """
    if command_type == CommandType.DIRECT:
        # 直接处理型命令：显示结果并等待用户继续输入
        if result is not None:
            print(result)
        # 检查是否是退出命令（exit/quit/q）
        if user_input.strip().lower() in ("exit", "quit", "q"):
            # 退出前保存历史记录
            input_handler.save_history()
            # 退出循环（程序会在 async with 块结束后自然退出）
            return (True, False, user_input)
        return (False, True, user_input)
    elif command_type == CommandType.CONVERT:
        # 转换型命令：将转换后的内容作为用户输入传给 agent
        return (False, False, result)
    return (False, False, user_input)


async def server_run_stream():
    all_messages: list[ModelMessage] = []
    # message_history: list[ModelMessage] | None = None

    # 初始化命令行输入处理器
    project_root = Path(__file__).parent
    input_handler = InputHandler(project_root)
    input_handler.initialize()

    # 创建统一的格式化器
    formatter = create_formatter()

    # 初始化 Planning 协调器（如果启用 Planning 模式）
    orchestrator = None
    if USE_PLANNING_MODE:
        orchestrator = PlanningOrchestrator()
        formatter.console.print("[green]✓ Planning Design 模式已启用[/green]")

    async with AsyncClient() as client:
        logfire.instrument_httpx(client, capture_all=True)
        deps = Deps(client=client)

        try:
            while True:
                # 等待用户输入（readline 会自动增强 input() 的功能，rich 美化提示符）
                user_input = formatter.ask_input()

                # 处理内置命令
                is_builtin, result, command_type = process_builtin_command(user_input)
                if is_builtin:
                    should_break, should_continue, user_input = (
                        handle_builtin_command_result(
                            command_type, result, user_input, input_handler
                        )
                    )
                    if should_break:
                        break
                    if should_continue:
                        continue

                # 根据配置选择使用 Planning 模式还是单一 Agent 模式
                if USE_PLANNING_MODE and orchestrator is not None:
                    # 使用 Planning Design 模式（非流式）
                    formatter.console.print("[dim]🤔 Planning 模式处理中...[/dim]")
                    planning_deps = PlanningDeps(client=client)
                    final_result = await orchestrator.execute(
                        user_input,
                        deps=planning_deps,
                        max_iterations=PLANNING_MAX_ITERATIONS,
                    )
                    # 显示结果
                    formatter.print_blank_line()
                    formatter.print_rule()
                    formatter.console.print(final_result)
                    formatter.print_blank_line()
                    formatter.print_rule()
                else:
                    # 使用单一 Agent 模式（流式）
                    async with agent.run_stream(
                        user_input,
                        deps=deps,
                        message_history=all_messages,
                        event_stream_handler=event_stream_handler,
                    ) as result:

                        # 处理历史消息
                        process_history_messages(result, formatter)

                        # 流式显示文本内容
                        await stream_and_render_text(result, formatter)

                        # 更新消息历史（仅单一 Agent 模式）
                        all_messages = all_messages + result.new_messages()
                        # 对于stream_text(delta=True)，result.all_messages()和result.new_messages()都不会返回历史信息
                        # 所以需要手动将历史信息添加到all_messages中
                        # all_messages = result.all_messages()
                        # message_history = result.new_messages()
                        # print(all_messages)

                        print()  # 空行分隔

        except (KeyboardInterrupt, EOFError):
            # 保存历史记录
            input_handler.cleanup()
            raise


async def server_run():
    async with AsyncClient() as client:
        logfire.instrument_httpx(client, capture_all=True)
        deps = Deps(client=client)

        while True:
            user_input = input("> ")

            result = agent.run_sync(user_input, deps=deps)
            print(f"返回结果: {result.output}")
            print()
