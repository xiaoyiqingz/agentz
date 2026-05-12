#!/usr/bin/env python3
"""
测试工具事件处理的脚本
"""

import asyncio
import uuid
from server import server_run_stream


async def main():
    print("🚀 启动工具事件测试...")
    print(
        "💡 提示：输入一些需要调用工具的问题，比如 '现在几点了？' 或 '北京天气怎么样？'"
    )
    print("=" * 50)

    try:
        await server_run_stream(session_id=str(uuid.uuid7()))
    except KeyboardInterrupt:
        print("\n👋 再见！")
    except Exception as e:
        print(f"❌ 错误：{e}")


if __name__ == "__main__":
    asyncio.run(main())
