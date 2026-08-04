import unittest

from pydantic_ai.messages import ModelRequest, SystemPromptPart, UserPromptPart

from core.server import _strip_legacy_system_prompts


class TestInstructionMigration(unittest.TestCase):
    def test_removes_legacy_system_prompt_and_keeps_user_context(self):
        messages = [
            ModelRequest(
                parts=[
                    SystemPromptPart(content="legacy static prompt"),
                    UserPromptPart(content="保留这个问题"),
                ]
            )
        ]

        migrated, changed = _strip_legacy_system_prompts(messages)

        self.assertTrue(changed)
        self.assertEqual(len(migrated), 1)
        self.assertEqual(len(migrated[0].parts), 1)
        self.assertIsInstance(migrated[0].parts[0], UserPromptPart)
        self.assertEqual(migrated[0].parts[0].content, "保留这个问题")

    def test_keeps_messages_without_legacy_system_prompt(self):
        messages = [ModelRequest(parts=[UserPromptPart(content="问题")])]

        migrated, changed = _strip_legacy_system_prompts(messages)

        self.assertFalse(changed)
        self.assertEqual(migrated, messages)


if __name__ == "__main__":
    unittest.main()
