"""MCP toolset loading and registration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic_ai.mcp import load_mcp_toolsets

from config.settings import Settings


def get_mcp_config_path(settings: Settings) -> Path:
    """Return the configured project MCP configuration path."""
    return settings.mcp_config_path


def get_configured_mcp_toolsets(settings: Settings) -> list[Any]:
    """Load MCP toolsets from the optional JSON configuration file."""
    config_path = get_mcp_config_path(settings)
    if not config_path.exists():
        return []

    try:
        return load_mcp_toolsets(config_path)
    except ValueError as exc:
        # Pydantic AI resolves ${VAR} placeholders while loading. A template
        # configuration without its runtime credentials must remain optional.
        if "Environment variable" in str(exc):
            return []
        raise


def build_mcp_toolsets(settings: Settings) -> list[Any]:
    """Build toolsets from the optional project MCP configuration."""
    return get_configured_mcp_toolsets(settings)
