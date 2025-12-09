"""
Planner Agent

负责任务分解和规划，生成结构化的任务计划。
"""

from typing import Optional, List
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
from dataclasses import dataclass
from httpx import AsyncClient

from models.qwen import model_qwen
from models.planning import Plan
from prompts.planning_prompts import get_planner_prompt


@dataclass
class PlannerDeps:
    """
    Planner Agent 的依赖项

    注意：Planner Agent 主要负责生成计划，通常不需要额外的依赖。
    但为了保持一致性，保留此结构，以便后续扩展。
    """

    client: AsyncClient  # HTTP 客户端（虽然 Planner 可能不需要，但保持一致性）


# 延迟初始化：在首次使用时创建 Planner Agent 实例
_planner_agent: Optional[Agent] = None


def _create_planner_agent() -> Agent:
    """
    创建 Planner Agent 实例

    Planner Agent 负责：
    1. 分析用户请求，理解主任务
    2. 将复杂任务分解为可管理的子任务
    3. 为每个子任务分配合适的专门化 Agent
    """
    return Agent(
        model=model_qwen,
        deps_type=PlannerDeps,
        output_type=Plan,  # 结构化输出：返回 Plan 对象
        system_prompt=get_planner_prompt(),
    )


def get_planner_agent() -> Agent:
    """
    获取 Planner Agent 实例（延迟初始化）

    Returns:
        Agent: Planner Agent 实例
    """
    global _planner_agent
    if _planner_agent is None:
        _planner_agent = _create_planner_agent()
    return _planner_agent


async def create_plan(
    user_input: str,
    deps: PlannerDeps,
    message_history: Optional[List[ModelMessage]] = None,
) -> tuple[Plan, object]:
    """
    根据用户输入生成任务计划

    Args:
        user_input: 用户输入/请求
        deps: Planner Agent 的依赖项
        message_history: 历史消息记录（用于保持对话上下文）

    Returns:
        tuple[Plan, object]: (生成的任务计划, planner_result)
        - Plan: 结构化的计划对象
        - planner_result: Planner Agent 的执行结果，包含 new_messages() 方法

    Raises:
        Exception: 如果 Planner Agent 执行失败或返回无效的计划
    """
    planner = get_planner_agent()

    # 调用 Planner Agent 生成计划（传入历史消息）
    result = await planner.run(
        user_input, deps=deps, message_history=message_history or []
    )

    # 返回结构化的计划（Pydantic 会自动验证）和 result 对象
    return result.output, result
