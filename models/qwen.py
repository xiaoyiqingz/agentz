from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
import os

load_dotenv()

model_qwen = OpenAIChatModel(
    os.getenv("QWEN_MODEL_NAME", "qwen3-coder-plus"),
    provider=OpenAIProvider(
        base_url=os.getenv("QWEN_BASE_URL"), api_key=os.getenv("QWEN_API_KEY")
    ),
)

if __name__ == "__main__":
    qwen_agent = Agent(model_qwen)
    result = qwen_agent.run_sync("你好, 你是什么模型")
    print(result)
