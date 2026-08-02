"""Sandboxed FileSystem capability setup for a session project."""

from __future__ import annotations

from pathlib import Path

from pydantic_ai.capabilities import Toolset
from pydantic_ai.toolsets import FilteredToolset
from pydantic_ai_harness import FileSystem

PROJECT_FILESYSTEM_TOOLS = frozenset(
    {
        "read_file",
        "write_file",
        "edit_file",
        "list_directory",
        "search_files",
        "find_files",
        "create_directory",
        "file_info",
    }
)


def build_project_filesystem(project_path: Path) -> Toolset:
    """Expose sandboxed project file tools, including controlled writes.

    ``FileSystem`` keeps all operations inside ``project_path`` and retains its
    default protected patterns for Git metadata, environment files, and keys.
    """
    filesystem = FileSystem(root_dir=project_path)
    toolset = FilteredToolset(
        filesystem.get_toolset(),
        filter_func=lambda _ctx, tool_def: tool_def.name in PROJECT_FILESYSTEM_TOOLS,
    )
    return Toolset(toolset)
