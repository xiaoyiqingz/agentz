from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.deepseek import DeepSeekProvider

from config import Settings


def build_deepseek_model(settings: Settings) -> OpenAIChatModel:
    return OpenAIChatModel(
        settings.models.deepseek.model_name,
        provider=DeepSeekProvider(api_key=settings.models.deepseek.api_key),
    )
