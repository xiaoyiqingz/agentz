"""Local weather tool."""

from urllib.parse import quote

import httpx
from pydantic_ai import FunctionToolset, ModelRetry, RunContext
from pydantic_ai.tools import Tool

from core.context.deps import Deps


async def get_weather(ctx: RunContext[Deps], city: str) -> str:
    """Get the current weather for ``city`` using the shared HTTP client."""
    url = f"http://wttr.in/{quote(city)}"
    try:
        response = await ctx.deps.client.get(url, params={"format": "3"})
        return response.text
    except httpx.ReadTimeout as exc:
        request_url = getattr(exc.request, "url", url) if hasattr(exc, "request") else url
        raise ModelRetry(
            f"获取 {city} 的天气信息时请求超时（URL: {request_url}，错误: {exc}），"
            f"正在重试（当前重试次数：{ctx.retry}）"
        ) from exc
    except httpx.RequestError as exc:
        return f"抱歉，获取 {city} 的天气信息时发生网络错误：{exc}。请稍后重试。"
    except Exception as exc:
        return f"抱歉，获取 {city} 的天气信息时发生错误：{exc}。请稍后重试。"


def build_weather_toolset() -> FunctionToolset:
    """Build the local weather toolset with bounded retries."""
    return FunctionToolset(
        tools=[Tool(get_weather, max_retries=2)],
        instructions="Use this tool only for the current weather.",
    )
