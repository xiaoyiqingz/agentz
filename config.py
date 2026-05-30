from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class HostedModelSettings:
    model_name: str
    api_key: str | None
    base_url: str | None = None


@dataclass(frozen=True)
class OllamaModelSettings:
    base_url: str
    model_ds: str
    model_qwen: str


@dataclass(frozen=True)
class ModelSettings:
    deepseek: HostedModelSettings
    qwen: HostedModelSettings
    mimo: HostedModelSettings
    ollama: OllamaModelSettings


@dataclass(frozen=True)
class ObservabilitySettings:
    backend: str
    langfuse_base_url: str
    langfuse_public_key: str | None
    langfuse_secret_key: str | None


@dataclass(frozen=True)
class Settings:
    models: ModelSettings
    observability: ObservabilitySettings
    tavily_api_key: str | None
    config_path: Path
    mcp_config_path: Path
    skills_dir: Path
    context_keep_recent_turns: int
    context_enable_summary: bool
    context_summary_trigger_turns: int
    context_summary_max_turns: int


def load_settings(env: dict[str, str] | None = None) -> Settings:
    """Build project settings from process environment."""
    values = env or os.environ
    base_path = Path(__file__).resolve().parent

    return Settings(
        models=ModelSettings(
            deepseek=HostedModelSettings(
                model_name=values.get("DEEPSEEK_MODEL_NAME", "deepseek-chat"),
                api_key=values.get("DEEPSEEK_API_KEY"),
            ),
            qwen=HostedModelSettings(
                model_name=values.get("QWEN_MODEL_NAME", "qwen3-coder-plus"),
                api_key=values.get("QWEN_API_KEY"),
                base_url=values.get("QWEN_BASE_URL"),
            ),
            mimo=HostedModelSettings(
                model_name=values.get("MIMO_MODEL_NAME", "mimo-v2.5-pro"),
                api_key=values.get("MIMO_API_KEY"),
                base_url=values.get(
                    "MIMO_BASE_URL",
                    "https://api.xiaomimimo.com/v1",
                ),
            ),
            ollama=OllamaModelSettings(
                base_url=values.get(
                    "OLLAMA_BASE_URL", "http://localhost:11434/v1"
                ),
                model_ds=values.get("OLLAMA_MODEL_DS", "deepseek-r1:7b"),
                model_qwen=values.get("OLLAMA_MODEL_QWEN", "qwen3:8b"),
            ),
        ),
        observability=ObservabilitySettings(
            backend=values.get("OBS_BACKEND", "logfire"),
            langfuse_base_url=values.get(
                "LANGFUSE_BASE_URL", "https://cloud.langfuse.com"
            ),
            langfuse_public_key=values.get("LANGFUSE_PUBLIC_KEY"),
            langfuse_secret_key=values.get("LANGFUSE_SECRET_KEY"),
        ),
        tavily_api_key=values.get("TAVILY_API_KEY"),
        config_path=_resolve_path(values.get("CONFIG_PATH", "~"), base_path),
        mcp_config_path=_resolve_path(
            values.get("MCP_CONFIG_PATH", "./mcp.json"), base_path
        ),
        skills_dir=_resolve_path(
            values.get("SKILLS_DIR", ".agents/skills"), base_path
        ),
        context_keep_recent_turns=int(
            values.get(
                "CONTEXT_KEEP_RECENT_TURNS",
                values.get("CONTEXT_KEEP_RECENT_MESSAGES", "12"),
            )
        ),
        context_enable_summary=values.get(
            "CONTEXT_ENABLE_SUMMARY", "true"
        ).lower() not in {"0", "false", "no", "off"},
        context_summary_trigger_turns=int(
            values.get(
                "CONTEXT_SUMMARY_TRIGGER_TURNS",
                values.get("CONTEXT_SUMMARY_TRIGGER_MESSAGES", "30"),
            )
        ),
        context_summary_max_turns=int(
            values.get(
                "CONTEXT_SUMMARY_MAX_TURNS",
                values.get("CONTEXT_SUMMARY_MAX_MESSAGES", "24"),
            )
        ),
    )


def _resolve_path(raw_path: str, base_path: Path) -> Path:
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute():
        return candidate
    return (base_path / candidate).resolve()
