from __future__ import annotations

from typing import Any, Protocol

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelRequest

from config.settings import Settings
from models.mimo import build_mimo_model

from .deps import Deps
from .history_processors import (
    SUMMARY_METADATA_KEY,
    is_summary_request,
    split_prefix_and_turns,
)
from .models import ConversationSummary, utc_now

SUMMARY_SYSTEM_PROMPT = """
You summarize prior turns of an AI assistant conversation.

Produce a compact summary that helps the assistant continue the conversation.
Focus on:
- user goals and constraints
- key facts already established
- decisions already made
- unresolved questions
- files, modules, or entities that matter

Do not add facts that are not present in the conversation.
Do not include conversational filler.
Return plain text using exactly this template:
HISTORICAL SUMMARY
Goals: ...
Constraints: ...
Established facts: ...
Decisions: ...
Open questions: ...
Relevant files and entities: ...
END HISTORICAL SUMMARY

Rules:
- Keep exactly one line for each field after the title line.
- Use `none` when a field has no content.
- Do not emit bullets, numbering, markdown emphasis, or code fences.
- If an existing summary is provided, refine it instead of duplicating content.
"""


class SummaryRunner(Protocol):
    async def run(self, user_prompt: str, **kwargs: Any) -> Any: ...


def build_summarizer_agent(settings: Settings) -> Agent:
    return Agent(
        model=build_mimo_model(settings),
        system_prompt=SUMMARY_SYSTEM_PROMPT,
        output_type=str,
    )


def is_summary_message(message: ModelMessage) -> bool:
    return is_summary_request(message)


def select_turns_for_summary(
    messages: list[ModelMessage],
    *,
    keep_recent_turns: int,
    max_turns: int,
) -> list[list[ModelMessage]]:
    _, turns = split_prefix_and_turns(messages)
    if len(turns) <= keep_recent_turns:
        return []
    candidates = turns[:-keep_recent_turns] if keep_recent_turns > 0 else turns
    if max_turns > 0 and len(candidates) > max_turns:
        return candidates[-max_turns:]
    return candidates


def _part_to_text(part: Any) -> str:
    if hasattr(part, "content"):
        return str(part.content)
    if hasattr(part, "tool_name"):
        args = getattr(part, "args", None)
        return f"tool={part.tool_name} args={args}"
    return repr(part)


def render_messages_for_summary(messages: list[ModelMessage]) -> str:
    chunks: list[str] = []
    for index, message in enumerate(messages, start=1):
        role = "request" if isinstance(message, ModelRequest) else "response"
        parts_text = " | ".join(_part_to_text(part) for part in message.parts)
        chunks.append(f"{index}. {role}: {parts_text}")
    return "\n".join(chunks)


def flatten_turns(turns: list[list[ModelMessage]]) -> list[ModelMessage]:
    return [message for turn in turns for message in turn]


def build_summary_prompt(
    messages: list[ModelMessage],
    existing_summary: str | None = None,
) -> str:
    sections = [
        "Summarize the following earlier conversation turns for future context reuse.",
        "Keep the summary factual and concise.",
        "Return plain text using exactly this template:",
        "HISTORICAL SUMMARY\n"
        "Goals: ...\n"
        "Constraints: ...\n"
        "Established facts: ...\n"
        "Decisions: ...\n"
        "Open questions: ...\n"
        "Relevant files and entities: ...\n"
        "END HISTORICAL SUMMARY",
    ]
    if existing_summary:
        sections.append(f"Existing summary to refine:\n{existing_summary.strip()}")
    sections.append(f"Conversation turns:\n{render_messages_for_summary(messages)}")
    return "\n\n".join(sections)


async def maybe_refresh_summary(
    summarizer: SummaryRunner,
    deps: Deps,
    all_messages: list[ModelMessage],
) -> ConversationSummary | None:
    settings = deps.settings
    if not settings.context_enable_summary:
        return None

    _, all_turns = split_prefix_and_turns(all_messages)
    turn_count = len(all_turns)
    if turn_count < settings.context_summary_trigger_turns:
        return None

    existing_summary = deps.session_store.load_summary()
    refresh_floor = turn_count - settings.context_keep_recent_turns
    if (
        existing_summary is not None
        and existing_summary.turn_count_at_summary >= refresh_floor
    ):
        return existing_summary

    selected_turns = select_turns_for_summary(
        all_messages,
        keep_recent_turns=settings.context_keep_recent_turns,
        max_turns=settings.context_summary_max_turns,
    )
    if not selected_turns:
        return None
    selected_messages = flatten_turns(selected_turns)

    prompt = build_summary_prompt(
        selected_messages,
        existing_summary.summary_text if existing_summary is not None else None,
    )
    result = await summarizer.run(
        prompt,
        conversation_id="new",
        metadata={"session_id": deps.session_id, "purpose": "conversation-summary"},
        infer_name=False,
    )
    summary_text = str(result.output).strip()
    if not summary_text:
        return None

    summary = ConversationSummary(
        session_id=deps.session_id,
        conversation_id=deps.conversation_id,
        summary_text=summary_text,
        turn_count_at_summary=turn_count,
        updated_at=utc_now(),
    )
    deps.session_store.save_summary(summary)
    return summary
