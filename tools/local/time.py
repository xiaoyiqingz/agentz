"""Local time tool."""

from datetime import datetime

from pydantic_ai import FunctionToolset


def get_current_time() -> str:
    """Return the current local time as ``YYYY-MM-DD HH:MM:SS``."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def build_time_toolset() -> FunctionToolset:
    """Build the local time toolset."""
    return FunctionToolset(tools=[get_current_time])
