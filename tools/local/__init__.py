"""Locally implemented Pydantic AI toolsets."""

from typing import Any

from config.settings import Settings
from tools.local.project_review import build_project_review_toolset
from tools.local.time import build_time_toolset
from tools.local.weather import build_weather_toolset
from tools.local.web_search import build_web_search_toolset


def build_local_toolsets(settings: Settings) -> list[Any]:
    """Build the explicitly enabled toolsets implemented by this application."""
    return [
        build_time_toolset(),
        build_weather_toolset(),
        build_project_review_toolset(),
        build_web_search_toolset(settings),
    ]
