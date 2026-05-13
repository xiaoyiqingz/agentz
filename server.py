from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import (
    ModelMessage,
    ThinkingPart,
    TextPart,
    TextPartDelta,
    PartStartEvent,
    PartDeltaEvent,
    ThinkingPartDelta,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    BuiltinToolCallEvent,
    BuiltinToolResultEvent,
)
from pydantic_ai.run import AgentRunResultEvent
import logfire
from pathlib import Path
from httpx import AsyncClient
from dataclasses import dataclass
from functools import lru_cache
from input_handler import InputHandler
from tools.coder import generate, modify
from config import Settings
from models.deepseek import build_deepseek_model
from prompts.prompt import get_smart_assistant_prompt
from tools.code_patcher import apply_patch
from tools.code_reader import read_file_lines
from tools.tools_registry import get_all_tools, get_all_toolsets
from output_formatter import create_formatter
from commands.builtin_commands import process_builtin_command, CommandType


@dataclass
class Deps:
    client: AsyncClient


@lru_cache(maxsize=1)
def configure_logfire() -> None:
    logfire.configure()
    logfire.instrument_pydantic_ai()


def create_agent(settings: Settings) -> Agent:
    tools_list = get_all_tools(settings)
    toolsets_list = get_all_toolsets(settings)

    agent_kwargs = {
        "model": build_deepseek_model(settings),
        "deps_type": Deps,
        "system_prompt": get_smart_assistant_prompt(),
    }
    if tools_list:
        agent_kwargs["tools"] = tools_list
    if toolsets_list:
        agent_kwargs["toolsets"] = toolsets_list

    agent = Agent(**agent_kwargs)

    @agent.tool
    async def read_code_file(
        ctx: RunContext[Deps], file_path: str, start_line: int, end_line: int
    ) -> str:
        return read_file_lines(file_path, start_line, end_line)

    @agent.tool
    async def apply_code_patch(
        ctx: RunContext[Deps], file_path: str, patch_string: str
    ) -> str:
        return apply_patch(patch_string, file_path)

    @agent.tool
    async def check_and_modify_code(
        ctx: RunContext[Deps], code_string: str, file_path: str, begin_line: int = 1
    ) -> str:
        return await modify(settings, code_string, file_path, begin_line)

    @agent.tool
    async def generate_code(ctx: RunContext[Deps], text: str) -> str:
        return await generate(settings, text)

    return agent


async def server_run_stream(settings: Settings, session_id: str):
    configure_logfire()
    agent = create_agent(settings)
    # 初始化命令行输入处理器
    project_root = Path(__file__).parent
    input_handler = InputHandler(project_root, session_id=session_id)
    input_handler.initialize()
    all_messages: list[ModelMessage] = input_handler.load_message_history()

    # 创建统一的格式化器
    formatter = create_formatter()

    async with AsyncClient() as client:
        logfire.instrument_httpx(client, capture_all=True)
        deps = Deps(client=client)

        try:
            while True:
                # 等待用户输入（readline 会自动增强 input() 的功能，rich 美化提示符）
                user_input = formatter.ask_input()

                # 处理内置命令
                is_builtin, result, command_type = process_builtin_command(
                    user_input, session_id=session_id
                )
                if is_builtin:
                    if command_type == CommandType.DIRECT:
                        # 直接处理型命令：显示结果并等待用户继续输入
                        if result is not None:
                            print(result)
                        # 检查是否是退出命令（exit/quit/q）
                        if user_input.strip().lower() in ("exit", "quit", "q"):
                            # 退出前保存历史记录
                            input_handler.save_message_history(all_messages)
                            input_handler.save_history()
                            # 退出循环（程序会在 async with 块结束后自然退出）
                            break
                        continue
                    elif command_type == CommandType.CONVERT:
                        # 转换型命令：将转换后的内容作为用户输入传给 agent
                        user_input = result

                # 在用户输入后加上"！"并返回
                final_response_text = ""
                run_result = None
                thinking_started = False

                formatter.print_user_input(user_input)
                formatter.print_blank_line()
                formatter.print_rule()

                async with agent.run_stream_events(
                    user_input,
                    deps=deps,
                    message_history=all_messages,
                ) as stream:
                    async for event in stream:
                        if isinstance(event, PartStartEvent):
                            if isinstance(event.part, ThinkingPart):
                                thinking_started = True
                                print()
                                print(
                                    f"🤔 Thinking：{event.part.content}",
                                    end="",
                                    flush=True,
                                )
                            elif isinstance(event.part, TextPart):
                                if thinking_started:
                                    print()
                                    thinking_started = False
                                if event.part.content:
                                    final_response_text += event.part.content
                                    formatter.add_chunk(event.part.content)
                                    formatter.render_if_needed()
                        elif isinstance(event, PartDeltaEvent):
                            if (
                                isinstance(event.delta, ThinkingPartDelta)
                                and thinking_started
                                and event.delta.content_delta
                            ):
                                print(event.delta.content_delta, end="", flush=True)
                            elif isinstance(event.delta, TextPartDelta):
                                if thinking_started:
                                    print()
                                    thinking_started = False
                                if event.delta.content_delta:
                                    final_response_text += event.delta.content_delta
                                    formatter.add_chunk(event.delta.content_delta)
                                    formatter.render_if_needed()
                        elif isinstance(event, FunctionToolCallEvent):
                            if thinking_started:
                                print()
                                thinking_started = False
                            formatter.print_tool_call(event.part.tool_name)
                        elif isinstance(event, FunctionToolResultEvent):
                            if thinking_started:
                                print()
                                thinking_started = False
                            formatter.print_tool_result(event.result.content)
                        elif isinstance(event, BuiltinToolCallEvent):
                            if thinking_started:
                                print()
                                thinking_started = False
                            print(f"🔧 调用内置tool：{event.part.tool_name}")
                        elif isinstance(event, BuiltinToolResultEvent):
                            if thinking_started:
                                print()
                                thinking_started = False
                            print(f"📤 内置tool返回：{event.result.content}")
                        elif isinstance(event, AgentRunResultEvent):
                            run_result = event.result

                formatter.render_final()
                formatter.reset()

                if run_result is None:
                    raise RuntimeError("Agent 流式运行未返回最终结果")

                all_messages = run_result.all_messages()
                # readline 输入历史和 Pydantic AI 消息历史分别持久化。
                input_handler.save_message_history(all_messages)
                input_handler.save_history()

                print()  # 空行分隔

        except (KeyboardInterrupt, EOFError):
            # 保存历史记录
            input_handler.save_message_history(all_messages)
            input_handler.cleanup()
            raise


async def server_run(settings: Settings):
    configure_logfire()
    agent = create_agent(settings)
    async with AsyncClient() as client:
        logfire.instrument_httpx(client, capture_all=True)
        deps = Deps(client=client)

        while True:
            user_input = input("> ")

            result = agent.run_sync(user_input, deps=deps)
            print(f"返回结果: {result.output}")
            print()
