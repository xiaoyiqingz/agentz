"""AgentZ 的终端交互入口。"""

from __future__ import annotations

from config.settings import Settings
from commands.builtin_commands import CommandType, process_builtin_command
from core.server import (
    AgentSession,
    build_usage_limit_prompt,
    open_agent_session,
    stream_session_turn,
)
from core.shell_approval import ShellApprovalRequest
from core.stream_event_handler import consume_stream_events, render_message_history
from tools.register import get_tool_status_labels

from .input_handler import InputHandler
from .output_formatter import create_formatter


async def run_cli(
    settings: Settings,
    session_id: str,
    requested_project_path: str | None = None,
) -> None:
    """Run the existing interactive CLI using the shared session service."""
    tool_status_labels = get_tool_status_labels()
    input_handler = InputHandler(settings.agentz_home, session_id=session_id)
    input_handler.initialize()

    async with open_agent_session(
        settings=settings,
        session_id=session_id,
        requested_project_path=requested_project_path,
    ) as session:
        print(f"当前项目目录: {session.project_path}")
        if session.ignored_requested_project_path:
            print("已恢复该 session 绑定的项目目录，忽略本次传入的 --project-path。")

        # Some terminals render every Rich Live refresh on a new line, so keep
        # the existing stable final-Markdown behavior by default.
        formatter = create_formatter(use_live=False)

        if session.all_messages:
            formatter.print_status("正在恢复历史对话...")
            rendered_turns = render_message_history(session.all_messages, formatter)
            print(f"已展示 {rendered_turns} 条历史助手回复。")
            formatter.print_blank_line()

        try:
            while True:
                try:
                    user_input = await input_handler.read_input()
                    recovery_action = {
                        "/continue": "continue",
                        "/summarize": "summarize",
                    }.get(user_input.strip().lower())
                    if recovery_action is not None:
                        recovery = session.runtime.session_store.load_usage_limit_recovery()
                        if recovery is None:
                            print("当前没有可恢复的受限任务。")
                            continue
                        user_input = build_usage_limit_prompt(recovery, recovery_action)
                    is_builtin, result, command_type = process_builtin_command(
                        user_input, session_id=session_id
                    )
                    if is_builtin:
                        if command_type == CommandType.DIRECT:
                            if result is not None:
                                print(result)
                            if user_input.strip().lower() in ("/exit", "/quit", "/q"):
                                session.save_history()
                                input_handler.save_history()
                                break
                            continue
                        if command_type == CommandType.CONVERT:
                            user_input = result

                    formatter.print_user_input(user_input)
                    formatter.print_blank_line()
                    formatter.print_rule()
                    formatter.print_status("正在分析问题...")

                    stream_result = await consume_stream_events(
                        stream=stream_session_turn(session, user_input),
                        formatter=formatter,
                        tool_status_labels=tool_status_labels,
                        on_shell_approval=lambda request: _confirm_shell_command(
                            input_handler, session, request
                        ),
                    )
                    formatter.render_final()
                    formatter.reset()

                    if stream_result.usage_limit_reached is not None:
                        print("\n本轮达到分析预算。输入 /continue 继续分析，或 /summarize 生成阶段结论。\n")
                        input_handler.save_history()
                        continue
                    if stream_result.run_result is None:
                        raise RuntimeError("Agent 流式运行未返回最终结果")
                    input_handler.save_history()
                    print()
                except (KeyboardInterrupt, EOFError):
                    raise
                except Exception as exc:
                    formatter.reset()
                    print(f"\n本轮处理失败，CLI 将继续运行：{exc}\n")
                    session.save_history()
                    input_handler.save_history()
        except (KeyboardInterrupt, EOFError):
            session.save_history()
            input_handler.cleanup()
            raise


async def _confirm_shell_command(
    input_handler: InputHandler,
    session: AgentSession,
    request: ShellApprovalRequest,
) -> None:
    approved = await input_handler.confirm_shell_command(
        request.command,
        request.working_directory,
        request.is_background,
    )
    session.deps.shell_approvals.resolve(request.approval_id, approved)
