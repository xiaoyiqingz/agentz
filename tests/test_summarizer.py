import asyncio
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart

from config import load_settings
from context.deps import Deps
from context.models import ConversationSummary
from context.session_store import SessionStore
from context.summarizer import (
    build_summary_prompt,
    flatten_turns,
    maybe_refresh_summary,
    render_messages_for_summary,
    select_turns_for_summary,
)


class FakeSummarizer:
    def __init__(self, output: str):
        self.output = output
        self.calls: list[tuple[str, dict]] = []

    async def run(self, user_prompt: str, **kwargs):
        self.calls.append((user_prompt, kwargs))
        return SimpleNamespace(output=self.output)


class TestSummarizer(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name)
        self.session_store = SessionStore(self.config_path, session_id="session-1")
        self.settings = load_settings(
            {
                "SKILLS_DIR": "./.agents/skills",
                "MCP_CONFIG_PATH": "./mcp.json",
                "CONTEXT_KEEP_RECENT_TURNS": "2",
                "CONTEXT_SUMMARY_TRIGGER_TURNS": "4",
                "CONTEXT_SUMMARY_MAX_TURNS": "3",
                "CONTEXT_ENABLE_SUMMARY": "true",
            }
        )
        self.deps = Deps(
            client=None,  # type: ignore[arg-type]
            session_id="session-1",
            conversation_id="conversation-1",
            config_path=self.config_path,
            project_path=self.config_path,
            settings=self.settings,
            session_store=self.session_store,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _messages(self, total: int):
        messages = []
        for index in range(total):
            messages.append(
                ModelRequest(parts=[UserPromptPart(content=f"user-{index}")])
            )
            messages.append(
                ModelResponse(parts=[TextPart(content=f"assistant-{index}")])
            )
        return messages

    def test_select_turns_for_summary_excludes_recent_tail(self):
        selected = select_turns_for_summary(
            self._messages(4),
            keep_recent_turns=2,
            max_turns=10,
        )
        self.assertEqual(len(selected), 2)
        flattened = flatten_turns(selected)
        self.assertEqual(len(flattened), 4)
        self.assertEqual(flattened[0].parts[0].content, "user-0")
        self.assertEqual(flattened[-1].parts[0].content, "assistant-1")

    def test_render_messages_for_summary_includes_roles(self):
        rendered = render_messages_for_summary(self._messages(1))
        self.assertIn("1. request:", rendered)
        self.assertIn("2. response:", rendered)

    def test_build_summary_prompt_includes_existing_summary(self):
        prompt = build_summary_prompt(
            self._messages(1),
            existing_summary="Earlier summary.",
        )
        self.assertIn("Earlier summary.", prompt)
        self.assertIn("Return plain text using exactly this template:", prompt)
        self.assertIn("HISTORICAL SUMMARY", prompt)
        self.assertIn("Conversation turns:", prompt)

    def test_maybe_refresh_summary_saves_summary(self):
        summarizer = FakeSummarizer("Condensed summary")
        messages = self._messages(4)

        summary = asyncio.run(maybe_refresh_summary(summarizer, self.deps, messages))

        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertEqual(summary.summary_text, "Condensed summary")
        self.assertEqual(len(summarizer.calls), 1)
        saved = self.session_store.load_summary()
        self.assertIsNotNone(saved)
        assert saved is not None
        self.assertEqual(saved.summary_text, "Condensed summary")

    def test_maybe_refresh_summary_skips_when_existing_summary_is_fresh(self):
        self.session_store.save_summary(
            ConversationSummary(
                session_id="session-1",
                conversation_id="conversation-1",
                summary_text="Existing summary",
                turn_count_at_summary=6,
            )
        )
        summarizer = FakeSummarizer("New summary")
        messages = self._messages(4)

        summary = asyncio.run(maybe_refresh_summary(summarizer, self.deps, messages))

        self.assertIsNotNone(summary)
        self.assertEqual(summary.summary_text, "Existing summary")
        self.assertEqual(len(summarizer.calls), 0)
