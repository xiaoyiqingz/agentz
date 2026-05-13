from functools import lru_cache

from pydantic_ai import Agent

from config import Settings
from models.qwen import build_qwen_model
from prompts.prompt import get_coder_prompt


@lru_cache(maxsize=8)
def create_coder_agent(settings: Settings) -> Agent:
    return Agent(
        model=build_qwen_model(settings),
        system_prompt=get_coder_prompt(),
    )


async def modify(
    settings: Settings, prompt: str, file_path: str, begin_line: int = 1
) -> str:
    prompt = f"这段代码是从文件{file_path}中低{begin_line}行开始读取的, 请帮我查看一下这段代买是否有错误, 如果有请修改, 并给出修改后的代码: {prompt}"
    result = await create_coder_agent(settings).run(prompt)
    return result.output


async def generate(settings: Settings, prompt: str) -> str:
    result = await create_coder_agent(settings).run(prompt)
    return result.output
