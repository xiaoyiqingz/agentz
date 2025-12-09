"""
任务路由器

负责根据计划将任务分发到对应的专门化 Agent，并收集执行结果。
"""

from typing import List, Optional
from dataclasses import dataclass

from models.planning import Plan, SubTask, AgentEnum
from planning.specialized_agents import get_agent_by_type, Deps
from planning.context_helper import format_history_for_context_agent


@dataclass
class TaskResult:
    """子任务执行结果"""

    task: SubTask  # 子任务
    result: str  # 执行结果
    agent_type: AgentEnum  # 使用的 Agent 类型
    success: bool  # 是否成功
    error: Optional[str] = None  # 错误信息（如果失败）


class TaskRouter:
    """任务路由器，负责将任务分发到对应的 Agent"""

    def __init__(self):
        """初始化任务路由器"""
        pass

    async def execute_plan(
        self, plan: Plan, deps: Deps, execute_parallel: bool = False
    ) -> List[TaskResult]:
        """
        执行计划

        Args:
            plan: 任务计划
            deps: Agent 依赖项
            execute_parallel: 是否并行执行（第一阶段暂不支持，保留接口）

        Returns:
            List[TaskResult]: 子任务执行结果列表
        """
        # 如果是问候语，不需要执行子任务
        if plan.is_greeting:
            return []

        # 如果没有子任务，返回空列表
        if not plan.subtasks:
            return []

        # 按优先级和依赖关系排序任务
        sorted_tasks = self._sort_tasks(plan.subtasks)

        results: List[TaskResult] = []

        # 串行执行任务（第一阶段先实现串行）
        for task in sorted_tasks:
            try:
                # 获取对应的 Agent
                agent = get_agent_by_type(task.assigned_agent)

                # 如果是 Context Agent，需要格式化历史记录并添加到任务描述中
                if task.assigned_agent == AgentEnum.CONTEXT_AGENT:
                    # 格式化历史记录
                    history_text = format_history_for_context_agent(
                        deps.message_history
                    )
                    # 将历史记录添加到任务描述中
                    enhanced_task = (
                        f"{task.task_details}\n\n对话历史记录：\n{history_text}"
                    )
                    agent_result = await agent.run(enhanced_task, deps=deps)
                else:
                    # 其他 Agent 正常执行
                    agent_result = await agent.run(task.task_details, deps=deps)

                # 收集结果
                results.append(
                    TaskResult(
                        task=task,
                        result=agent_result.output,
                        agent_type=task.assigned_agent,
                        success=True,
                    )
                )
            except Exception as e:
                # 任务执行失败，记录错误但继续执行其他任务
                error_msg = f"执行任务失败: {str(e)}"
                results.append(
                    TaskResult(
                        task=task,
                        result="",
                        agent_type=task.assigned_agent,
                        success=False,
                        error=error_msg,
                    )
                )

        return results

    def _sort_tasks(self, tasks: List[SubTask]) -> List[SubTask]:
        """
        根据依赖关系和优先级排序任务

        第一阶段实现简单排序：
        1. 先按优先级排序（数字越大优先级越高）
        2. 如果优先级相同，按依赖关系排序（无依赖的优先）

        后续可以升级为拓扑排序，正确处理复杂的依赖关系。

        Args:
            tasks: 子任务列表

        Returns:
            List[SubTask]: 排序后的子任务列表
        """
        # 简单排序：先按优先级降序，再按依赖数量升序
        sorted_tasks = sorted(
            tasks,
            key=lambda t: (-t.priority, len(t.dependencies)),
        )

        # TODO: 后续可以实现拓扑排序，正确处理依赖关系
        # 例如：如果任务 A 依赖任务 B，确保 B 在 A 之前执行

        return sorted_tasks
