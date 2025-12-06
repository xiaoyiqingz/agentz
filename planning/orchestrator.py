"""
主协调器

统一管理整个 Planning Design 流程：
1. 调用 Planner 生成计划
2. 调用 Router 执行计划
3. 调用 Aggregator 汇总结果
"""

from typing import Optional
from httpx import AsyncClient

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
    ) -> str:
        """
        执行用户请求（支持迭代规划）

        Args:
            user_input: 用户输入/请求
            deps: Agent 依赖项（包含 HTTP 客户端等）
            max_iterations: 最大迭代次数（第一阶段默认为 1，不迭代）

        Returns:
            str: 最终响应
        """
        iteration = 0
        previous_plan: Optional[Plan] = None

        # 创建 Planner 的依赖（需要 AsyncClient）
        planner_deps = PlannerDeps(client=deps.client)

        while iteration < max_iterations:
            iteration += 1

            try:
                # 1. 生成计划
                plan = await create_plan(user_input, deps=planner_deps)

                # 2. 如果是问候语，直接处理
                if plan.is_greeting:
                    return await self._handle_greeting(plan, deps)

                # 3. 执行计划
                task_results = await self.router.execute_plan(plan, deps=deps)

                # 4. 汇总结果
                final_result = self.aggregator.aggregate(plan.main_task, task_results)

                # 5. 检查是否需要迭代
                if not plan.requires_iteration or iteration >= max_iterations:
                    return final_result

                # 如果需要迭代，将当前结果作为上下文，重新规划
                user_input = (
                    f"{user_input}\n\n"
                    f"当前执行结果：{final_result}\n"
                    f"请根据结果调整计划。"
                )
                previous_plan = plan

            except Exception as e:
                # 如果执行过程中出现错误，返回错误信息
                error_msg = f"执行 Planning 流程时发生错误：{str(e)}"
                return error_msg

        # 达到最大迭代次数，返回最后一次的结果
        # （实际上如果到这里，说明最后一次迭代已经返回了结果）
        return "执行完成"

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
