"""
Planning Design 模式测试

测试 Planning Design 模式的核心功能：
1. Planner Agent 生成计划
2. 任务路由和执行
3. 结果汇总
4. 完整流程
"""

import asyncio
import os
from httpx import AsyncClient
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from models.planning import Plan, SubTask, AgentEnum
from planning.planner import create_plan, PlannerDeps
from planning.router import TaskRouter, TaskResult
from planning.aggregator import ResultAggregator
from planning.orchestrator import PlanningOrchestrator
from planning.specialized_agents import Deps


async def test_planner_simple():
    """测试 Planner Agent：简单任务"""
    print("\n=== 测试 1: Planner Agent - 简单任务 ===")

    async with AsyncClient() as client:
        planner_deps = PlannerDeps(client=client)

        user_input = "查询北京天气"
        plan = await create_plan(user_input, deps=planner_deps)

        print(f"主任务: {plan.main_task}")
        print(f"是否问候语: {plan.is_greeting}")
        print(f"子任务数量: {len(plan.subtasks)}")
        for i, task in enumerate(plan.subtasks, 1):
            print(f"  子任务 {i}: {task.task_details}")
            print(f"    分配 Agent: {task.assigned_agent.value}")

        assert isinstance(plan, Plan), "应该返回 Plan 对象"
        assert not plan.is_greeting, "不应该识别为问候语"
        assert len(plan.subtasks) > 0, "应该有子任务"
        print("✅ 测试通过")


async def test_planner_complex():
    """测试 Planner Agent：复杂任务"""
    print("\n=== 测试 2: Planner Agent - 复杂任务 ===")

    async with AsyncClient() as client:
        planner_deps = PlannerDeps(client=client)

        user_input = "查询北京天气，然后生成一个 Python 脚本来显示天气"
        plan = await create_plan(user_input, deps=planner_deps)

        print(f"主任务: {plan.main_task}")
        print(f"子任务数量: {len(plan.subtasks)}")
        for i, task in enumerate(plan.subtasks, 1):
            print(f"  子任务 {i}: {task.task_details}")
            print(f"    分配 Agent: {task.assigned_agent.value}")
            print(f"    优先级: {task.priority}")
            print(f"    依赖: {task.dependencies}")

        assert len(plan.subtasks) >= 2, "应该有至少 2 个子任务"
        print("✅ 测试通过")


async def test_planner_greeting():
    """测试 Planner Agent：问候语"""
    print("\n=== 测试 3: Planner Agent - 问候语 ===")

    async with AsyncClient() as client:
        planner_deps = PlannerDeps(client=client)

        user_input = "你好"
        plan = await create_plan(user_input, deps=planner_deps)

        print(f"主任务: {plan.main_task}")
        print(f"是否问候语: {plan.is_greeting}")

        assert plan.is_greeting, "应该识别为问候语"
        print("✅ 测试通过")


async def test_router_execution():
    """测试任务路由器：执行计划"""
    print("\n=== 测试 4: 任务路由器 - 执行计划 ===")

    async with AsyncClient() as client:
        planner_deps = PlannerDeps(client=client)
        router_deps = Deps(client=client)

        # 先创建一个计划
        user_input = "查询北京天气"
        plan = await create_plan(user_input, deps=planner_deps)

        # 执行计划
        router = TaskRouter()
        results = await router.execute_plan(plan, deps=router_deps)

        print(f"执行结果数量: {len(results)}")
        for i, result in enumerate(results, 1):
            print(f"  结果 {i}:")
            print(f"    任务: {result.task.task_details}")
            print(f"    Agent: {result.agent_type.value}")
            print(f"    成功: {result.success}")
            if result.success:
                print(f"    结果: {result.result[:100]}...")  # 只显示前100字符
            else:
                print(f"    错误: {result.error}")

        assert len(results) > 0, "应该有执行结果"
        print("✅ 测试通过")


async def test_aggregator():
    """测试结果汇总器"""
    print("\n=== 测试 5: 结果汇总器 ===")

    # 创建模拟结果
    results = [
        TaskResult(
            task=SubTask(
                task_details="查询北京天气",
                assigned_agent=AgentEnum.WEATHER_AGENT,
            ),
            result="北京：晴天，25°C",
            agent_type=AgentEnum.WEATHER_AGENT,
            success=True,
        ),
        TaskResult(
            task=SubTask(
                task_details="生成显示天气的脚本",
                assigned_agent=AgentEnum.CODE_AGENT,
            ),
            result="print('北京：晴天，25°C')",
            agent_type=AgentEnum.CODE_AGENT,
            success=True,
        ),
    ]

    aggregator = ResultAggregator()
    summary = aggregator.aggregate("查询天气并生成脚本", results)

    print("汇总结果:")
    print(summary)

    assert "北京" in summary, "应该包含天气信息"
    assert "成功" in summary, "应该包含成功信息"
    print("✅ 测试通过")


async def test_orchestrator_simple():
    """测试主协调器：简单任务"""
    print("\n=== 测试 6: 主协调器 - 简单任务 ===")

    async with AsyncClient() as client:
        deps = Deps(client=client)
        orchestrator = PlanningOrchestrator()

        user_input = "查询北京天气"
        result = await orchestrator.execute(user_input, deps=deps, max_iterations=1)

        print("最终结果:")
        print(result[:200] + "..." if len(result) > 200 else result)

        assert len(result) > 0, "应该有结果"
        print("✅ 测试通过")


async def test_orchestrator_greeting():
    """测试主协调器：问候语"""
    print("\n=== 测试 7: 主协调器 - 问候语 ===")

    async with AsyncClient() as client:
        deps = Deps(client=client)
        orchestrator = PlanningOrchestrator()

        user_input = "你好"
        result = await orchestrator.execute(user_input, deps=deps, max_iterations=1)

        print("最终结果:")
        print(result)

        assert len(result) > 0, "应该有结果"
        print("✅ 测试通过")


async def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("Planning Design 模式测试")
    print("=" * 60)

    tests = [
        test_planner_simple,
        test_planner_complex,
        test_planner_greeting,
        test_router_execution,
        test_aggregator,
        test_orchestrator_simple,
        test_orchestrator_greeting,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback

            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"测试完成: 通过 {passed}/{len(tests)}, 失败 {failed}/{len(tests)}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all_tests())


