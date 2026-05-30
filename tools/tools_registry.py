"""
工具注册表

统一管理所有 Agent 工具的初始化和注册。
"""

from typing import List, Any

from pydantic_ai.tools import Tool
from config import Settings
from tools.mcp_loader import get_all_mcp_toolsets
from tools.project_review import (
    exec_review_command_tool,
    git_diff_file_tool,
    git_diff_summary_tool,
    git_status_summary_tool,
    read_project_file_tool,
    search_repo_tool,
)
from tools.skills_toolset import get_skills_toolset
from tools.time_tools import get_current_time
from tools.web_search import get_tavily_search_tool, get_duckduckgo_search_tool
from tools.weather_tools import get_weather

TOOL_STATUS_LABELS = {
    "list_skills": "正在检查可用技能",
    "load_skill": "正在加载技能",
    "read_skill_resource": "正在读取技能资料",
    "run_skill_script": "正在执行技能脚本",
    "git_status_summary": "正在检查项目变更摘要",
    "git_diff_summary": "正在汇总项目 diff",
    "git_diff_file": "正在读取文件 diff",
    "read_project_file": "正在读取项目文件",
    "search_repo": "正在搜索项目代码",
    "exec_review_command": "正在执行只读 review 命令",
}

HIDDEN_TOOL_RESULT_NAMES = {
    "list_skills",
    "load_skill",
    "read_skill_resource",
    "run_skill_script",
}


def get_all_tools(settings: Settings) -> List[Any]:
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

    # 添加天气工具, 可以重试两次
    tools_list.append(Tool(get_weather, max_retries=2))

    # 添加 Tavily 网页搜索工具（如果可用）
    # tavily_tool = get_tavily_search_tool(settings)
    # if tavily_tool is not None:
    #     tools_list.append(tavily_tool)

    # 添加 DuckDuckGo 网页搜索工具（不需要配置，始终可用）
    duckduckgo_tool = get_duckduckgo_search_tool()
    if duckduckgo_tool is not None:
        tools_list.append(duckduckgo_tool)

    tools_list.extend(get_project_review_tools())

    return tools_list


def get_project_review_tools() -> List[Any]:
    return [
        Tool(read_project_file_tool, name="read_project_file"),
        Tool(git_status_summary_tool, name="git_status_summary"),
        Tool(git_diff_summary_tool, name="git_diff_summary"),
        Tool(git_diff_file_tool, name="git_diff_file"),
        Tool(search_repo_tool, name="search_repo"),
        Tool(exec_review_command_tool, name="exec_review_command"),
    ]


def get_tool_status_labels() -> dict[str, str]:
    return dict(TOOL_STATUS_LABELS)


def get_hidden_tool_result_names() -> set[str]:
    return set(HIDDEN_TOOL_RESULT_NAMES)


def get_all_toolsets(settings: Settings) -> List[Any]:
    """
    获取所有可用的外部 toolsets，例如 MCP servers 和 Agent Skills。
    """
    toolsets: List[Any] = []
    toolsets.extend(get_all_mcp_toolsets(settings))
    toolsets.append(get_skills_toolset(settings))
    return toolsets
