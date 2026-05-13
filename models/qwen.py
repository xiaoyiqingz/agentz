from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from config import Settings


def build_qwen_model(settings: Settings) -> OpenAIChatModel:
    return OpenAIChatModel(
        settings.qwen_model_name,
        provider=OpenAIProvider(
            base_url=settings.qwen_base_url, api_key=settings.qwen_api_key
        ),
    )
