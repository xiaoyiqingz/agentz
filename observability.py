from __future__ import annotations

import base64
import os
from typing import Any

import logfire

from config import Settings


def configure_observability(settings: Settings) -> None:
    backend = settings.observability.backend.strip().lower()

    if backend == "logfire":
        logfire.configure()
    elif backend == "langfuse":
        _configure_langfuse_export(settings)
        logfire.configure(send_to_logfire=False)
    else:
        raise ValueError(f"Unsupported OBS_BACKEND: {settings.observability.backend}")

    logfire.instrument_pydantic_ai()


def instrument_http_client(client: Any) -> None:
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
