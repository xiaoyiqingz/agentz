"""
MCP toolset 通用加载入口。

通过项目级 `mcp.json` 配置文件加载 MCP servers。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pydantic_ai.mcp import load_mcp_servers


def get_mcp_config_path() -> Path:
    """
    获取 MCP 配置文件路径。

    优先读取 `.env` 中的 `MCP_CONFIG_PATH`，否则默认使用当前项目目录下的 `mcp.json`。
    """
    configured_path = os.getenv("MCP_CONFIG_PATH")
    if configured_path:
        return Path(configured_path).expanduser()

    return Path.cwd() / "mcp.json"


def get_configured_mcp_toolsets() -> list[Any]:
    """
    从 JSON 配置文件中加载 MCP toolsets。

    配置文件缺失时返回空列表。
    """
    config_path = get_mcp_config_path()
    if not config_path.exists():
        return []

    return load_mcp_servers(config_path)


def get_all_mcp_toolsets() -> list[Any]:
    """
    获取所有通过配置文件启用的 MCP toolsets。
    """
    return get_configured_mcp_toolsets()
