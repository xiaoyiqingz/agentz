import os
import unittest
from unittest.mock import patch

from config.settings import load_settings
from infra.observability import (
    _build_langfuse_auth_header,
    _build_langfuse_otlp_endpoint,
    configure_observability,
)


class TestObservability(unittest.TestCase):
    def test_build_langfuse_otlp_endpoint(self):
        self.assertEqual(
            _build_langfuse_otlp_endpoint("https://cloud.langfuse.com/"),
            "https://cloud.langfuse.com/api/public/otel",
        )

    def test_build_langfuse_auth_header(self):
        self.assertEqual(
            _build_langfuse_auth_header("pk-lf-test", "sk-lf-test"),
            "cGstbGYtdGVzdDpzay1sZi10ZXN0",
        )

    @patch("infra.observability.logfire.instrument_pydantic_ai")
    @patch("infra.observability.logfire.configure")
    def test_configure_observability_uses_logfire_backend(
        self,
        configure_mock,
        instrument_mock,
    ):
        settings = load_settings(
            {
                "OBS_BACKEND": "logfire",
                "SKILLS_DIR": "./.agents/skills",
                "MCP_CONFIG_PATH": "./mcp.json",
            }
        )

        configure_observability(settings)

        configure_mock.assert_called_once_with()
        instrument_mock.assert_called_once_with()

    @patch("infra.observability.logfire.instrument_pydantic_ai")
    @patch("infra.observability.logfire.configure")
    def test_configure_observability_uses_langfuse_backend(
        self,
        configure_mock,
        instrument_mock,
    ):
        settings = load_settings(
            {
                "OBS_BACKEND": "langfuse",
                "LANGFUSE_BASE_URL": "https://us.cloud.langfuse.com",
                "LANGFUSE_PUBLIC_KEY": "pk-lf-test",
                "LANGFUSE_SECRET_KEY": "sk-lf-test",
                "SKILLS_DIR": "./.agents/skills",
                "MCP_CONFIG_PATH": "./mcp.json",
            }
        )

        previous = {
            "OTEL_EXPORTER_OTLP_ENDPOINT": os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"),
            "OTEL_EXPORTER_OTLP_HEADERS": os.environ.get("OTEL_EXPORTER_OTLP_HEADERS"),
            "OTEL_EXPORTER_OTLP_TRACES_HEADERS": os.environ.get(
                "OTEL_EXPORTER_OTLP_TRACES_HEADERS"
            ),
        }

        try:
            configure_observability(settings)

            configure_mock.assert_called_once_with(send_to_logfire=False)
            instrument_mock.assert_called_once_with()
            self.assertEqual(
                os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"],
                "https://us.cloud.langfuse.com/api/public/otel",
            )
            self.assertIn(
                "Authorization=Basic cGstbGYtdGVzdDpzay1sZi10ZXN0",
                os.environ["OTEL_EXPORTER_OTLP_HEADERS"],
            )
            self.assertIn(
                "x-langfuse-ingestion-version=4",
                os.environ["OTEL_EXPORTER_OTLP_HEADERS"],
            )
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_configure_observability_requires_langfuse_keys(self):
        settings = load_settings(
            {
                "OBS_BACKEND": "langfuse",
                "SKILLS_DIR": "./.agents/skills",
                "MCP_CONFIG_PATH": "./mcp.json",
            }
        )

        with self.assertRaisesRegex(ValueError, "LANGFUSE_PUBLIC_KEY"):
            configure_observability(settings)
