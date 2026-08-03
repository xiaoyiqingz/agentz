"""Read-only local Git inspection tools."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Literal

from pydantic_ai import FunctionToolset, RunContext
from pydantic_ai.tools import Tool

from core.context.deps import Deps

MAX_OUTPUT_CHARS = 12000
DEFAULT_TIMEOUT_SECONDS = 15
_SAFE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/@-]*$")

GitOperation = Literal["status", "diff", "log", "show", "blame", "grep", "merge_base"]


def resolve_repo_path(project_path: Path, candidate: str | Path) -> Path:
    project_root = project_path.resolve()
    requested_path = Path(candidate).expanduser()
    resolved = (
        requested_path.resolve()
        if requested_path.is_absolute()
        else (project_root / requested_path).resolve()
    )
    try:
        resolved.relative_to(project_root)
    except ValueError as exc:
        raise ValueError(f"路径超出当前项目目录: {candidate}") from exc
    return resolved


def git_readonly(
    project_path: Path,
    operation: GitOperation,
    *,
    repository_path: str | Path | None = None,
    base_ref: str | None = None,
    target_ref: str = "HEAD",
    path: str | None = None,
    pattern: str | None = None,
    start_line: int | None = None,
    end_line: int | None = None,
    stat: bool = False,
    max_entries: int = 50,
) -> str:
    """Run a bounded, read-only Git inspection command for one project repository.

    ``repository_path`` identifies a Git work tree inside ``project_path``.  When
    omitted, the session project root itself is used for backwards compatibility.
    ``path`` always identifies a file relative to the selected repository.
    """
    if repository_path is not None and not str(repository_path).strip():
        raise ValueError("Git 仓库路径不能为空")
    repository = resolve_repo_path(
        project_path,
        project_path if repository_path is None else repository_path,
    )
    _ensure_git_worktree(
        repository,
        require_repository_root=repository_path is not None,
    )
    _validate_ref(target_ref)
    if base_ref is not None:
        _validate_ref(base_ref)
    if not 1 <= max_entries <= 200:
        raise ValueError("max_entries 必须在 1 到 200 之间")
    argv = ["git", "--no-pager"]
    if operation == "status":
        argv.extend(["status", "--short", "--branch"])
    elif operation == "diff":
        argv.extend(["diff", "--no-ext-diff", "--no-textconv"])
        if stat:
            argv.append("--stat")
        if base_ref is not None:
            argv.append(f"{base_ref}...{target_ref}")
        if path is not None:
            argv.extend(["--", _relative_path(repository, path)])
    elif operation == "log":
        argv.extend(["log", "--oneline", f"--max-count={max_entries}"])
        argv.append(f"{base_ref}..{target_ref}" if base_ref else target_ref)
    elif operation == "show":
        argv.extend(["show", "--no-ext-diff", "--no-textconv", target_ref])
        if stat:
            argv.append("--stat")
    elif operation == "blame":
        if path is None:
            raise ValueError("git blame 必须提供 path")
        argv.append("blame")
        if start_line is not None or end_line is not None:
            if (
                start_line is None
                or end_line is None
                or start_line < 1
                or end_line < start_line
            ):
                raise ValueError("blame 的行范围无效")
            argv.extend(["-L", f"{start_line},{end_line}"])
        argv.extend([target_ref, "--", _relative_path(repository, path)])
    elif operation == "grep":
        if not pattern or len(pattern) > 500:
            raise ValueError("git grep 必须提供不超过 500 字符的 pattern")
        argv.extend(["grep", "-n", "--", pattern])
        if path is not None:
            argv.append(_relative_path(repository, path))
    elif operation == "merge_base":
        if base_ref is None:
            raise ValueError("git merge_base 必须提供 base_ref")
        argv.extend(["merge-base", base_ref, target_ref])
    else:  # pragma: no cover
        raise ValueError(f"不支持的 Git 操作: {operation}")
    return _run_git(argv, repository)


async def git_readonly_tool(
    ctx: RunContext[Deps],
    operation: GitOperation,
    repository_path: str | None = None,
    base_ref: str | None = None,
    target_ref: str = "HEAD",
    path: str | None = None,
    pattern: str | None = None,
    start_line: int | None = None,
    end_line: int | None = None,
    stat: bool = False,
    max_entries: int = 50,
) -> str:
    """Inspect one project Git repository without changing repository state.

    Set ``repository_path`` when the requested repository is a subdirectory of
    the session project root.  It must remain within that root; ``path`` is then
    interpreted relative to the selected repository.
    """
    return git_readonly(
        ctx.deps.project_path,
        operation,
        repository_path=repository_path,
        base_ref=base_ref,
        target_ref=target_ref,
        path=path,
        pattern=pattern,
        start_line=start_line,
        end_line=end_line,
        stat=stat,
        max_entries=max_entries,
    )


def _validate_ref(ref: str) -> None:
    if not ref or len(ref) > 200 or ".." in ref or not _SAFE_REF.fullmatch(ref):
        raise ValueError(f"非法 Git 引用: {ref!r}")


def _relative_path(project_path: Path, path: str) -> str:
    return str(resolve_repo_path(project_path, path).relative_to(project_path.resolve()))


def _ensure_git_worktree(
    repository_path: Path, *, require_repository_root: bool
) -> None:
    """Reject non-repositories and explicit paths that are not repository roots."""
    if not repository_path.is_dir():
        raise ValueError(f"Git 仓库路径不是目录: {repository_path}")
    completed = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree", "--show-toplevel"],
        cwd=repository_path,
        env={
            "PATH": os.environ.get("PATH", ""),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_PAGER": "cat",
            "NO_COLOR": "1",
        },
        capture_output=True,
        text=True,
        timeout=DEFAULT_TIMEOUT_SECONDS,
        check=False,
    )
    output_lines = completed.stdout.splitlines()
    if completed.returncode != 0 or not output_lines or output_lines[0] != "true":
        raise ValueError(f"路径不是 Git 工作区: {repository_path}")
    if require_repository_root and len(output_lines) < 2:
        raise ValueError(f"路径不是 Git 仓库根目录: {repository_path}")
    if require_repository_root and Path(output_lines[1]).resolve() != repository_path.resolve():
        raise ValueError(f"路径不是 Git 仓库根目录: {repository_path}")


def _run_git(argv: list[str], cwd: Path) -> str:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_PAGER": "cat",
        "NO_COLOR": "1",
    }
    completed = subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=DEFAULT_TIMEOUT_SECONDS,
        check=False,
    )
    output = (completed.stdout if completed.returncode == 0 else completed.stderr).strip()
    if not output:
        return "(无输出)"
    if len(output) > MAX_OUTPUT_CHARS:
        return f"{output[:MAX_OUTPUT_CHARS]}\n\n[输出已截断]"
    return output


def build_project_review_toolset() -> FunctionToolset:
    """Build bounded, read-only Git inspection tools."""
    return FunctionToolset(
        tools=[Tool(git_readonly_tool, name="git_readonly")],
        instructions="Use git_readonly to inspect Git state and history; it never changes the repository.",
    )
