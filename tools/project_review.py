from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

from pydantic_ai import RunContext

from core.context.deps import Deps
from tools.file_reader import read_file_lines

MAX_OUTPUT_CHARS = 12000
DEFAULT_TIMEOUT_SECONDS = 15
DISALLOWED_SHELL_SNIPPETS = ("&&", "||", ";", "|", ">", "<", "$(", "`", "\n")
DISALLOWED_GIT_ARGS = (
    "-c",
    "--exec-path",
    "--git-dir",
    "--work-tree",
    "--output",
    "--no-index",
    "--ext-diff",
)
ALLOWED_GIT_SUBCOMMANDS = {"status", "diff", "log"}
ALLOWED_RG_FLAGS = {"-n", "-i", "-A", "-B", "-C", "--glob", "-g"}


class CommandRejectedError(ValueError):
    """Raised when a review command falls outside the readonly whitelist."""


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


def read_project_file(
    project_path: Path,
    file_path: str,
    start_line: int,
    end_line: int,
) -> str:
    resolved = resolve_repo_path(project_path, file_path)
    return read_file_lines(str(resolved), start_line, end_line)


def git_status_summary(project_path: Path) -> str:
    return _run_review_subprocess(
        ["git", "status", "--short", "--branch"],
        cwd=project_path,
    )


def git_diff_summary(project_path: Path, paths: list[str] | None = None) -> str:
    argv = ["git", "diff", "--stat"]
    if paths:
        argv.append("--")
        argv.extend(str(resolve_repo_path(project_path, path).relative_to(project_path)) for path in paths)
    return _run_review_subprocess(argv, cwd=project_path)


def git_diff_file(project_path: Path, file_path: str, max_lines: int = 400) -> str:
    resolved = resolve_repo_path(project_path, file_path)
    relative_path = str(resolved.relative_to(project_path))
    output = _run_review_subprocess(
        ["git", "diff", "--", relative_path],
        cwd=project_path,
    )
    lines = output.splitlines()
    if len(lines) <= max_lines:
        return output
    truncated = "\n".join(lines[:max_lines])
    return f"{truncated}\n\n[输出已截断，共 {len(lines)} 行，仅显示前 {max_lines} 行]"


def search_repo(
    project_path: Path,
    pattern: str,
    glob: str | None = None,
    max_matches: int = 50,
    context: int = 2,
) -> str:
    argv = ["rg", "-n", "--max-count", str(max_matches), "-C", str(context), pattern]
    if glob:
        argv.extend(["--glob", glob])
    argv.append(".")
    return _run_review_subprocess(argv, cwd=project_path)


def exec_review_command(project_path: Path, command: str) -> str:
    argv = _parse_review_command(project_path, command)
    return _run_review_subprocess(argv, cwd=project_path)


async def read_project_file_tool(
    ctx: RunContext[Deps], file_path: str, start_line: int, end_line: int
) -> str:
    return read_project_file(ctx.deps.project_path, file_path, start_line, end_line)


async def git_status_summary_tool(ctx: RunContext[Deps]) -> str:
    return git_status_summary(ctx.deps.project_path)


async def git_diff_summary_tool(
    ctx: RunContext[Deps], paths: list[str] | None = None
) -> str:
    return git_diff_summary(ctx.deps.project_path, paths)


async def git_diff_file_tool(
    ctx: RunContext[Deps], file_path: str, max_lines: int = 400
) -> str:
    return git_diff_file(ctx.deps.project_path, file_path, max_lines=max_lines)


async def search_repo_tool(
    ctx: RunContext[Deps],
    pattern: str,
    glob: str | None = None,
    max_matches: int = 50,
    context: int = 2,
) -> str:
    return search_repo(
        ctx.deps.project_path,
        pattern,
        glob=glob,
        max_matches=max_matches,
        context=context,
    )


async def exec_review_command_tool(ctx: RunContext[Deps], command: str) -> str:
    return exec_review_command(ctx.deps.project_path, command)


def _parse_review_command(project_path: Path, command: str) -> list[str]:
    stripped = command.strip()
    if not stripped:
        raise CommandRejectedError("命令不能为空")
    if any(snippet in stripped for snippet in DISALLOWED_SHELL_SNIPPETS):
        raise CommandRejectedError("命令包含不允许的 shell 连接或重定向语法")

    argv = shlex.split(stripped, posix=True)
    if not argv:
        raise CommandRejectedError("命令不能为空")

    program = argv[0]
    if program == "git":
        return _validate_git_command(project_path, argv)
    if program == "rg":
        return _validate_rg_command(project_path, argv)
    raise CommandRejectedError(f"不支持的 review 命令: {program}")


def _validate_git_command(project_path: Path, argv: list[str]) -> list[str]:
    if len(argv) < 2:
        raise CommandRejectedError("git review 命令必须包含子命令")
    subcommand = argv[1]
    if subcommand not in ALLOWED_GIT_SUBCOMMANDS:
        raise CommandRejectedError(f"不允许的 git 子命令: {subcommand}")

    validated = argv[:2]
    for token in argv[2:]:
        if any(token == bad or token.startswith(f"{bad}=") for bad in DISALLOWED_GIT_ARGS):
            raise CommandRejectedError(f"不允许的 git 参数: {token}")
        if subcommand == "status":
            validated.append(token)
            continue
        if token.startswith("-"):
            validated.append(token)
            continue
        if "/" in token or token.startswith("."):
            resolved = resolve_repo_path(project_path, token)
            validated.append(str(resolved.relative_to(project_path)))
            continue
        validated.append(token)
    return validated


def _validate_rg_command(project_path: Path, argv: list[str]) -> list[str]:
    validated = ["rg"]
    pattern_seen = False
    index = 1
    while index < len(argv):
        token = argv[index]
        if token in {"--glob", "-g"}:
            if index + 1 >= len(argv):
                raise CommandRejectedError(f"参数缺少值: {token}")
            validated.extend([token, argv[index + 1]])
            index += 2
            continue
        if token in ALLOWED_RG_FLAGS:
            validated.append(token)
            index += 1
            continue
        if token.startswith("-"):
            raise CommandRejectedError(f"不允许的 rg 参数: {token}")
        if not pattern_seen:
            validated.append(token)
            pattern_seen = True
            index += 1
            continue
        resolved = resolve_repo_path(project_path, token)
        validated.append(str(resolved.relative_to(project_path)))
        index += 1
    if not pattern_seen:
        raise CommandRejectedError("rg review 命令必须包含搜索模式")
    return validated


def _run_review_subprocess(
    argv: list[str],
    cwd: Path,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    max_output_chars: int = MAX_OUTPUT_CHARS,
) -> str:
    completed = subprocess.run(
        argv,
        cwd=cwd,
        capture_output=True,
        text=True,
        shell=False,
        timeout=timeout,
        check=False,
    )
    sections: list[str] = []
    if completed.stdout:
        sections.append(completed.stdout.strip())
    if completed.stderr:
        sections.append(f"[stderr]\n{completed.stderr.strip()}")
    if not sections:
        sections.append("[命令无输出]")

    output = "\n\n".join(section for section in sections if section)
    if len(output) > max_output_chars:
        output = (
            f"{output[:max_output_chars]}\n\n"
            f"[输出已截断，总长度超过 {max_output_chars} 字符]"
        )
    if completed.returncode != 0:
        return f"[exit_code={completed.returncode}]\n{output}"
    return output
