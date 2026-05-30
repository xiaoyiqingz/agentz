import unittest

from config.settings import load_settings
from models.mimo import build_mimo_model


class TestMimoModel(unittest.TestCase):
    def test_build_mimo_model_uses_configured_model_name(self):
        settings = load_settings(
            {
                "MIMO_BASE_URL": "https://example.test/v1",
                "MIMO_API_KEY": "test-key",
                "MIMO_MODEL_NAME": "mimo-test",
                "SKILLS_DIR": "./.agents/skills",
                "MCP_CONFIG_PATH": "./mcp.json",
            }
        )

        model = build_mimo_model(settings)

        self.assertEqual(model.model_name, "mimo-test")
