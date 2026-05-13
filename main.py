"""
交互式客户端程序
等待用户输入，在输入内容后加上"！"并返回给用户
按 Ctrl-C 可以退出程序
"""

import argparse
import asyncio

from dotenv import load_dotenv

from config import load_settings
from utils.session import normalize_session_id


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="启动交互式 agent 客户端")
    parser.add_argument(
        "--resume",
        metavar="SESSION_ID",
        help="恢复指定 session id 的输入历史和消息历史",
    )
    return parser.parse_args()


def main():
    """主函数：处理用户输入并返回带感叹号的内容"""
    # 启动阶段统一加载环境变量，再初始化依赖配置的模块。
    load_dotenv()

    from server import server_run_stream

    args = _parse_args()
    settings = load_settings()
    session_id, resumed = normalize_session_id(args.resume)

    print("欢迎使用交互式客户端！")
    print(f"当前 session: {session_id}")
    if resumed:
        print("已根据 --resume 加载该 session 的历史。")
    print("请输入内容（按 Ctrl-C 退出）：")

    try:
        asyncio.run(server_run_stream(settings=settings, session_id=session_id))
        # asyncio.run(server_run())

    except KeyboardInterrupt:
        # 捕获 Ctrl-C 信号
        print(f"\n\n程序已退出，再见！当前 session: {session_id}")
    except EOFError:
        # 捕获 EOF 信号（某些终端环境）
        print(f"\n\n程序已退出，再见！当前 session: {session_id}")


if __name__ == "__main__":
    main()
