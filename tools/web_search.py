"""
网页搜索工具 - Tavily 和 DuckDuckGo 集成

使用 pydantic-ai 自带的 Tavily 和 DuckDuckGo 工具提供网页搜索功能。
参考文档: https://docs.tavily.com/documentation/integrations/pydantic-ai
"""

import os
from typing import Optional
from pydantic_ai.common_tools.tavily import tavily_search_tool
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool


def get_tavily_search_tool() -> Optional[object]:
    """
    获取 Tavily 网页搜索工具

    从环境变量读取 Tavily API Key，如果未配置则返回 None。

    Returns:
        Tavily 搜索工具实例，如果未配置 API Key 则返回 None

    环境变量配置:
        TAVILY_API_KEY: Tavily API 密钥
        获取方式: https://docs.tavily.com/get-an-api-key
    """
    # 从环境变量读取 Tavily API Key
    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        # 如果未配置，返回 None（不启用网页搜索功能）
        return None

    # 创建并返回 Tavily 搜索工具
    return tavily_search_tool(api_key)


def get_duckduckgo_search_tool() -> Optional[object]:
    """
    获取 DuckDuckGo 网页搜索工具

    DuckDuckGo 搜索工具不需要 API Key，可以直接使用。

    Returns:
        DuckDuckGo 搜索工具实例
    """
    # DuckDuckGo 搜索工具不需要配置，直接返回
    return duckduckgo_search_tool()


def get_tavily_config() -> dict:
    """
    获取 Tavily 的配置信息

    返回当前配置的字典，用于调试和日志记录。

    Returns:
        dict: 包含配置信息的字典
    """
    api_key = os.getenv("TAVILY_API_KEY")
    return {
        "api_key_set": bool(api_key),
        "api_key_preview": (
            f"{api_key[:8]}..." if api_key and len(api_key) > 8 else None
        ),
        "enabled": bool(api_key),
    }


def get_duckduckgo_config() -> dict:
    """
    获取 DuckDuckGo 的配置信息

    返回当前配置的字典，用于调试和日志记录。

    Returns:
        dict: 包含配置信息的字典
    """
    return {
        "enabled": True,  # DuckDuckGo 不需要配置，始终可用
        "api_key_required": False,
    }
