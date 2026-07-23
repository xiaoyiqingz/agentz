"""
交互式客户端程序
等待用户输入，在输入内容后加上"！"并返回给用户
按 Ctrl-C 可以退出程序
"""

import argparse
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from config.settings import load_settings
from utils.session import normalize_session_id


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="启动交互式 agent 客户端")
    parser.add_argument(
        "--resume",
        metavar="SESSION_ID",
        help="恢复指定 session id 的输入历史和消息历史",
    )
    parser.add_argument(
        "--project-path",
        help="当前 session 绑定的项目目录；不传时默认使用当前工作目录",
    )
    parser.add_argument(
        "--agentz-home",
        help="AgentZ 数据与配置目录；不传时使用 AGENTZ_HOME 或 ~/.agentz",
    )
    return parser.parse_args(argv)


def _load_agentz_env(agentz_home_override: str | None) -> Path:
    """Load the .env file stored under the resolved AgentZ home directory."""
    raw_home = agentz_home_override or os.environ.get("AGENTZ_HOME", "~/.agentz")
    agentz_home = Path(raw_home).expanduser()
    if not agentz_home.is_absolute():
        agentz_home = Path.cwd() / agentz_home
    agentz_home = agentz_home.resolve()

    load_dotenv(agentz_home / ".env")
    # The config file location must be stable. Do not let a value inside that file
    # redirect the active home after it has already been selected.
    os.environ["AGENTZ_HOME"] = str(agentz_home)
    return agentz_home


def main():
    """主函数：处理用户输入并返回带感叹号的内容"""
    from core.server import server_run_stream

    args = _parse_args()
    # 在读取模型、MCP、skills 等配置前，先从 AgentZ Home 加载 .env。
    _load_agentz_env(args.agentz_home)
    settings = load_settings()
    session_id, resumed = normalize_session_id(args.resume)

    print("欢迎使用交互式客户端！")
    print("请输入内容（按 Ctrl-C 退出）：")
    print(f"当前 session: {session_id}")
    if resumed:
        print("已根据 --resume 加载该 session 的历史。")

    try:
        asyncio.run(
            server_run_stream(
                settings=settings,
                session_id=session_id,
                requested_project_path=args.project_path,
            )
        )
        # asyncio.run(server_run())

    except KeyboardInterrupt:
        # 捕获 Ctrl-C 信号
        print(f"\n\n程序已退出，再见！当前 session: {session_id}")
    except EOFError:
        # 捕获 EOF 信号（某些终端环境）
        print(f"\n\n程序已退出，再见！当前 session: {session_id}")


if __name__ == "__main__":
    main()
