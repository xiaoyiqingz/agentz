"""
天气相关工具

提供天气查询功能的工具函数，供 Agent 使用。
"""

from pydantic_ai import RunContext, ModelRetry
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
        str: 天气信息字符串

    Raises:
        ModelRetry: 当请求超时时，抛出此异常以触发 pydantic-ai 的重试机制
    """
    # 对城市名进行 URL 编码，确保中文字符能正确传输
    encoded_city = quote(city)
    # 使用 httpx 的 params 参数，让 httpx 自动处理查询参数的编码
    url = f"http://wttr.in/{encoded_city}"

    try:
        response = await ctx.deps.client.get(url, params={"format": "3"})
        return response.text
    except httpx.ReadTimeout as e:
        # 请求超时，抛出 ModelRetry 以触发 pydantic-ai 的重试机制
        # 重试次数由 Tool(max_retries=2) 控制
        # 从异常中获取错误详情
        error_detail = str(e)
        request_url = getattr(e.request, "url", url) if hasattr(e, "request") else url
        raise ModelRetry(
            f"获取 {city} 的天气信息时请求超时（URL: {request_url}，错误: {error_detail}），正在重试（当前重试次数：{ctx.retry}）"
        )
    except httpx.RequestError as e:
        # 其他网络请求错误，不重试，直接返回错误信息
        return f"抱歉，获取 {city} 的天气信息时发生网络错误：{str(e)}。请稍后重试。"
    except Exception as e:
        # 其他未知错误，不重试，直接返回错误信息
        return f"抱歉，获取 {city} 的天气信息时发生错误：{str(e)}。请稍后重试。"
