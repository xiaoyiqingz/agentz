"""Bounded batch file reading and searching for project analysis."""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_ai import FunctionToolset, RunContext
from pydantic_ai.tools import Tool

from core.context.deps import Deps

MAX_BATCH_FILES = 6
MAX_BATCH_SEARCHES = 5
MAX_TOTAL_CHARS = 30_000
MAX_SEARCH_MATCHES = 200
MAX_SEARCHED_FILES = 2_000
MAX_MATCH_LINE_CHARS = 1_000
PROTECTED_PARTS = {".git", ".env", "__pycache__"}


class FileReadSpec(BaseModel):
    path: str
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=300, ge=1, le=1_000)


class FileSearchSpec(BaseModel):
    pattern: str = Field(min_length=1, max_length=500)
    path: str = "."
    include_glob: str | None = None


def _resolve_project_path(project_path: Path, candidate: str) -> Path:
    root = project_path.resolve()
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"路径超出当前项目目录: {candidate}") from exc
    if any(part in PROTECTED_PARTS for part in resolved.relative_to(root).parts):
        raise ValueError(f"不允许访问受保护路径: {candidate}")
    return resolved


async def read_files_tool(
    ctx: RunContext[Deps], files: list[FileReadSpec]
) -> list[dict[str, object]]:
    """Read 2-6 known project files in one call, with a shared output budget."""
    if not 1 <= len(files) <= MAX_BATCH_FILES:
        raise ValueError(f"files 数量必须在 1 到 {MAX_BATCH_FILES} 之间")
    results: list[dict[str, object]] = []
    remaining = MAX_TOTAL_CHARS
    for spec in files:
        path = _resolve_project_path(ctx.deps.project_path, spec.path)
        if not path.is_file():
            results.append({"path": spec.path, "error": "文件不存在或不是普通文件"})
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            results.append({"path": spec.path, "error": "文件不是 UTF-8 文本"})
            continue
        selected_content = "\n".join(lines[spec.offset : spec.offset + spec.limit])
        content = selected_content[:remaining]
        results.append(
            {
                "path": spec.path,
                "offset": spec.offset,
                "content": content,
                "truncated": len(content) < len(selected_content),
            }
        )
        remaining -= len(content)
        if remaining <= 0:
            break
    return results


async def search_files_batch_tool(
    ctx: RunContext[Deps], searches: list[FileSearchSpec]
) -> list[dict[str, object]]:
    """Run up to five independent content searches across project files in one call."""
    if not 1 <= len(searches) <= MAX_BATCH_SEARCHES:
        raise ValueError(f"searches 数量必须在 1 到 {MAX_BATCH_SEARCHES} 之间")
    results: list[dict[str, object]] = []
    remaining = MAX_SEARCH_MATCHES
    scanned_files = 0
    for spec in searches:
        try:
            regex = re.compile(spec.pattern)
        except re.error as exc:
            results.append({"pattern": spec.pattern, "path": spec.path, "error": f"无效正则表达式: {exc}"})
            continue
        root = _resolve_project_path(ctx.deps.project_path, spec.path)
        if not root.exists():
            results.append({"pattern": spec.pattern, "path": spec.path, "error": "路径不存在"})
            continue
        candidates = [root] if root.is_file() else root.rglob("*")
        matches: list[dict[str, object]] = []
        for candidate in candidates:
            if remaining <= 0 or scanned_files >= MAX_SEARCHED_FILES:
                break
            if not candidate.is_file():
                continue
            try:
                candidate = _resolve_project_path(ctx.deps.project_path, str(candidate))
            except ValueError:
                continue
            if not candidate.is_file():
                continue
            scanned_files += 1
            relative = str(candidate.relative_to(ctx.deps.project_path.resolve()))
            if spec.include_glob and not fnmatch.fnmatch(relative, spec.include_glob):
                continue
            try:
                lines = candidate.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            for line_number, line in enumerate(lines, start=1):
                if regex.search(line):
                    matches.append(
                        {
                            "path": relative,
                            "line": line_number,
                            "text": line[:MAX_MATCH_LINE_CHARS],
                            "line_truncated": len(line) > MAX_MATCH_LINE_CHARS,
                        }
                    )
                    remaining -= 1
                    if remaining <= 0:
                        break
        results.append(
            {
                "pattern": spec.pattern,
                "path": spec.path,
                "matches": matches,
                "truncated": remaining <= 0 or scanned_files >= MAX_SEARCHED_FILES,
            }
        )
    return results


def build_batch_file_toolset() -> FunctionToolset:
    return FunctionToolset(
        tools=[
            Tool(read_files_tool, name="read_files"),
            Tool(search_files_batch_tool, name="search_files_batch"),
        ],
        instructions="Use batch file tools only for independent, known targets.",
    )
