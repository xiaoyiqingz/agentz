"""
天气相关工具

提供天气查询功能的工具函数，供 Agent 使用。
"""

from pydantic_ai import RunContext
from typing import Any
from urllib.parse import quote
import httpx


async def get_weather(ctx: RunContext[Any], city: str) -> str:
    """
    获取指定城市的天气信息

    Args:
        ctx: Agent 运行上下文，包含依赖项（如 HTTP 客户端）
        city: 城市名称（支持中文）

    Returns:
        str: 天气信息字符串，如果请求超时则返回提示信息
    """
    # 对城市名进行 URL 编码，确保中文字符能正确传输
    encoded_city = quote(city)
    # 使用 httpx 的 params 参数，让 httpx 自动处理查询参数的编码
    url = f"http://wttr.in/{encoded_city}"
    try:
        print(f"获取 {city} 的天气信息 (URL: {url})")
        response = await ctx.deps.client.get(url, params={"format": "3"})
        return response.text
    except httpx.ReadTimeout:
        # 请求超时，返回友好提示而不是抛出异常
        return f"抱歉，获取 {city} 的天气信息时请求超时。请稍后重试，或者检查网络连接是否正常。"
    except httpx.RequestError as e:
        # 其他网络请求错误
        return f"抱歉，获取 {city} 的天气信息时发生网络错误：{str(e)}。请稍后重试。"
    except Exception as e:
        # 其他未知错误
        return f"抱歉，获取 {city} 的天气信息时发生错误：{str(e)}。请稍后重试。"
