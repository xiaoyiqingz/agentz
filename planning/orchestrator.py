"""
主协调器

统一管理整个 Planning Design 流程：
1. 调用 Planner 生成计划
2. 调用 Router 执行计划
3. 调用 Aggregator 汇总结果
"""

from typing import Optional, List
from httpx import AsyncClient
from pydantic_ai.messages import ModelMessage

from models.planning import Plan
from planning.planner import create_plan, PlannerDeps
from planning.router import TaskRouter, TaskResult
from planning.aggregator import ResultAggregator
from planning.specialized_agents import Deps, get_general_agent


class PlanningOrchestrator:
    """Planning Design 模式的主协调器"""

    def __init__(self):
        """初始化主协调器"""
        self.router = TaskRouter()
        self.aggregator = ResultAggregator()

    async def execute(
        self,
        user_input: str,
        deps: Deps,
        max_iterations: int = 1,
        message_history: Optional[List[ModelMessage]] = None,
    ) -> tuple[str, object]:
        """
        执行用户请求（支持迭代规划）

        Args:
            user_input: 用户输入/请求
            deps: Agent 依赖项（包含 HTTP 客户端等）
            max_iterations: 最大迭代次数（第一阶段默认为 1，不迭代）
            message_history: 历史消息记录（用于保持对话上下文）

        Returns:
            tuple[str, object]: (最终响应, planner_result)
            - str: 最终响应文本
            - planner_result: Planner Agent 的执行结果，包含 new_messages() 方法
        """
        iteration = 0
        previous_plan: Optional[Plan] = None
        planner_result = None

        # 创建 Planner 的依赖（需要 AsyncClient）
        planner_deps = PlannerDeps(client=deps.client)

        while iteration < max_iterations:
            iteration += 1

            try:
                # 1. 生成计划（传入历史消息）
                plan, planner_result = await create_plan(
                    user_input, deps=planner_deps, message_history=message_history
                )

                # 2. 如果是问候语，直接处理
                if plan.is_greeting:
                    greeting_result = await self._handle_greeting(plan, deps)
                    return greeting_result, planner_result

                # 3. 执行计划
                task_results = await self.router.execute_plan(plan, deps=deps)

                # 4. 汇总结果
                final_result = self.aggregator.aggregate(plan.main_task, task_results)

                # 5. 检查是否需要迭代
                if not plan.requires_iteration or iteration >= max_iterations:
                    return final_result, planner_result

                # 如果需要迭代，将当前结果作为上下文，重新规划
                # 注意：迭代时也需要更新历史消息
                user_input = (
                    f"{user_input}\n\n"
                    f"当前执行结果：{final_result}\n"
                    f"请根据结果调整计划。"
                )
                previous_plan = plan

            except Exception as e:
                # 如果执行过程中出现错误，返回错误信息
                error_msg = f"执行 Planning 流程时发生错误：{str(e)}"
                # 如果 planner_result 存在，返回它；否则返回 None
                return error_msg, planner_result if planner_result else None

        # 达到最大迭代次数，返回最后一次的结果
        # （实际上如果到这里，说明最后一次迭代已经返回了结果）
        return "执行完成", planner_result if planner_result else None

    async def _handle_greeting(self, plan: Plan, deps: Deps) -> str:
        """
        处理问候语

        Args:
            plan: 计划对象（包含主任务）
            deps: Agent 依赖项

        Returns:
            str: 问候语响应
        """
        # 使用通用 Agent 处理问候语
        general_agent = get_general_agent()
        result = await general_agent.run(plan.main_task, deps=deps)
        return result.output
