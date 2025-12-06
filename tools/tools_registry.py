"""
工具注册表

统一管理所有 Agent 工具的初始化和注册。
支持按功能分类工具，用于 Planning Design 模式的专门化 Agent。
"""

from typing import List, Any
from pydantic_ai import RunContext
from pydantic_ai.tools import Tool

from tools.time_tools import get_current_time
from tools.web_search import get_tavily_search_tool, get_duckduckgo_search_tool
from tools.weather_tools import get_weather
from tools.code_reader import read_file_lines
from tools.code_patcher import apply_patch
from tools.coder import generate, modify


# ==================== 代码相关工具函数 ====================


async def read_code_file(
    ctx: RunContext[Any], file_path: str, start_line: int, end_line: int
) -> str:
    """
    读取指定文件的指定行范围代码

    Args:
        ctx: Agent 运行上下文
        file_path: 文件路径
        start_line: 起始行号（从1开始）
        end_line: 结束行号（从1开始）

    Returns:
        str: 指定行范围的代码内容
    """
    return read_file_lines(file_path, start_line, end_line)


async def apply_code_patch_tool(
    ctx: RunContext[Any], file_path: str, patch_string: str
) -> str:
    """
    应用代码补丁到文件

    Args:
        ctx: Agent 运行上下文
        file_path: 目标文件路径
        patch_string: 统一 diff 格式的补丁字符串

    Returns:
        str: 操作结果描述
    """
    success = apply_patch(patch_string, file_path)
    if success:
        return f"✅ 成功将补丁应用到文件: {file_path}"
    else:
        return f"❌ 应用补丁失败: {file_path}"


async def check_and_modify_code(
    ctx: RunContext[Any], code_string: str, file_path: str, begin_line: int = 1
) -> str:
    """
    检查并修改代码

    Args:
        ctx: Agent 运行上下文
        code_string: 代码字符串
        file_path: 文件路径
        begin_line: 代码在文件中的起始行号

    Returns:
        str: 修改后的代码（diff 格式）
    """
    return await modify(code_string, file_path, begin_line)


async def generate_code(ctx: RunContext[Any], text: str) -> str:
    """
    根据描述生成代码

    Args:
        ctx: Agent 运行上下文
        text: 代码需求描述

    Returns:
        str: 生成的代码（带详细注释）
    """
    return await generate(text)


# ==================== 工具分类函数 ====================


def get_code_tools() -> List[Any]:
    """
    获取代码相关工具列表

    Returns:
        List[Any]: 代码工具列表
    """
    return [
        read_code_file,
        apply_code_patch_tool,
        check_and_modify_code,
        generate_code,
    ]


def get_weather_tools() -> List[Any]:
    """
    获取天气/时间相关工具列表

    Returns:
        List[Any]: 天气/时间工具列表
    """
    return [
        get_current_time,
        Tool(get_weather, max_retries=2),  # 天气工具可以重试两次
    ]


def get_search_tools() -> List[Any]:
    """
    获取搜索相关工具列表

    Returns:
        List[Any]: 搜索工具列表
    """
    tools_list: List[Any] = []

    # 添加 DuckDuckGo 网页搜索工具（不需要配置，始终可用）
    duckduckgo_tool = get_duckduckgo_search_tool()
    if duckduckgo_tool is not None:
        tools_list.append(duckduckgo_tool)

    # 添加 Tavily 网页搜索工具（如果可用）
    # tavily_tool = get_tavily_search_tool()
    # if tavily_tool is not None:
    #     tools_list.append(tavily_tool)

    return tools_list


def get_all_tools() -> List[Any]:
    """
    获取所有可用的工具列表

    此函数负责初始化和注册所有工具，包括：
    - 代码工具 (read_code_file, apply_code_patch, check_and_modify_code, generate_code)
    - 时间工具 (get_current_time)
    - 天气工具 (get_weather)
    - 搜索工具 (duckduckgo_search, tavily_search)

    用于通用 Agent 或保持向后兼容。

    Returns:
        List[Any]: 工具列表，如果没有任何工具则返回空列表
    """
    tools_list: List[Any] = []

    # 添加代码工具
    tools_list.extend(get_code_tools())

    # 添加天气/时间工具
    tools_list.extend(get_weather_tools())

    # 添加搜索工具
    tools_list.extend(get_search_tools())

    return tools_list
