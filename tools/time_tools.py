"""
时间相关工具

提供时间相关的工具函数，供 Agent 使用。
"""

from datetime import datetime


def get_current_time() -> str:
    """
    获取当前时间

    Returns:
        str: 格式化的当前时间字符串 (YYYY-MM-DD HH:MM:SS)
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
