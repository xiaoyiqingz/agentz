from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    deepseek_api_key: str | None
    deepseek_model_name: str
    qwen_base_url: str | None
    qwen_api_key: str | None
    qwen_model_name: str
    ollama_base_url: str
    ollama_model_ds: str
    ollama_model_qwen: str
    tavily_api_key: str | None
    mcp_config_path: Path
    skills_dir: Path


def load_settings(env: dict[str, str] | None = None) -> Settings:
    """Build project settings from process environment."""
    values = env or os.environ
    project_root = Path(__file__).resolve().parent

    return Settings(
        deepseek_api_key=values.get("DEEPSEEK_API_KEY"),
        deepseek_model_name=values.get("DEEPSEEK_MODEL_NAME", "deepseek-chat"),
        qwen_base_url=values.get("QWEN_BASE_URL"),
        qwen_api_key=values.get("QWEN_API_KEY"),
        qwen_model_name=values.get("QWEN_MODEL_NAME", "qwen3-coder-plus"),
        ollama_base_url=values.get("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        ollama_model_ds=values.get("OLLAMA_MODEL_DS", "deepseek-r1:7b"),
        ollama_model_qwen=values.get("OLLAMA_MODEL_QWEN", "qwen3:8b"),
        tavily_api_key=values.get("TAVILY_API_KEY"),
        mcp_config_path=_resolve_path(
            values.get("MCP_CONFIG_PATH", "./mcp.json"), project_root
        ),
        skills_dir=_resolve_path(values.get("SKILLS_DIR", "./skills"), project_root),
    )


def _resolve_path(raw_path: str, project_root: Path) -> Path:
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute():
        return candidate
    return (project_root / candidate).resolve()
