"""
专门化 Agent

为 Planning Design 模式创建各个专门化的 Agent 实例。
每个 Agent 专注于特定领域的任务，配备相应的工具和提示词。
"""

from typing import Dict
from pydantic_ai import Agent
from dataclasses import dataclass
from httpx import AsyncClient

from models.qwen import model_qwen
from models.planning import AgentEnum
from prompts.planning_prompts import (
    get_code_agent_prompt,
    get_weather_agent_prompt,
    get_search_agent_prompt,
    get_general_agent_prompt,
)
from tools.tools_registry import (
    get_code_tools,
    get_weather_tools,
    get_search_tools,
    get_all_tools,
)


@dataclass
class Deps:
    """Agent 依赖项（与 server.py 中的 Deps 保持一致）"""

    client: AsyncClient


# ==================== 专门化 Agent 创建 ====================


def _create_code_agent() -> Agent:
    """创建 Code Agent（代码相关任务）"""
    return Agent(
        name="code_agent",
        model=model_qwen,
        deps_type=Deps,
        tools=get_code_tools(),
        system_prompt=get_code_agent_prompt(),
    )


def _create_weather_agent() -> Agent:
    """创建 Weather Agent（天气/时间相关任务）"""
    return Agent(
        name="weather_agent",
        model=model_qwen,
        deps_type=Deps,
        tools=get_weather_tools(),
        system_prompt=get_weather_agent_prompt(),
    )


def _create_search_agent() -> Agent:
    """创建 Search Agent（搜索相关任务）"""
    return Agent(
        name="search_agent",
        model=model_qwen,
        deps_type=Deps,
        tools=get_search_tools(),
        system_prompt=get_search_agent_prompt(),
    )


def _create_general_agent() -> Agent:
    """创建 General Agent（通用任务）"""
    return Agent(
        name="general_agent",
        model=model_qwen,
        deps_type=Deps,
        tools=get_all_tools(),
        system_prompt=get_general_agent_prompt(),
    )


# ==================== Agent 实例 ====================

# 延迟初始化：在首次使用时创建 Agent 实例
_code_agent: Agent | None = None
_weather_agent: Agent | None = None
_search_agent: Agent | None = None
_general_agent: Agent | None = None


def _get_code_agent() -> Agent:
    """获取 Code Agent 实例（延迟初始化）"""
    global _code_agent
    if _code_agent is None:
        _code_agent = _create_code_agent()
    return _code_agent


def _get_weather_agent() -> Agent:
    """获取 Weather Agent 实例（延迟初始化）"""
    global _weather_agent
    if _weather_agent is None:
        _weather_agent = _create_weather_agent()
    return _weather_agent


def _get_search_agent() -> Agent:
    """获取 Search Agent 实例（延迟初始化）"""
    global _search_agent
    if _search_agent is None:
        _search_agent = _create_search_agent()
    return _search_agent


def _get_general_agent() -> Agent:
    """获取 General Agent 实例（延迟初始化）"""
    global _general_agent
    if _general_agent is None:
        _general_agent = _create_general_agent()
    return _general_agent


# ==================== 公共接口 ====================


def get_code_agent() -> Agent:
    """获取 Code Agent 实例"""
    return _get_code_agent()


def get_weather_agent() -> Agent:
    """获取 Weather Agent 实例"""
    return _get_weather_agent()


def get_search_agent() -> Agent:
    """获取 Search Agent 实例"""
    return _get_search_agent()


def get_general_agent() -> Agent:
    """获取 General Agent 实例"""
    return _get_general_agent()


# Agent 注册表
_agent_registry: Dict[AgentEnum, callable] = {
    AgentEnum.CODE_AGENT: _get_code_agent,
    AgentEnum.WEATHER_AGENT: _get_weather_agent,
    AgentEnum.SEARCH_AGENT: _get_search_agent,
    AgentEnum.GENERAL_AGENT: _get_general_agent,
    AgentEnum.DEFAULT_AGENT: _get_general_agent,  # 默认使用 General Agent
}


def get_agent_by_type(agent_type: AgentEnum) -> Agent:
    """
    根据 Agent 类型获取对应的 Agent 实例

    Args:
        agent_type: Agent 类型枚举

    Returns:
        Agent: 对应的 Agent 实例
    """
    if agent_type not in _agent_registry:
        # 如果类型不在注册表中，使用默认 Agent
        return _get_general_agent()

    return _agent_registry[agent_type]()


# 为了向后兼容，提供直接的 Agent 实例访问（延迟初始化）
# 注意：这些是函数，调用时返回 Agent 实例
code_agent = _get_code_agent
weather_agent = _get_weather_agent
search_agent = _get_search_agent
general_agent = _get_general_agent
