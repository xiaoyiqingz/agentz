import asyncio
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from pydantic_ai.run import AgentRunResultEvent

from core.server import AgentSession, stream_session_turn


class _StreamContext:
    def __init__(self, events):
        self.events = events

    async def __aenter__(self):
        async def stream():
            for event in self.events:
                yield event

        return stream()

    async def __aexit__(self, exc_type, exc_value, traceback):
        return False


class TestServer(unittest.TestCase):
    def test_stream_session_turn_persists_history_without_cli_dependencies(self):
        messages = [SimpleNamespace(role="assistant")]
        run_result = Mock()
        run_result.all_messages.return_value = messages
        agent = Mock()
        agent.run_stream_events.return_value = _StreamContext(
            [AgentRunResultEvent(result=run_result)]
        )
        session_store = Mock()
        runtime = SimpleNamespace(
            project_path=Path("/project"),
            conversation_id="conversation-1",
            session_store=session_store,
            ignored_cli_project_path=False,
        )
        session = AgentSession(
            runtime=runtime,
            agent=agent,
            deps=SimpleNamespace(session_id="session-1"),
            all_messages=[],
        )

        async def consume():
            return [event async for event in stream_session_turn(session, "hello")]

        events = asyncio.run(consume())

        self.assertEqual(len(events), 1)
        self.assertEqual(session.all_messages, messages)
        session_store.save_message_history.assert_called_once_with(messages)
        agent.run_stream_events.assert_called_once_with(
            "hello",
            deps=session.deps,
            message_history=[],
            conversation_id="conversation-1",
            metadata={"session_id": "session-1", "project_path": "/project"},
        )


if __name__ == "__main__":
    unittest.main()
