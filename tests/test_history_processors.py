import asyncio
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)

from config import load_settings
from context.deps import Deps
from context.history_processors import (
    SUMMARY_METADATA_KEY,
    inject_summary_if_needed,
    keep_recent_messages,
)
from context.models import ConversationSummary
from context.session_store import SessionStore


class TestHistoryProcessors(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name)
        self.session_store = SessionStore(self.config_path, session_id="session-1")
        self.settings = load_settings(
            {
                "CONTEXT_KEEP_RECENT_TURNS": "2",
                "SKILLS_DIR": "./.agents/skills",
                "MCP_CONFIG_PATH": "./mcp.json",
            }
        )
        self.deps = Deps(
            client=None,  # type: ignore[arg-type]
            session_id="session-1",
            conversation_id="conversation-1",
            config_path=self.config_path,
            settings=self.settings,
            session_store=self.session_store,
        )
        self.ctx = SimpleNamespace(deps=self.deps)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_keep_recent_messages_applies_limit(self):
        messages = [
            ModelRequest(parts=[UserPromptPart(content="one")]),
            ModelRequest(parts=[UserPromptPart(content="two")]),
            ModelRequest(parts=[UserPromptPart(content="three")]),
        ]

        kept = asyncio.run(keep_recent_messages(self.ctx, messages))

        self.assertEqual(len(kept), 2)
        self.assertEqual(kept[0].parts[0].content, "two")
        self.assertEqual(kept[1].parts[0].content, "three")

    def test_keep_recent_messages_preserves_whole_turn_with_tool_chain(self):
        messages = [
            ModelRequest(parts=[UserPromptPart(content="turn-1")]),
            ModelResponse(parts=[ToolCallPart(tool_name="search", args={"q": "x"})]),
            ModelRequest(parts=[ToolReturnPart(tool_name="search", content="result")]),
            ModelResponse(parts=[TextPart(content="answer-1")]),
            ModelRequest(parts=[UserPromptPart(content="turn-2")]),
            ModelResponse(parts=[TextPart(content="answer-2")]),
        ]
        self.deps.settings = load_settings(  # type: ignore[misc]
            {
                "CONTEXT_KEEP_RECENT_TURNS": "1",
                "SKILLS_DIR": "./.agents/skills",
                "MCP_CONFIG_PATH": "./mcp.json",
            }
        )

        kept = asyncio.run(keep_recent_messages(self.ctx, messages))

        self.assertEqual(len(kept), 2)
        self.assertEqual(kept[0].parts[0].content, "turn-2")
        self.assertEqual(kept[1].parts[0].content, "answer-2")

    def test_inject_summary_adds_summary_request(self):
        self.session_store.save_summary(
            ConversationSummary(
                session_id="session-1",
                conversation_id="conversation-1",
                summary_text="Summary for prior turns.",
                turn_count_at_summary=3,
            )
        )
        messages = [ModelRequest(parts=[UserPromptPart(content="latest")])]

        processed = asyncio.run(inject_summary_if_needed(self.ctx, messages))

        self.assertEqual(len(processed), 2)
        self.assertTrue(processed[1].metadata[SUMMARY_METADATA_KEY])
        self.assertIn("[HISTORICAL SUMMARY]", processed[1].parts[0].content)
        self.assertIn("Summary for prior turns.", processed[1].parts[0].content)

    def test_inject_summary_replaces_existing_summary_request(self):
        self.session_store.save_summary(
            ConversationSummary(
                session_id="session-1",
                conversation_id="conversation-1",
                summary_text="Fresh summary.",
                turn_count_at_summary=5,
            )
        )
        messages = [
            ModelRequest(parts=[UserPromptPart(content="latest")]),
            ModelRequest(
                parts=[UserPromptPart(content="old summary")],
                metadata={SUMMARY_METADATA_KEY: True},
            ),
        ]

        processed = asyncio.run(inject_summary_if_needed(self.ctx, messages))

        self.assertEqual(len(processed), 2)
        self.assertIn("Fresh summary.", processed[1].parts[0].content)

    def test_keep_recent_messages_treats_leading_tool_continuation_as_turn(self):
        messages = [
            ModelResponse(parts=[ToolCallPart(tool_name="search", args={"q": "x"})]),
            ModelRequest(parts=[ToolReturnPart(tool_name="search", content="result")]),
            ModelResponse(parts=[TextPart(content="continued-answer")]),
            ModelRequest(parts=[UserPromptPart(content="turn-2")]),
            ModelResponse(parts=[TextPart(content="answer-2")]),
        ]
        self.deps.settings = load_settings(  # type: ignore[misc]
            {
                "CONTEXT_KEEP_RECENT_TURNS": "1",
                "SKILLS_DIR": "./.agents/skills",
                "MCP_CONFIG_PATH": "./mcp.json",
            }
        )

        kept = asyncio.run(keep_recent_messages(self.ctx, messages))

        self.assertEqual(len(kept), 2)
        self.assertEqual(kept[0].parts[0].content, "turn-2")
        self.assertEqual(kept[1].parts[0].content, "answer-2")
