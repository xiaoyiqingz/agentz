"""
任务路由器

负责根据计划将任务分发到对应的专门化 Agent，并收集执行结果。
"""

from typing import List, Optional, Dict
from dataclasses import dataclass
from collections import deque

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

        # 使用拓扑排序确保依赖任务先执行
        sorted_tasks = self._topological_sort(plan.subtasks)

        # 创建结果映射：{task_index: TaskResult}
        # 用于存储每个任务的执行结果，供后续任务使用
        results_map: Dict[int, TaskResult] = {}
        results: List[TaskResult] = []

        # 串行执行任务（按拓扑排序后的顺序）
        for task in sorted_tasks:
            try:
                # 获取对应的 Agent
                agent = get_agent_by_type(task.assigned_agent)

                # 获取当前任务在原始列表中的索引
                task_index = plan.subtasks.index(task)

                # 收集依赖任务的结果
                dependency_results = self._get_dependency_results(
                    task, task_index, results_map, plan.subtasks
                )

                # 增强任务描述（包含依赖任务的结果）
                enhanced_task = self._enhance_task_with_dependencies(
                    task, dependency_results
                )

                # 如果是 Context Agent，还需要格式化历史记录并添加到任务描述中
                if task.assigned_agent == AgentEnum.CONTEXT_AGENT:
                    history_text = format_history_for_context_agent(
                        deps.message_history
                    )
                    enhanced_task = f"{enhanced_task}\n\n对话历史记录：\n{history_text}"

                # 执行任务
                agent_result = await agent.run(enhanced_task, deps=deps)

                # 创建任务结果
                task_result = TaskResult(
                    task=task,
                    result=agent_result.output,
                    agent_type=task.assigned_agent,
                    success=True,
                )

                # 保存结果（供后续依赖任务使用）
                results_map[task_index] = task_result
                results.append(task_result)

            except Exception as e:
                # 任务执行失败，记录错误但继续执行其他任务
                error_msg = f"执行任务失败: {str(e)}"
                task_result = TaskResult(
                    task=task,
                    result="",
                    agent_type=task.assigned_agent,
                    success=False,
                    error=error_msg,
                )
                # 即使失败也保存结果，避免后续任务因找不到依赖结果而失败
                results_map[task_index] = task_result
                results.append(task_result)

        return results

    def _topological_sort(self, tasks: List[SubTask]) -> List[SubTask]:
        """
        使用拓扑排序算法，根据依赖关系排序任务

        确保如果任务 A 依赖任务 B，则 B 一定在 A 之前执行。
        对于没有依赖关系的任务，保持原有顺序（或按优先级排序）。

        Args:
            tasks: 子任务列表

        Returns:
            List[SubTask]: 拓扑排序后的子任务列表

        Raises:
            ValueError: 如果存在循环依赖
        """
        n = len(tasks)
        if n == 0:
            return []

        # 构建依赖图：计算每个任务的入度（被依赖的次数）
        in_degree = [0] * n  # 每个任务的入度
        graph: Dict[int, List[int]] = {i: [] for i in range(n)}  # 依赖图

        for i, task in enumerate(tasks):
            for dep_index in task.dependencies:
                # 验证依赖索引是否有效
                if dep_index < 0 or dep_index >= n:
                    raise ValueError(
                        f"任务 {i} 的依赖索引 {dep_index} 无效（任务总数：{n}）"
                    )
                # 如果任务 i 依赖任务 dep_index，则 dep_index -> i
                graph[dep_index].append(i)
                in_degree[i] += 1

        # 使用 Kahn 算法进行拓扑排序
        queue = deque()
        # 将所有入度为 0 的任务（无依赖的任务）加入队列
        for i in range(n):
            if in_degree[i] == 0:
                queue.append(i)

        sorted_indices = []
        while queue:
            # 取出一个无依赖的任务
            current = queue.popleft()
            sorted_indices.append(current)

            # 遍历所有依赖当前任务的任务
            for dependent in graph[current]:
                in_degree[dependent] -= 1
                # 如果依赖任务的所有依赖都已执行，加入队列
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # 检查是否存在循环依赖
        if len(sorted_indices) != n:
            raise ValueError("检测到循环依赖，无法进行拓扑排序")

        # 将索引转换为任务对象
        sorted_tasks = [tasks[i] for i in sorted_indices]

        # 对于同一层级的任务（无依赖关系），按优先级排序
        # 这里简单处理：在拓扑排序的基础上，对连续的无依赖任务按优先级排序
        # 更精细的实现可以在拓扑排序过程中维护优先级队列
        return sorted_tasks

    def _get_dependency_results(
        self,
        task: SubTask,
        task_index: int,
        results_map: Dict[int, TaskResult],
        all_tasks: List[SubTask],
    ) -> List[TaskResult]:
        """
        获取当前任务所依赖的任务的执行结果

        Args:
            task: 当前任务
            task_index: 当前任务在 all_tasks 中的索引
            results_map: 任务索引到执行结果的映射
            all_tasks: 所有任务的列表

        Returns:
            List[TaskResult]: 依赖任务的结果列表，按依赖顺序排列
        """
        dependency_results = []
        for dep_index in task.dependencies:
            # 验证依赖索引是否有效
            if dep_index < 0 or dep_index >= len(all_tasks):
                continue

            # 检查依赖任务是否已执行
            if dep_index in results_map:
                dep_result = results_map[dep_index]
                dependency_results.append(dep_result)
            else:
                # 如果依赖任务还未执行，这不应该发生（拓扑排序应该保证顺序）
                # 但为了健壮性，记录警告
                dependency_results.append(
                    TaskResult(
                        task=all_tasks[dep_index],
                        result="",
                        agent_type=all_tasks[dep_index].assigned_agent,
                        success=False,
                        error=f"依赖任务 {dep_index} 的结果未找到",
                    )
                )

        return dependency_results

    def _enhance_task_with_dependencies(
        self, task: SubTask, dependency_results: List[TaskResult]
    ) -> str:
        """
        将依赖任务的结果添加到当前任务的描述中

        Args:
            task: 当前任务
            dependency_results: 依赖任务的结果列表

        Returns:
            str: 增强后的任务描述
        """
        if not dependency_results:
            # 没有依赖，直接返回原始任务描述
            return task.task_details

        # 构建依赖结果的文本
        dependency_parts = []
        dependency_parts.append("\n\n--- 依赖任务结果 ---")

        for i, dep_result in enumerate(dependency_results, 1):
            dep_task_desc = dep_result.task.task_details
            if dep_result.success:
                dependency_parts.append(
                    f"\n依赖任务 {i}: {dep_task_desc}\n结果: {dep_result.result}"
                )
            else:
                dependency_parts.append(
                    f"\n依赖任务 {i}: {dep_task_desc}\n状态: 执行失败"
                )
                if dep_result.error:
                    dependency_parts.append(f"错误: {dep_result.error}")

        dependency_parts.append("---\n")

        # 将依赖结果添加到任务描述中
        enhanced_task = task.task_details + "\n".join(dependency_parts)

        return enhanced_task
