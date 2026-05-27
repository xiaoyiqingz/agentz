from pydantic_ai.models.openai import OpenAIChatModel, OpenAIResponsesModelSettings
from pydantic_ai.providers.ollama import OllamaProvider

from config import Settings


def build_ollama_qwen_model(settings: Settings) -> OpenAIChatModel:
    return OpenAIChatModel(
        settings.models.ollama.model_qwen,
        provider=OllamaProvider(base_url=settings.models.ollama.base_url),
    )

settings = OpenAIResponsesModelSettings(
    openai_reasoning_effort="low",
    openai_reasoning_summary="detailed",
)
