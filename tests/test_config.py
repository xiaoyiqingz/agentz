import unittest

from config import load_settings


class TestConfig(unittest.TestCase):
    def test_load_settings_includes_mimo_defaults(self):
        settings = load_settings(
            {
                "SKILLS_DIR": "./.agents/skills",
                "MCP_CONFIG_PATH": "./mcp.json",
            }
        )

        self.assertEqual(
            settings.models.mimo.base_url,
            "https://api.xiaomimimo.com/v1",
        )
        self.assertIsNone(settings.models.mimo.api_key)
        self.assertEqual(settings.models.mimo.model_name, "mimo-v2.5-pro")

    def test_load_settings_accepts_mimo_overrides(self):
        settings = load_settings(
            {
                "MIMO_BASE_URL": "https://example.test/v1",
                "MIMO_API_KEY": "test-key",
                "MIMO_MODEL_NAME": "mimo-test",
                "SKILLS_DIR": "./.agents/skills",
                "MCP_CONFIG_PATH": "./mcp.json",
            }
        )

        self.assertEqual(settings.models.mimo.base_url, "https://example.test/v1")
        self.assertEqual(settings.models.mimo.api_key, "test-key")
        self.assertEqual(settings.models.mimo.model_name, "mimo-test")
