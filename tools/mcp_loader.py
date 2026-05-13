"""
MCP toolset 通用加载入口。

通过项目级 `mcp.json` 配置文件加载 MCP servers。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic_ai.mcp import load_mcp_servers
from config import Settings


def get_mcp_config_path(settings: Settings) -> Path:
    """
    获取 MCP 配置文件路径。
    """
    return settings.mcp_config_path


def get_configured_mcp_toolsets(settings: Settings) -> list[Any]:
    """
    从 JSON 配置文件中加载 MCP toolsets。

    配置文件缺失时返回空列表。
    """
    config_path = get_mcp_config_path(settings)
    if not config_path.exists():
        return []

    return load_mcp_servers(config_path)


def get_all_mcp_toolsets(settings: Settings) -> list[Any]:
    """
    获取所有通过配置文件启用的 MCP toolsets。
    """
    return get_configured_mcp_toolsets(settings)
