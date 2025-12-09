"""
Planning Design 模式的数据模型

定义任务计划、子任务和 Agent 类型等核心数据结构。
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class AgentEnum(str, Enum):
    """可用的 Agent 类型枚举"""

    CODE_AGENT = "code_agent"  # 代码相关任务（生成、修改、文件操作等）
    WEATHER_AGENT = "weather_agent"  # 天气/时间相关任务
    SEARCH_AGENT = "search_agent"  # 网络搜索、信息查询任务
    GENERAL_AGENT = "general_agent"  # 通用对话、问答任务
    CONTEXT_AGENT = "context_agent"  # 上下文/历史相关任务
    DEFAULT_AGENT = "default_agent"  # 默认/兜底 Agent


class SubTask(BaseModel):
    """子任务模型"""

    task_details: str = Field(description="子任务的详细描述，说明需要完成什么")
    assigned_agent: AgentEnum = Field(
        description="分配给哪个专门化 Agent 来处理这个子任务"
    )
    priority: int = Field(
        default=0, description="任务优先级，数字越大优先级越高。默认为 0"
    )
    dependencies: List[int] = Field(
        default_factory=list,
        description="依赖的其他子任务索引列表。如果此任务依赖于其他任务，先执行依赖任务",
    )


class Plan(BaseModel):
    """任务计划模型"""

    main_task: str = Field(description="主任务描述，总结用户想要达成的整体目标")
    subtasks: List[SubTask] = Field(
        description="子任务列表，将主任务分解为可管理的子任务"
    )
    is_greeting: bool = Field(
        default=False,
        description="是否是问候语或简单对话。如果是，可以直接处理，不需要分解任务",
    )
    requires_iteration: bool = Field(
        default=False,
        description="是否需要迭代规划。如果任务执行后需要根据结果调整计划，设为 True",
    )
