"""
结果汇总器

负责汇总各 Agent 的执行结果，生成最终响应。
第一阶段使用简单拼接，后续可以升级为使用 Agent 汇总。
"""

from typing import List
from planning.router import TaskResult


class ResultAggregator:
    """结果汇总器，负责汇总各 Agent 的执行结果"""

    def __init__(self):
        """初始化结果汇总器"""
        pass

    def aggregate(self, main_task: str, results: List[TaskResult]) -> str:
        """
        汇总结果（第一阶段：简单拼接）

        Args:
            main_task: 主任务描述
            results: 子任务执行结果列表

        Returns:
            str: 汇总后的最终响应
        """
        # 如果没有结果，返回提示
        if not results:
            return f"任务 '{main_task}' 没有需要执行的子任务。"

        # 统计成功和失败的任务
        success_count = sum(1 for r in results if r.success)
        fail_count = len(results) - success_count

        # 构建汇总文本
        aggregated_parts: List[str] = []

        # 添加主任务说明
        aggregated_parts.append(f"## 任务：{main_task}\n")

        # 添加每个子任务的结果
        for i, result in enumerate(results, 1):
            agent_name = result.agent_type.value.replace("_", " ").title()
            task_desc = result.task.task_details

            if result.success:
                aggregated_parts.append(f"### {i}. [{agent_name}] {task_desc}")
                aggregated_parts.append(f"✅ 执行成功")
                aggregated_parts.append(f"{result.result}\n")
            else:
                aggregated_parts.append(f"### {i}. [{agent_name}] {task_desc}")
                aggregated_parts.append(f"❌ 执行失败")
                if result.error:
                    aggregated_parts.append(f"错误：{result.error}\n")
                else:
                    aggregated_parts.append("\n")

        # 添加总结
        if fail_count > 0:
            aggregated_parts.append(
                f"\n---\n**总结**：共 {len(results)} 个子任务，"
                f"成功 {success_count} 个，失败 {fail_count} 个。"
            )
        else:
            aggregated_parts.append(
                f"\n---\n**总结**：所有 {len(results)} 个子任务执行成功。"
            )

        return "\n".join(aggregated_parts)

    # TODO: 后续可以添加使用 Agent 汇总的方法
    # async def aggregate_with_agent(
    #     self, main_task: str, results: List[TaskResult], deps: Deps
    # ) -> str:
    #     """使用 Agent 汇总结果（更智能，但需要额外调用）"""
    #     ...
