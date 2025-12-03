from typing import AsyncIterable
from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPServerSSE
from pydantic_ai.messages import (
    ModelMessage,
    SystemPromptPart,
    ThinkingPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
    AgentStreamEvent,
    PartStartEvent,
    PartDeltaEvent,
    ThinkingPartDelta,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    BuiltinToolCallEvent,
    BuiltinToolResultEvent,
)
from datetime import datetime
import logfire
import os
import sys
from pathlib import Path
from httpx import AsyncClient
from dataclasses import dataclass

# 导入 readline 模块以增强命令行输入功能（支持中文删除、历史记录等）
try:
    import readline
except ImportError:
    # 某些系统可能没有 readline，尝试导入 gnureadline（macOS 上可能需要）
    try:
        import gnureadline as readline  # type: ignore[import-untyped]
    except ImportError:
        # 如果都没有，readline 将为 None，但不影响基本功能
        readline = None
from tools.coder import generate, modify
from models.qwen import model_qwen
from models.deepseek import model_deepseek
from prompts.prompt import get_common_prompt
from tools.code_patcher import apply_patch
from tools.code_reader import read_file_lines
from commands.builtin_commands import process_builtin_command, CommandType

# 配置 logfire 将日志输出到文件而不是控制台
logfire.configure()
logfire.instrument_pydantic_ai()


@dataclass
class Deps:
    client: AsyncClient


# mcpServer = MCPServerSSE(url=os.getenv("MCP_SERVER_URL"))
# agent = Agent(model=model, deps_type=Deps, toolsets=[mcpServer])
agent = Agent(
    model=model_qwen,
    deps_type=Deps,
    # system_prompt=get_common_prompt(),
    # toolsets=[mcpServer],
)


@agent.tool_plain
def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@agent.tool
async def get_weather(ctx: RunContext[Deps], city: str) -> str:
    url = f"http://wttr.in/{city}?format=3"
    response = await ctx.deps.client.get(url)
    return response.text


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
    return await modify(code_string, file_path, begin_line)


@agent.tool
async def generate_code(ctx: RunContext[Deps], text: str) -> str:
    return await generate(text)


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


def _save_history(history_file: Path | None, readline_module) -> None:
    """
    保存 readline 历史记录到文件

    Args:
        history_file: 历史记录文件路径
        readline_module: readline 模块（可能为 None）
    """
    if readline_module is None or history_file is None:
        return

    try:
        # 确保目录存在
        history_file.parent.mkdir(parents=True, exist_ok=True)
        # 保存历史记录（即使为空也会创建文件）
        readline_module.write_history_file(str(history_file))
    except Exception as e:
        # 打印错误信息以便调试，但不影响程序运行
        print(
            f"\n警告：无法保存历史记录到 {history_file}: {e}",
            file=sys.stderr,
        )


async def server_run_stream():
    all_messages: list[ModelMessage] = []
    # message_history: list[ModelMessage] | None = None

    # 初始化 readline 以增强命令行输入功能
    history_file = None
    if readline is not None:
        # 获取项目根目录（server.py 所在目录的父目录）
        project_root = Path(__file__).parent
        # 设置历史记录文件路径为项目目录下的 data/agentz_history
        data_dir = project_root / "data"
        # 确保 data 目录存在
        data_dir.mkdir(exist_ok=True)
        history_file = data_dir / "agentz_history"

        try:
            # 尝试加载历史记录
            readline.read_history_file(str(history_file))
        except FileNotFoundError:
            # 历史记录文件不存在，这是正常的（首次运行）
            pass
        except Exception as e:
            # 其他错误（如权限问题）也忽略，不影响程序运行
            print(f"警告：无法加载历史记录文件: {e}")

        # 设置历史记录最大长度
        readline.set_history_length(1000)

        # 配置 readline 选项以改善中文输入体验
        # 这些设置有助于正确处理多字节字符（如中文）
        if hasattr(readline, "parse_and_bind"):
            # 启用更好的编辑功能
            readline.parse_and_bind("set editing-mode emacs")
            # macOS 上可能需要这个设置
            if hasattr(readline, "set_completer_delims"):
                readline.set_completer_delims(
                    readline.get_completer_delims().replace("/", "")
                )

    async with AsyncClient() as client:
        logfire.instrument_httpx(client, capture_all=True)
        deps = Deps(client=client)

        try:
            while True:
                # 等待用户输入（readline 会自动增强 input() 的功能）
                user_input = input("> ")

                # 处理内置命令
                is_builtin, result, command_type = process_builtin_command(user_input)
                if is_builtin:
                    if command_type == CommandType.DIRECT:
                        # 直接处理型命令：显示结果并等待用户继续输入
                        if result is not None:
                            print(result)
                        # 检查是否是退出命令（exit/quit/q）
                        if user_input.strip().lower() in ("exit", "quit", "q"):
                            # 退出前保存历史记录
                            _save_history(history_file, readline)
                            # 退出循环（程序会在 async with 块结束后自然退出）
                            break
                        continue
                    elif command_type == CommandType.CONVERT:
                        # 转换型命令：将转换后的内容作为用户输入传给 agent
                        user_input = result

                # 在用户输入后加上"！"并返回
                async with agent.run_stream(
                    user_input,
                    deps=deps,
                    message_history=all_messages,
                    event_stream_handler=event_stream_handler,
                ) as result:

                    # 处理历史消息
                    for message in result.new_messages():
                        for call in message.parts:
                            if isinstance(call, ToolCallPart):
                                print("调用tool：", call.tool_name)
                            elif isinstance(call, ToolReturnPart):
                                print("tool返回：", call.content)
                            elif isinstance(call, SystemPromptPart):
                                print("系统提示：", call.content)
                            elif isinstance(call, UserPromptPart):
                                print("用户输入：", call.content)
                            elif isinstance(call, ThinkingPart):
                                # 什么也不做，因为已经在 event_stream_handler 中处理了，此处打印只会在Think全部完成后打印内容，太慢
                                pass
                            else:
                                print(type(call))

                    print("\n================\n")
                    """ 流式显示文本内容 """
                    async for message in result.stream_text(delta=True):
                        print(message, end="", flush=True)
                    print()  # 换行

                all_messages = all_messages + result.new_messages()
                # 对于stream_text(delta=True)，result.all_messages()和result.new_messages()都不会返回历史信息
                # 所以需要手动将历史信息添加到all_messages中
                # all_messages = result.all_messages()
                # message_history = result.new_messages()
                # print(all_messages)

                print()  # 空行分隔

        except (KeyboardInterrupt, EOFError):
            # 保存历史记录
            _save_history(history_file, readline)
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
