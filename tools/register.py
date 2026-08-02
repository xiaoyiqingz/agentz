"""Single composition root for every Agent-callable toolset.

Capabilities are intentionally not registered here: they alter the Agent runtime
and are composed by ``core.server`` separately from callable tools.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from config.settings import Settings
from tools.local import build_local_toolsets
from tools.mcp import build_mcp_toolsets
from tools.skills import build_skills_toolsets

TOOL_STATUS_LABELS = {
    "list_skills": "正在检查可用技能",
    "load_skill": "正在加载技能",
    "read_skill_resource": "正在读取技能资料",
    "run_skill_script": "正在执行技能脚本",
    "git_readonly": "正在检查 Git 仓库",
    "read_file": "正在读取项目文件",
    "search_files": "正在搜索项目代码",
    "write_file": "正在写入项目文件",
    "edit_file": "正在修改项目文件",
    "create_directory": "正在创建项目目录",
    "write_plan": "正在更新执行计划",
}

HIDDEN_TOOL_RESULT_NAMES = frozenset(
    {"list_skills", "load_skill", "read_skill_resource", "run_skill_script"}
)


@dataclass(frozen=True)
class AgentToolRegistration:
    """All metadata the server needs for Agent-callable tools."""

    toolsets: list[Any]
    status_labels: dict[str, str]
    hidden_result_names: frozenset[str]


def get_tool_status_labels() -> dict[str, str]:
    """Return presentation labels without instantiating any toolsets."""
    return dict(TOOL_STATUS_LABELS)


def get_hidden_tool_result_names() -> set[str]:
    """Return tool result names the CLI should suppress."""
    return set(HIDDEN_TOOL_RESULT_NAMES)


def build_agent_tools(settings: Settings) -> AgentToolRegistration:
    """Build local, MCP, and Skills toolsets in their registration order.

    Project-scoped tools obtain their project path from ``RunContext.deps``.
    """
    return AgentToolRegistration(
        toolsets=[
            *build_local_toolsets(settings),
            *build_mcp_toolsets(settings),
            *build_skills_toolsets(settings),
        ],
        status_labels=get_tool_status_labels(),
        hidden_result_names=HIDDEN_TOOL_RESULT_NAMES,
    )
