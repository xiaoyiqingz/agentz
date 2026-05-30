from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
from pathlib import Path
from httpx import AsyncClient
from input_handler import InputHandler
from config import Settings
from context.deps import Deps
from context.history_processors import build_history_processors
from context.session_runtime import initialize_session_runtime
from context.summarizer import build_summarizer_agent, maybe_refresh_summary
from models.mimo import build_mimo_model
from observability import configure_observability, instrument_http_client
from prompts.prompt import get_smart_assistant_prompt
from tools.tools_registry import (
    get_all_tools,
    get_all_toolsets,
    get_tool_status_labels,
)
from output_formatter import create_formatter
from commands.builtin_commands import process_builtin_command, CommandType
from stream_event_handler import consume_stream_events

def create_agent(settings: Settings) -> Agent:
    tools_list = get_all_tools(settings)
    toolsets_list = get_all_toolsets(settings)

    agent_kwargs = {
        "model": build_mimo_model(settings),
        "deps_type": Deps,
        "system_prompt": get_smart_assistant_prompt(),
        "history_processors": build_history_processors(settings),
    }
    if tools_list:
        agent_kwargs["tools"] = tools_list
    if toolsets_list:
        agent_kwargs["toolsets"] = toolsets_list

    return Agent(**agent_kwargs)


async def server_run_stream(
    settings: Settings,
    session_id: str,
    requested_project_path: str | None = None,
):
    tool_status_labels = get_tool_status_labels()
    configure_observability(settings)
    agent = create_agent(settings)
    summarizer = build_summarizer_agent(settings)
    # 初始化命令行输入处理器
    config_path = settings.config_path
    input_handler = InputHandler(config_path, session_id=session_id)
    input_handler.initialize()
    session_runtime = initialize_session_runtime(
        config_path=config_path,
        session_id=session_id,
        requested_project_path=requested_project_path,
    )
    session_store = session_runtime.session_store
    all_messages: list[ModelMessage] = session_runtime.all_messages
    conversation_id = session_runtime.conversation_id
    project_path = session_runtime.project_path
    print(f"当前项目目录: {project_path}")
    if session_runtime.ignored_cli_project_path:
        print("已恢复该 session 绑定的项目目录，忽略本次传入的 --project-path。")

    # 创建统一的格式化器
    # 部分终端对 rich Live 的重绘兼容性较差，会把每次刷新都落成新行。
    # 因此默认关闭 Live，改为直接流式输出原始文本，结束时不再重复整段渲染。
    formatter = create_formatter(use_live=False)

    async with AsyncClient() as client:
        instrument_http_client(client)
        deps = Deps(
            client=client,
            session_id=session_id,
            conversation_id=conversation_id,
            config_path=config_path,
            project_path=project_path,
            settings=settings,
            session_store=session_store,
        )

        try:
            while True:
                try:
                    # 等待用户输入，交由 prompt_toolkit 负责稳定的命令行编辑体验。
                    user_input = await input_handler.read_input()

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
                                session_store.save_message_history(all_messages)
                                input_handler.save_history()
                                # 退出循环（程序会在 async with 块结束后自然退出）
                                break
                            continue
                        elif command_type == CommandType.CONVERT:
                            # 转换型命令：将转换后的内容作为用户输入传给 agent
                            user_input = result

                    # 在用户输入后加上"！"并返回
                    formatter.print_user_input(user_input)
                    formatter.print_blank_line()
                    formatter.print_rule()
                    formatter.print_status("正在分析问题...")

                    async with agent.run_stream_events(
                        user_input,
                        deps=deps,
                        message_history=all_messages,
                        conversation_id=conversation_id,
                        metadata={
                            "session_id": session_id,
                            "project_path": str(project_path),
                        },
                    ) as stream:
                        stream_result = await consume_stream_events(
                            stream=stream,
                            formatter=formatter,
                            tool_status_labels=tool_status_labels,
                        )

                    formatter.render_final()
                    formatter.reset()

                    final_response_text = stream_result.final_response_text
                    run_result = stream_result.run_result
                    if run_result is None:
                        raise RuntimeError("Agent 流式运行未返回最终结果")

                    all_messages = run_result.all_messages()
                    # readline 输入历史和 Pydantic AI 消息历史分别持久化。
                    session_store.save_message_history(all_messages)
                    try:
                        await maybe_refresh_summary(summarizer, deps, all_messages)
                    except Exception as exc:
                        print(f"\n警告：刷新会话摘要失败：{exc}\n")
                    input_handler.save_history()

                    print()  # 空行分隔
                except (KeyboardInterrupt, EOFError):
                    raise
                except Exception as exc:
                    formatter.reset()
                    print(f"\n本轮处理失败，CLI 将继续运行：{exc}\n")
                    session_store.save_message_history(all_messages)
                    input_handler.save_history()
                    continue

        except (KeyboardInterrupt, EOFError):
            # 保存历史记录
            session_store.save_message_history(all_messages)
            input_handler.cleanup()
            raise


async def server_run(settings: Settings):
    configure_observability(settings)
    agent = create_agent(settings)
    summarizer = build_summarizer_agent(settings)
    config_path = settings.config_path
    session_id = "sync-session"
    session_runtime = initialize_session_runtime(
        config_path=config_path,
        session_id=session_id,
        cwd=Path.cwd().resolve(),
    )
    session_store = session_runtime.session_store
    conversation_id = session_runtime.conversation_id
    project_path = session_runtime.project_path
    async with AsyncClient() as client:
        instrument_http_client(client)
        deps = Deps(
            client=client,
            session_id=session_id,
            conversation_id=conversation_id,
            config_path=config_path,
            project_path=project_path,
            settings=settings,
            session_store=session_store,
        )

        while True:
            user_input = input("> ")

            result = agent.run_sync(
                user_input,
                deps=deps,
                conversation_id=conversation_id,
                metadata={
                    "session_id": session_id,
                    "project_path": str(project_path),
                },
            )
            session_store.save_message_history(result.all_messages())
            try:
                await maybe_refresh_summary(summarizer, deps, result.all_messages())
            except Exception as exc:
                print(f"\n警告：刷新会话摘要失败：{exc}\n")
            print(f"返回结果: {result.output}")
            print()
