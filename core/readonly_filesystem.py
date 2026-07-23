"""Read-only FileSystem capability setup for a session project."""

from __future__ import annotations

from pathlib import Path

from pydantic_ai.capabilities import Toolset
from pydantic_ai.toolsets import FilteredToolset
from pydantic_ai_harness import FileSystem

READ_ONLY_FILESYSTEM_TOOLS = frozenset(
    {"read_file", "list_directory", "search_files", "find_files", "file_info"}
)


def build_readonly_filesystem(project_path: Path) -> Toolset:
    """Expose only inspection tools from Harness FileSystem for one project root."""
    filesystem = FileSystem(root_dir=project_path)
    toolset = FilteredToolset(
        filesystem.get_toolset(),
        filter_func=lambda _ctx, tool_def: tool_def.name in READ_ONLY_FILESYSTEM_TOOLS,
    )
    return Toolset(toolset)
