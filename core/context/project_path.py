from __future__ import annotations

from pathlib import Path

from core.context.models import SessionMeta


def normalize_project_path(
    raw_project_path: str | Path | None,
    cwd: Path | None = None,
) -> Path:
    """Resolve a requested project path, defaulting to the current directory."""
    base_dir = (cwd or Path.cwd()).resolve()
    if raw_project_path is None:
        return base_dir

    candidate = Path(raw_project_path).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (base_dir / candidate).resolve()


def resolve_session_project_path(
    session_meta: SessionMeta | None,
    requested_project_path: str | Path | None,
    cwd: Path | None = None,
) -> tuple[Path, bool]:
    """Prefer the project path persisted for a resumed session when present."""
    base_dir = (cwd or Path.cwd()).resolve()
    if session_meta is not None and session_meta.project_path:
        resolved_meta_path = Path(session_meta.project_path).expanduser().resolve()
        ignored_cli_path = requested_project_path is not None and (
            normalize_project_path(requested_project_path, base_dir)
            != resolved_meta_path
        )
        return resolved_meta_path, ignored_cli_path

    return normalize_project_path(requested_project_path, base_dir), False
