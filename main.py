"""
交互式客户端程序
等待用户输入，在输入内容后加上"！"并返回给用户
按 Ctrl-C 可以退出程序
"""

import asyncio
import argparse
import secrets
import time
import uuid
from dotenv import load_dotenv
from server import server_run_stream

# 加载 .env 文件中的环境变量（包括代理设置）
load_dotenv()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="启动交互式 agent 客户端")
    parser.add_argument(
        "--resume",
        metavar="SESSION_ID",
        help="恢复指定 session id 的输入历史和消息历史",
    )
    return parser.parse_args()


def _normalize_session_id(raw_session_id: str | None) -> tuple[str, bool]:
    """
    规范化 session id。

    Returns:
        tuple[str, bool]: (session_id, resumed)
    """
    if raw_session_id:
        try:
            return str(uuid.UUID(raw_session_id)), True
        except ValueError as e:
            raise SystemExit(f"无效的 --resume session id: {raw_session_id}\n{e}") from e

    return _generate_session_id(), False


def _generate_session_id() -> str:
    """
    生成新的 session id。

    优先使用标准库 uuid7；如果运行时不支持，则生成兼容 UUIDv7 布局的 ID。
    """
    if hasattr(uuid, "uuid7"):
        return str(uuid.uuid7())

    # 48-bit Unix epoch milliseconds + UUIDv7 version/variant bits + 74 random bits
    ts_ms = int(time.time() * 1000) & ((1 << 48) - 1)
    rand_a = secrets.randbits(12)
    rand_b = secrets.randbits(62)

    value = ts_ms << 80
    value |= 0x7 << 76
    value |= rand_a << 64
    value |= 0b10 << 62
    value |= rand_b
    return str(uuid.UUID(int=value))


def main():
    """主函数：处理用户输入并返回带感叹号的内容"""
    args = _parse_args()
    session_id, resumed = _normalize_session_id(args.resume)

    print("欢迎使用交互式客户端！")
    print(f"当前 session: {session_id}")
    if resumed:
        print("已根据 --resume 加载该 session 的历史。")
    else:
        print("未提供 --resume，已创建新的 session。")
    print("请输入内容（按 Ctrl-C 退出）：")

    try:
        asyncio.run(server_run_stream(session_id=session_id))
        # asyncio.run(server_run())

    except KeyboardInterrupt:
        # 捕获 Ctrl-C 信号
        print(f"\n\n程序已退出，再见！当前 session: {session_id}")
    except EOFError:
        # 捕获 EOF 信号（某些终端环境）
        print(f"\n\n程序已退出，再见！当前 session: {session_id}")


if __name__ == "__main__":
    main()
