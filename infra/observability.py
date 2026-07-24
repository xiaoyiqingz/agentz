from __future__ import annotations

import base64
import os
from typing import Any

import logfire

from config.settings import Settings


def observability_enabled(settings: Settings) -> bool:
    """Return whether a supported telemetry backend was explicitly selected."""
    return bool((settings.observability.backend or "").strip())


def configure_observability(settings: Settings) -> None:
    """Configure telemetry only when ``OBS_BACKEND`` is explicitly set."""
    raw_backend = settings.observability.backend
    if raw_backend is None or not raw_backend.strip():
        return

    backend = raw_backend.strip().lower()

    if backend == "logfire":
        logfire.configure()
    elif backend == "langfuse":
        _configure_langfuse_export(settings)
        logfire.configure(send_to_logfire=False)
    else:
        raise ValueError(f"Unsupported OBS_BACKEND: {raw_backend}")

    logfire.instrument_pydantic_ai()


def instrument_http_client(client: Any, settings: Settings) -> None:
    """Instrument HTTPX only when telemetry has been enabled."""
    if not observability_enabled(settings):
        return
    logfire.instrument_httpx(client, capture_all=True)


def _configure_langfuse_export(settings: Settings) -> None:
    public_key = settings.observability.langfuse_public_key
    secret_key = settings.observability.langfuse_secret_key

    if not public_key or not secret_key:
        raise ValueError(
            "LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are required when "
            "OBS_BACKEND=langfuse"
        )

    auth = _build_langfuse_auth_header(public_key, secret_key)
    endpoint = _build_langfuse_otlp_endpoint(settings.observability.langfuse_base_url)
    headers = f"Authorization=Basic {auth},x-langfuse-ingestion-version=4"

    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = endpoint
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = headers
    os.environ["OTEL_EXPORTER_OTLP_TRACES_HEADERS"] = headers


def _build_langfuse_otlp_endpoint(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/api/public/otel"


def _build_langfuse_auth_header(public_key: str, secret_key: str) -> str:
    raw = f"{public_key}:{secret_key}".encode("utf-8")
    return base64.b64encode(raw).decode("ascii")
