"""Local web-search tools backed by configured providers."""

from pydantic_ai import FunctionToolset
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
from pydantic_ai.common_tools.tavily import tavily_search_tool

from config.settings import Settings


def get_tavily_search_tool(settings: Settings) -> object | None:
    """Return Tavily search when an API key is configured."""
    if not settings.tavily_api_key:
        return None
    return tavily_search_tool(settings.tavily_api_key)


def get_duckduckgo_search_tool() -> object:
    """Return the no-key-required DuckDuckGo search tool."""
    return duckduckgo_search_tool()


def build_web_search_toolset(settings: Settings) -> FunctionToolset:
    """Build the web-search tools enabled by application configuration."""
    tools: list[object] = [get_duckduckgo_search_tool()]
    if tavily_tool := get_tavily_search_tool(settings):
        tools.append(tavily_tool)

    return FunctionToolset(
        tools=tools,
        instructions="Use web search when current external information is needed.",
    )
