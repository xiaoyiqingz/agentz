"""共享的 Agent 会话执行服务。

本模块不依赖终端、HTTP 或 Web UI。不同交互入口只需打开一个会话，
消费 ``stream_session_turn`` 产生的 Pydantic AI 事件，并按各自协议渲染。
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from httpx import AsyncClient
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelRequest, SystemPromptPart
from pydantic_ai.run import AgentRunResultEvent
from pydantic_ai_harness.planning import Planning

from config.settings import Settings
from infra.observability import configure_observability, instrument_http_client
from models.deepseek import build_deepseek_model
from prompts.prompt import get_smart_assistant_prompt
from tools.register import build_agent_tools

from .context.compaction import build_compaction
from .context.deps import Deps
from .context.session_runtime import SessionRuntime, initialize_session_runtime
from .readonly_filesystem import build_project_filesystem


def create_agent(settings: Settings, project_path: Path) -> Agent:
    """Build the Agent configured for one session's bound project."""
    registered_tools = build_agent_tools(settings)

    capabilities = [
        build_compaction(settings),
        build_project_filesystem(project_path),
    ]
    if settings.planning_enabled:
        capabilities.append(Planning(cache_ttl=settings.planning_cache_ttl))

    agent_kwargs = {
        "model": build_deepseek_model(settings),
        "deps_type": Deps,
        "instructions": get_smart_assistant_prompt(),
        "capabilities": capabilities,
    }
    if registered_tools.toolsets:
        agent_kwargs["toolsets"] = registered_tools.toolsets

    return Agent(**agent_kwargs)


@dataclass
class AgentSession:
    """Resources and state shared by every turn in one open session."""

    runtime: SessionRuntime
    agent: Agent
    deps: Deps
    all_messages: list[ModelMessage]

    @property
    def session_id(self) -> str:
        return self.deps.session_id

    @property
    def project_path(self) -> Path:
        return self.runtime.project_path

    @property
    def ignored_requested_project_path(self) -> bool:
        return self.runtime.ignored_cli_project_path

    def save_history(self) -> None:
        """Persist the latest successfully completed history."""
        self.runtime.session_store.save_message_history(self.all_messages)


@asynccontextmanager
async def open_agent_session(
    settings: Settings,
    session_id: str,
    requested_project_path: str | None = None,
) -> AsyncIterator[AgentSession]:
    """Open a session without assuming how its events will be presented."""
    configure_observability(settings)
    runtime = initialize_session_runtime(
        agentz_home=settings.agentz_home,
        session_id=session_id,
        requested_project_path=requested_project_path,
    )
    all_messages, migrated = _strip_legacy_system_prompts(runtime.all_messages)
    if migrated:
        runtime.session_store.save_message_history(all_messages)
    agent = create_agent(settings, runtime.project_path)

    async with AsyncClient() as client:
        instrument_http_client(client, settings)
        deps = Deps(
            client=client,
            session_id=session_id,
            conversation_id=runtime.conversation_id,
            agentz_home=settings.agentz_home,
            project_path=runtime.project_path,
            settings=settings,
            session_store=runtime.session_store,
        )
        yield AgentSession(
            runtime=runtime,
            agent=agent,
            deps=deps,
            all_messages=all_messages,
        )


async def stream_session_turn(
    session: AgentSession,
    user_input: str,
) -> AsyncIterator[Any]:
    """Run and persist one turn, yielding provider-independent stream events.

    Consumers may format these events for a terminal, encode them as SSE, or
    turn them into a non-streaming API response. History is written only after
    the stream completes successfully.
    """
    run_result = None
    async with session.agent.run_stream_events(
        user_input,
        deps=session.deps,
        message_history=session.all_messages,
        conversation_id=session.runtime.conversation_id,
        metadata={
            "session_id": session.session_id,
            "project_path": str(session.project_path),
        },
    ) as stream:
        async for event in stream:
            if isinstance(event, AgentRunResultEvent):
                run_result = event.result
            yield event

    if run_result is None:
        raise RuntimeError("Agent 流式运行未返回最终结果")

    session.all_messages = run_result.all_messages()
    session.save_history()


def _strip_legacy_system_prompts(
    messages: list[ModelMessage],
) -> tuple[list[ModelMessage], bool]:
    """Remove static prompts persisted before AgentZ switched to instructions.

    AgentZ historically had one static ``system_prompt``. Its content is now
    supplied by the current agent as ``instructions``, so retaining those old
    parts would defeat the new history semantics and waste context tokens.
    """
    migrated_messages: list[ModelMessage] = []
    changed = False

    for message in messages:
        if not isinstance(message, ModelRequest):
            migrated_messages.append(message)
            continue

        parts = [
            part for part in message.parts if not isinstance(part, SystemPromptPart)
        ]
        if len(parts) == len(message.parts):
            migrated_messages.append(message)
            continue

        changed = True
        if parts:
            migrated_messages.append(replace(message, parts=parts))

    return migrated_messages, changed
