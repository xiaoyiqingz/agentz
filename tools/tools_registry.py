"""
工具注册表

统一管理所有 Agent 工具的初始化和注册。
"""

from typing import List, Any
from tools.time_tools import get_current_time
from tools.web_search_mcp import get_tavily_search_tool, get_duckduckgo_search_tool
from tools.weather_tools import get_weather


def get_all_tools() -> List[Any]:
    """
    获取所有可用的工具列表

    此函数负责初始化和注册所有工具，包括：
    - 时间工具 (get_current_time)
    - 天气工具 (get_weather)
    - Tavily 网页搜索工具（如果配置了 API Key）
    - DuckDuckGo 网页搜索工具（不需要配置）
    - 其他工具...

    Returns:
        List[Any]: 工具列表，如果没有任何工具则返回空列表
    """
    tools_list: List[Any] = []

    # 添加时间工具
    tools_list.append(get_current_time)

    # 添加天气工具
    tools_list.append(get_weather)

    # 添加 Tavily 网页搜索工具（如果可用）
    # tavily_tool = get_tavily_search_tool()
    # if tavily_tool is not None:
    #     tools_list.append(tavily_tool)

    # 添加 DuckDuckGo 网页搜索工具（不需要配置，始终可用）
    duckduckgo_tool = get_duckduckgo_search_tool()
    if duckduckgo_tool is not None:
        tools_list.append(duckduckgo_tool)

    # 可以在这里添加更多工具...

    return tools_list
