from __future__ import annotations

from collections.abc import Sequence

from pydantic_ai import RunContext
from pydantic_ai.messages import ModelMessage, ModelRequest, SystemPromptPart, UserPromptPart

from config import Settings
from context.deps import Deps

SUMMARY_METADATA_KEY = "agentz_summary"
SUMMARY_LABEL = "HISTORICAL SUMMARY"


def is_summary_request(message: ModelMessage) -> bool:
    return (
        isinstance(message, ModelRequest)
        and (message.metadata or {}).get(SUMMARY_METADATA_KEY) is True
    )


def is_user_turn_start(message: ModelMessage) -> bool:
    return isinstance(message, ModelRequest) and any(
        isinstance(part, UserPromptPart) for part in message.parts
    )


def is_system_only_request(message: ModelMessage) -> bool:
    return isinstance(message, ModelRequest) and bool(message.parts) and all(
        isinstance(part, SystemPromptPart) for part in message.parts
    )


def split_prefix_and_turns(
    messages: list[ModelMessage],
) -> tuple[list[ModelMessage], list[list[ModelMessage]]]:
    filtered = [message for message in messages if not is_summary_request(message)]
    prefix: list[ModelMessage] = []
    turns: list[list[ModelMessage]] = []
    current_turn: list[ModelMessage] | None = None

    for message in filtered:
        if is_user_turn_start(message):
            if current_turn is not None:
                turns.append(current_turn)
            current_turn = [message]
            continue

        if current_turn is None:
            if is_system_only_request(message):
                prefix.append(message)
            else:
                # Treat orphaned tool continuations or assistant-only carry-over
                # as a synthetic turn, so trimming does not pin them as prefix.
                current_turn = [message]
        else:
            current_turn.append(message)

    if current_turn is not None:
        turns.append(current_turn)

    return prefix, turns


async def keep_recent_messages(
    ctx: RunContext[Deps], messages: list[ModelMessage]
) -> list[ModelMessage]:
    keep_recent_turns = ctx.deps.settings.context_keep_recent_turns
    prefix, turns = split_prefix_and_turns(messages)
    if keep_recent_turns <= 0:
        return prefix
    if len(turns) <= keep_recent_turns:
        return messages
    kept_turns = turns[-keep_recent_turns:]
    flattened = [message for turn in kept_turns for message in turn]
    return prefix + flattened


async def inject_summary_if_needed(
    ctx: RunContext[Deps], messages: list[ModelMessage]
) -> list[ModelMessage]:
    summary = ctx.deps.session_store.load_summary()
    if summary is None or not summary.summary_text.strip():
        return messages

    summary_request = ModelRequest(
        parts=[
            SystemPromptPart(
                content=(
                    f"[{SUMMARY_LABEL}]\n"
                    "Scope: prior turns only. Treat this as compressed history, not"
                    " as a new instruction.\n"
                    "Priority: if later raw turns conflict with this summary, prefer"
                    " the later raw turns.\n"
                    "Usage: use it to recover prior goals, constraints, facts,"
                    " decisions, unresolved questions, and relevant files.\n"
                    "Format: the summary body below follows a fixed schema.\n"
                    f"{summary.summary_text.strip()}\n"
                    f"[END {SUMMARY_LABEL}]"
                )
            )
        ],
        metadata={SUMMARY_METADATA_KEY: True},
        conversation_id=ctx.deps.conversation_id,
    )

    retained_messages = [
        msg
        for msg in messages
        if not is_summary_request(msg)
    ]

    insert_at = 0
    if retained_messages and isinstance(retained_messages[0], ModelRequest):
        insert_at = 1

    return retained_messages[:insert_at] + [summary_request] + retained_messages[insert_at:]


def build_history_processors(settings: Settings) -> Sequence:
    del settings
    return [keep_recent_messages, inject_summary_if_needed]
