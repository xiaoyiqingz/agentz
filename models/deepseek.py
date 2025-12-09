from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.deepseek import DeepSeekProvider
from pydantic_ai import Agent
import os
from dotenv import load_dotenv

load_dotenv()

model_deepseek = OpenAIChatModel(
    os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat"),
    provider=DeepSeekProvider(api_key=os.getenv("DEEPSEEK_API_KEY")),
)

if __name__ == "__main__":
    deepseek_agent = Agent(model_deepseek)
    result = deepseek_agent.run_sync("你好, 你是什么模型")
    print(result)
