"""
MySQL MCP 工具集配置。

通过环境变量按需启用 `@benborla29/mcp-server-mysql`，
并将其作为 Pydantic AI 的 MCP toolset 暴露给主 Agent。
"""

from __future__ import annotations

import os
from typing import Any

from pydantic_ai.mcp import MCPServerStdio


def get_mysql_mcp_toolset() -> MCPServerStdio | None:
    """
    根据环境变量构建 MySQL MCP toolset。

    启用条件：
    - `ENABLE_MYSQL_MCP=true`
    - 且配置了 `MYSQL_CONNECTION_STRING`
      或至少配置了 `MYSQL_HOST` / `MYSQL_USER`

    Returns:
        MCPServerStdio | None: 可用时返回 MCP toolset，否则返回 None。
    """
    if os.getenv("ENABLE_MYSQL_MCP", "").lower() != "true":
        return None

    if not _has_required_mysql_config():
        return None

    command = os.getenv("MYSQL_MCP_COMMAND", "npx")
    args = os.getenv("MYSQL_MCP_ARGS", "-y @benborla29/mcp-server-mysql").split()
    env = _build_mysql_mcp_env()

    return MCPServerStdio(
        command,
        args=args,
        env=env,
        timeout=float(os.getenv("MYSQL_MCP_TIMEOUT", "10")),
        read_timeout=float(os.getenv("MYSQL_MCP_READ_TIMEOUT", "300")),
        tool_prefix=os.getenv("MYSQL_MCP_TOOL_PREFIX") or None,
    )


def _has_required_mysql_config() -> bool:
    if os.getenv("MYSQL_CONNECTION_STRING"):
        return True

    return bool(os.getenv("MYSQL_HOST") and os.getenv("MYSQL_USER"))


def _build_mysql_mcp_env() -> dict[str, str]:
    """
    收集并传递 MySQL MCP server 需要的环境变量。

    这里只透传已设置的值，避免覆盖调用环境中的其他变量。
    """
    env = os.environ.copy()

    allowed_keys = (
        "MYSQL_CONNECTION_STRING",
        "MYSQL_SOCKET_PATH",
        "MYSQL_HOST",
        "MYSQL_PORT",
        "MYSQL_USER",
        "MYSQL_PASS",
        "MYSQL_DB",
        "MYSQL_POOL_SIZE",
        "MYSQL_QUERY_TIMEOUT",
        "MYSQL_CACHE_TTL",
        "MYSQL_QUEUE_LIMIT",
        "MYSQL_CONNECT_TIMEOUT",
        "MYSQL_RATE_LIMIT",
        "MYSQL_MAX_QUERY_COMPLEXITY",
        "MYSQL_SSL",
        "MYSQL_SSL_CA",
        "MYSQL_SSL_CERT",
        "MYSQL_SSL_KEY",
        "MYSQL_SSL_REJECT_UNAUTHORIZED",
        "MYSQL_TIMEZONE",
        "MYSQL_DATE_STRINGS",
        "MYSQL_ENABLE_LOGGING",
        "MYSQL_LOG_LEVEL",
        "MYSQL_METRICS_ENABLED",
        "ALLOW_INSERT_OPERATION",
        "ALLOW_UPDATE_OPERATION",
        "ALLOW_DELETE_OPERATION",
        "ALLOW_DDL_OPERATION",
        "MYSQL_DISABLE_READ_ONLY_TRANSACTIONS",
        "SCHEMA_INSERT_PERMISSIONS",
        "SCHEMA_UPDATE_PERMISSIONS",
        "SCHEMA_DELETE_PERMISSIONS",
        "SCHEMA_DDL_PERMISSIONS",
        "MULTI_DB_WRITE_MODE",
        "IS_REMOTE_MCP",
        "REMOTE_SECRET_KEY",
        "PORT",
    )

    for key in allowed_keys:
        value = os.getenv(key)
        if value is not None:
            env[key] = value

    # 默认仍保持只读，除非用户显式开启写操作。
    env.setdefault("ALLOW_INSERT_OPERATION", "false")
    env.setdefault("ALLOW_UPDATE_OPERATION", "false")
    env.setdefault("ALLOW_DELETE_OPERATION", "false")

    return env


def get_all_mcp_toolsets() -> list[Any]:
    """
    获取所有启用的 MCP toolsets。
    """
    toolsets: list[Any] = []

    mysql_mcp = get_mysql_mcp_toolset()
    if mysql_mcp is not None:
        toolsets.append(mysql_mcp)

    return toolsets
