"""会话上下文与历史管理。"""

from .deps import Deps
from .history_processors import (
    SUMMARY_LABEL,
    SUMMARY_METADATA_KEY,
    build_history_processors,
    inject_summary_if_needed,
    keep_recent_messages,
)
from .models import ConversationSummary, SessionMeta, utc_now
from .session_runtime import SessionRuntime, initialize_session_runtime
from .session_store import SessionStore
from .summarizer import build_summarizer_agent, maybe_refresh_summary

__all__ = [
    "ConversationSummary",
    "Deps",
    "SUMMARY_LABEL",
    "SUMMARY_METADATA_KEY",
    "SessionMeta",
    "SessionRuntime",
    "SessionStore",
    "build_history_processors",
    "build_summarizer_agent",
    "inject_summary_if_needed",
    "initialize_session_runtime",
    "keep_recent_messages",
    "maybe_refresh_summary",
    "utc_now",
]
