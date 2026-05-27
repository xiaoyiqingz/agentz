from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from config import Settings


def build_mimo_model(settings: Settings) -> OpenAIChatModel:
    # MiMo thinking mode with tool calls requires preserving reasoning_content
    # across turns. Keep that in mind before wiring this into a tool-using agent.
    return OpenAIChatModel(
        settings.models.mimo.model_name,
        provider=OpenAIProvider(
            base_url=settings.models.mimo.base_url,
            api_key=settings.models.mimo.api_key,
        ),
    )
