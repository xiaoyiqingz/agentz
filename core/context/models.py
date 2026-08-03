from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SessionMeta(BaseModel):
    session_id: str
    conversation_id: str
    project_path: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    resumed: bool = False


class ConversationSummary(BaseModel):
    session_id: str
    conversation_id: str
    summary_text: str
    turn_count_at_summary: int
    updated_at: datetime = Field(default_factory=utc_now)


class UsageLimitRecovery(BaseModel):
    """Persisted evidence needed to continue a run stopped by a usage limit."""

    session_id: str
    original_prompt: str
    tool_transcript: str
    limit_message: str
    updated_at: datetime = Field(default_factory=utc_now)
