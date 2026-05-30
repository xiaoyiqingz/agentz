from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from httpx import AsyncClient

from config import Settings
from context.session_store import SessionStore


@dataclass
class Deps:
    client: AsyncClient
    session_id: str
    conversation_id: str
    config_path: Path
    project_path: Path
    settings: Settings
    session_store: SessionStore
