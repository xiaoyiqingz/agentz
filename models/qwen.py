from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from config import Settings


def build_qwen_model(settings: Settings) -> OpenAIChatModel:
    return OpenAIChatModel(
        settings.models.qwen.model_name,
        provider=OpenAIProvider(
            base_url=settings.models.qwen.base_url,
            api_key=settings.models.qwen.api_key,
        ),
    )
