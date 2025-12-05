# Planning Design 模式分析与实现方案

## 一、Planning Design 核心概念

基于 [Microsoft AI Agents for Beginners - Planning Design](https://github.com/microsoft/ai-agents-for-beginners/blob/main/07-planning-design/README.md) 的学习总结：

### 1.1 核心思想

**Planning Design** 是一种将复杂任务分解为可管理子任务的 Agent 设计模式，主要包括：

1. **定义清晰的总体目标**：确保 Agent 明确知道需要达成什么
2. **任务分解（Task Decomposition）**：将复杂任务拆分为更小的、目标明确的子任务
3. **结构化输出（Structured Output）**：使用 Pydantic 模型或 JSON Schema 让 LLM 生成可解析的计划
4. **多 Agent 编排（Multi-Agent Orchestration）**：根据计划将任务分配给专门的 Agent
5. **迭代规划（Iterative Planning）**：根据执行结果动态调整计划

### 1.2 关键组件

#### 1.2.1 Planner Agent（规划 Agent）
- **职责**：接收用户请求，分析需求，生成结构化计划
- **输出**：包含主任务、子任务列表、每个子任务分配的 Agent 的结构化数据
- **示例结构**：
  ```python
  class TravelSubTask(BaseModel):
      task_details: str
      assigned_agent: AgentEnum
  
  class TravelPlan(BaseModel):
      main_task: str
      subtasks: List[TravelSubTask]
      is_greeting: bool
  ```

#### 1.2.2 专门化 Agent（Specialized Agents）
- **职责**：处理特定类型的子任务
- **特点**：每个 Agent 专注于一个领域（如代码生成、天气查询、文件操作等）
- **工具配置**：每个 Agent 配备相应的工具集

#### 1.2.3 任务路由（Task Routing）
- **职责**：根据计划中的 `assigned_agent` 字段，将子任务路由到对应的 Agent
- **实现方式**：
  - 单任务场景：直接发送到对应 Agent
  - 多任务场景：使用 Group Chat Manager 协调多个 Agent

#### 1.2.4 结果汇总（Result Aggregation）
- **职责**：收集各 Agent 的执行结果，生成最终输出
- **实现方式**：由 Planner 或专门的 Summarizer Agent 完成

### 1.3 工作流程

```
用户请求
  ↓
Planner Agent（生成结构化计划）
  ↓
任务分解（识别子任务和分配的 Agent）
  ↓
任务路由（根据 assigned_agent 分发任务）
  ↓
专门化 Agent 执行（并行或串行）
  ↓
结果汇总（生成最终响应）
  ↓
用户反馈（可选：触发重新规划）
```

## 二、当前项目架构分析

### 2.1 当前架构特点

#### ✅ 已具备的能力

1. **Pydantic AI 框架支持**
   - ✅ 支持结构化输出（`output_type` 参数）
   - ✅ 支持工具注册和调用（`@agent.tool` 装饰器）
   - ✅ 支持依赖注入（`deps_type`）
   - ✅ 支持流式处理（`run_stream`）
   - ✅ 支持多模型（Qwen、DeepSeek、Ollama）

2. **工具系统**
   - ✅ 工具注册表（`tools_registry.py`）
   - ✅ 多种工具：天气、时间、搜索、代码操作等
   - ✅ 工具重试机制（`max_retries`）

3. **代码组织**
   - ✅ 模块化设计（tools、models、prompts 分离）
   - ✅ Agent 创建工具（`anget.py`）

#### ❌ 缺失的能力

1. **多 Agent 架构**
   - ❌ 当前只有一个通用 Agent（`server.py` 中的 `agent`）
   - ❌ 没有专门的 Planner Agent
   - ❌ 没有专门化的子 Agent（代码 Agent、天气 Agent 等）
   - ❌ 没有 Agent 路由机制

2. **结构化规划**
   - ❌ 没有定义计划模型（Plan、SubTask 等）
   - ❌ 没有任务分解逻辑
   - ❌ 没有任务分配机制

3. **多 Agent 协调**
   - ❌ 没有 Group Chat Manager
   - ❌ 没有结果汇总机制
   - ❌ 没有迭代规划支持

### 2.2 Pydantic AI 对 Planning Design 的支持

根据 [Pydantic AI 官方文档](https://ai.pydantic.dev/)：

#### ✅ 完全支持的特性

1. **结构化输出**
   ```python
   agent = Agent(
       model=model,
       output_type=TravelPlan  # Pydantic 模型
   )
   ```

2. **多 Agent 创建**
   - 可以创建多个独立的 Agent 实例
   - 每个 Agent 可以有不同的模型、工具、提示词

3. **工具系统**
   - 支持函数工具（`@agent.tool`）
   - 支持工具集（Toolsets）
   - 支持延迟工具（Deferred Tools）

4. **依赖注入**
   - 通过 `deps_type` 传递上下文
   - 支持在工具和指令中使用依赖

#### ⚠️ 需要自行实现的部分

1. **Agent 路由逻辑**：Pydantic AI 不提供内置的路由器，需要自己实现
2. **多 Agent 协调**：需要自己实现任务分发和结果汇总
3. **迭代规划**：需要自己实现重新规划的逻辑

## 三、实现方案

### 3.1 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                   用户输入层                              │
│              (main.py / server.py)                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Planner Agent（规划 Agent）                  │
│  - 接收用户请求                                          │
│  - 生成结构化计划（TravelPlan）                          │
│  - 任务分解和 Agent 分配                                │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Task Router（任务路由器）                    │
│  - 解析计划中的子任务                                    │
│  - 根据 assigned_agent 路由到对应 Agent                 │
│  - 管理任务执行顺序（串行/并行）                         │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Code     │  │ Weather  │  │ Search   │
│ Agent    │  │ Agent    │  │ Agent    │
│          │  │          │  │          │
│ - 代码   │  │ - 天气   │  │ - 搜索   │
│ - 文件   │  │ - 时间   │  │ - 查询   │
└──────────┘  └──────────┘  └──────────┘
        │            │            │
        └────────────┼────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│          Result Aggregator（结果汇总器）                 │
│  - 收集各 Agent 的执行结果                              │
│  - 生成最终响应                                          │
│  - 支持迭代规划（根据结果重新规划）                      │
└─────────────────────────────────────────────────────────┘
```

### 3.2 核心组件设计

#### 3.2.1 计划模型（Plan Models）

**文件位置**：`models/planning.py`

```python
from enum import Enum
from typing import List
from pydantic import BaseModel, Field

class AgentEnum(str, Enum):
    """可用的 Agent 类型枚举"""
    CODE_AGENT = "code_agent"          # 代码相关任务
    WEATHER_AGENT = "weather_agent"    # 天气/时间任务
    SEARCH_AGENT = "search_agent"      # 搜索任务
    GENERAL_AGENT = "general_agent"    # 通用任务
    DEFAULT_AGENT = "default_agent"    # 默认/兜底

class SubTask(BaseModel):
    """子任务模型"""
    task_details: str = Field(description="子任务的详细描述")
    assigned_agent: AgentEnum = Field(description="分配给哪个 Agent 处理")
    priority: int = Field(default=0, description="任务优先级，数字越大优先级越高")
    dependencies: List[int] = Field(default_factory=list, description="依赖的其他子任务索引")

class Plan(BaseModel):
    """计划模型"""
    main_task: str = Field(description="主任务描述")
    subtasks: List[SubTask] = Field(description="子任务列表")
    is_greeting: bool = Field(default=False, description="是否是问候语")
    requires_iteration: bool = Field(default=False, description="是否需要迭代规划")
```

#### 3.2.2 Planner Agent（规划 Agent）

**文件位置**：`agents/planner.py`

```python
from pydantic_ai import Agent, RunContext
from models.planning import Plan, AgentEnum
from models.qwen import model_qwen
from dataclasses import dataclass

@dataclass
class PlannerDeps:
    """Planner Agent 的依赖"""
    available_agents: dict[AgentEnum, str]  # Agent 类型 -> 描述

planner_agent = Agent(
    model=model_qwen,
    deps_type=PlannerDeps,
    output_type=Plan,
    system_prompt="""你是一个任务规划 Agent。
你的职责是：
1. 分析用户请求，理解主任务
2. 将复杂任务分解为可管理的子任务
3. 为每个子任务分配合适的专门化 Agent

可用的 Agent：
- code_agent: 处理代码生成、修改、文件操作等任务
- weather_agent: 处理天气查询、时间查询等任务
- search_agent: 处理网络搜索、信息查询等任务
- general_agent: 处理通用对话、问答等任务
- default_agent: 兜底 Agent，处理无法分类的任务

请根据任务特点，合理分配 Agent。"""
)
```

#### 3.2.3 专门化 Agent

**文件位置**：`agents/specialized_agents.py`

```python
from pydantic_ai import Agent
from models.qwen import model_qwen
from models.deepseek import model_deepseek
from tools.tools_registry import get_code_tools, get_weather_tools, get_search_tools
from prompts.prompt import get_coder_prompt, get_smart_assistant_prompt

# 代码 Agent
code_agent = Agent(
    model=model_qwen,  # 使用代码能力强的模型
    tools=get_code_tools(),  # 代码相关工具
    system_prompt=get_coder_prompt(),
)

# 天气 Agent
weather_agent = Agent(
    model=model_qwen,
    tools=get_weather_tools(),  # 天气、时间工具
    system_prompt="你是一个天气和时间助手，专门处理天气查询和时间相关的问题。",
)

# 搜索 Agent
search_agent = Agent(
    model=model_qwen,
    tools=get_search_tools(),  # 搜索工具
    system_prompt="你是一个搜索助手，专门处理网络搜索和信息查询任务。",
)

# 通用 Agent
general_agent = Agent(
    model=model_qwen,
    tools=get_all_tools(),  # 所有工具
    system_prompt=get_smart_assistant_prompt(),
)
```

#### 3.2.4 任务路由器（Task Router）

**文件位置**：`agents/router.py`

```python
from typing import Dict, List, Any
from models.planning import Plan, AgentEnum, SubTask
from agents.specialized_agents import (
    code_agent, weather_agent, search_agent, general_agent
)

class TaskRouter:
    """任务路由器，负责将任务分发到对应的 Agent"""
    
    def __init__(self):
        self.agents: Dict[AgentEnum, Agent] = {
            AgentEnum.CODE_AGENT: code_agent,
            AgentEnum.WEATHER_AGENT: weather_agent,
            AgentEnum.SEARCH_AGENT: search_agent,
            AgentEnum.GENERAL_AGENT: general_agent,
            AgentEnum.DEFAULT_AGENT: general_agent,  # 默认使用通用 Agent
        }
    
    async def execute_plan(
        self, 
        plan: Plan, 
        deps: Any,
        execute_parallel: bool = False
    ) -> List[Dict[str, Any]]:
        """
        执行计划
        
        Args:
            plan: 计划对象
            deps: 依赖项
            execute_parallel: 是否并行执行（如果任务间无依赖）
        
        Returns:
            子任务执行结果列表
        """
        results = []
        
        # 按优先级和依赖关系排序任务
        sorted_tasks = self._sort_tasks(plan.subtasks)
        
        for task in sorted_tasks:
            agent = self.agents.get(task.assigned_agent, self.agents[AgentEnum.DEFAULT_AGENT])
            
            # 执行任务
            result = await agent.run(
                task.task_details,
                deps=deps
            )
            
            results.append({
                "task": task,
                "result": result.output,
                "agent": task.assigned_agent.value
            })
        
        return results
    
    def _sort_tasks(self, tasks: List[SubTask]) -> List[SubTask]:
        """根据依赖关系和优先级排序任务"""
        # TODO: 实现拓扑排序
        return sorted(tasks, key=lambda t: (-t.priority, t.dependencies))
```

#### 3.2.5 结果汇总器（Result Aggregator）

**文件位置**：`agents/aggregator.py`

```python
from typing import List, Dict, Any
from pydantic_ai import Agent
from models.qwen import model_qwen

class ResultAggregator:
    """结果汇总器，负责汇总各 Agent 的执行结果"""
    
    def __init__(self):
        self.summarizer = Agent(
            model=model_qwen,
            system_prompt="""你是一个结果汇总 Agent。
你的职责是将多个子任务的执行结果整合成一个连贯、完整的响应。
请确保：
1. 结果逻辑清晰
2. 信息完整
3. 语言自然流畅"""
        )
    
    async def aggregate(
        self,
        main_task: str,
        results: List[Dict[str, Any]],
        deps: Any
    ) -> str:
        """
        汇总结果
        
        Args:
            main_task: 主任务描述
            results: 子任务执行结果列表
            deps: 依赖项
        
        Returns:
            汇总后的最终响应
        """
        # 构建汇总提示
        summary_prompt = f"""主任务：{main_task}

子任务执行结果：
"""
        for i, result in enumerate(results, 1):
            summary_prompt += f"""
{i}. [{result['agent']}] {result['task'].task_details}
   结果：{result['result']}
"""
        summary_prompt += "\n请将以上结果整合成一个完整的响应。"
        
        # 调用汇总 Agent
        summary_result = await self.summarizer.run(summary_prompt, deps=deps)
        return summary_result.output
```

#### 3.2.6 主协调器（Main Orchestrator）

**文件位置**：`agents/orchestrator.py`

```python
from typing import Optional
from models.planning import Plan
from agents.planner import planner_agent, PlannerDeps
from agents.router import TaskRouter
from agents.aggregator import ResultAggregator
from dataclasses import dataclass

@dataclass
class OrchestratorDeps:
    """协调器的依赖"""
    client: Any  # HTTP 客户端等

class PlanningOrchestrator:
    """Planning Design 模式的主协调器"""
    
    def __init__(self):
        self.planner = planner_agent
        self.router = TaskRouter()
        self.aggregator = ResultAggregator()
    
    async def execute(
        self,
        user_input: str,
        deps: OrchestratorDeps,
        max_iterations: int = 3
    ) -> str:
        """
        执行用户请求（支持迭代规划）
        
        Args:
            user_input: 用户输入
            deps: 依赖项
            max_iterations: 最大迭代次数
        
        Returns:
            最终响应
        """
        iteration = 0
        previous_plan: Optional[Plan] = None
        
        while iteration < max_iterations:
            iteration += 1
            
            # 1. 生成计划
            planner_deps = PlannerDeps(
                available_agents={
                    # 定义可用 Agent 的描述
                }
            )
            
            plan_result = await self.planner.run(
                user_input,
                deps=planner_deps
            )
            plan = plan_result.output
            
            # 如果是问候语，直接返回
            if plan.is_greeting:
                return await self._handle_greeting(plan, deps)
            
            # 2. 执行计划
            task_results = await self.router.execute_plan(plan, deps)
            
            # 3. 汇总结果
            final_result = await self.aggregator.aggregate(
                plan.main_task,
                task_results,
                deps
            )
            
            # 4. 检查是否需要迭代
            if not plan.requires_iteration:
                return final_result
            
            # 如果需要迭代，将当前结果作为上下文，重新规划
            user_input = f"{user_input}\n\n当前执行结果：{final_result}\n请根据结果调整计划。"
            previous_plan = plan
        
        # 达到最大迭代次数，返回最后一次的结果
        return final_result
    
    async def _handle_greeting(self, plan: Plan, deps: OrchestratorDeps) -> str:
        """处理问候语"""
        # 使用通用 Agent 处理
        from agents.specialized_agents import general_agent
        result = await general_agent.run(plan.main_task, deps=deps)
        return result.output
```

### 3.3 集成到现有系统

#### 3.3.1 修改 `server.py`

```python
# 在 server.py 中添加 Planning Design 模式支持

from agents.orchestrator import PlanningOrchestrator, OrchestratorDeps

# 创建协调器实例
orchestrator = PlanningOrchestrator()

async def server_run_stream():
    # ... 现有代码 ...
    
    # 在用户输入处理部分，添加 Planning 模式选项
    async with AsyncClient() as client:
        deps = OrchestratorDeps(client=client)
        
        # 可以选择使用 Planning 模式或直接使用单一 Agent
        use_planning = True  # 可以通过配置或用户命令控制
        
        if use_planning:
            # 使用 Planning Design 模式
            result_text = await orchestrator.execute(user_input, deps)
            formatter.print_text(result_text)
        else:
            # 使用原有的单一 Agent 模式
            async with agent.run_stream(...) as result:
                # ... 现有代码 ...
```

#### 3.3.2 工具注册表重构

**文件位置**：`tools/tools_registry.py`

```python
def get_code_tools() -> List[Any]:
    """获取代码相关工具"""
    return [
        read_code_file,
        apply_code_patch,
        check_and_modify_code,
        generate_code,
    ]

def get_weather_tools() -> List[Any]:
    """获取天气/时间工具"""
    return [
        get_current_time,
        Tool(get_weather, max_retries=2),
    ]

def get_search_tools() -> List[Any]:
    """获取搜索工具"""
    return [
        get_duckduckgo_search_tool(),
    ]

def get_all_tools() -> List[Any]:
    """获取所有工具（用于通用 Agent）"""
    return (
        get_code_tools() +
        get_weather_tools() +
        get_search_tools()
    )
```

### 3.4 配置和开关

#### 3.4.1 环境变量配置

```bash
# .env
# Planning Design 模式开关
USE_PLANNING_MODE=true

# 最大迭代次数
PLANNING_MAX_ITERATIONS=3

# 是否并行执行任务（如果无依赖）
PLANNING_PARALLEL_EXECUTION=false
```

#### 3.4.2 命令控制

在 `commands/builtin_commands.py` 中添加：

```python
def process_builtin_command(user_input: str):
    # ... 现有代码 ...
    
    # 添加 Planning 模式切换命令
    if user_input.strip() == "planning on":
        return True, "Planning Design 模式已启用", CommandType.DIRECT
    elif user_input.strip() == "planning off":
        return True, "Planning Design 模式已禁用", CommandType.DIRECT
```

## 四、实施步骤建议

### 阶段一：基础架构（1-2 天）

1. ✅ 创建计划模型（`models/planning.py`）
2. ✅ 创建 Planner Agent（`agents/planner.py`）
3. ✅ 重构工具注册表，按功能分类（`tools/tools_registry.py`）

### 阶段二：专门化 Agent（2-3 天）

1. ✅ 创建专门化 Agent（`agents/specialized_agents.py`）
   - Code Agent
   - Weather Agent
   - Search Agent
   - General Agent

2. ✅ 为每个 Agent 配置合适的工具和提示词

### 阶段三：路由和协调（2-3 天）

1. ✅ 实现任务路由器（`agents/router.py`）
2. ✅ 实现结果汇总器（`agents/aggregator.py`）
3. ✅ 实现主协调器（`agents/orchestrator.py`）

### 阶段四：集成和测试（2-3 天）

1. ✅ 集成到 `server.py`
2. ✅ 添加配置开关
3. ✅ 测试各种场景
4. ✅ 性能优化

### 阶段五：迭代规划（可选，1-2 天）

1. ✅ 实现依赖关系处理
2. ✅ 实现并行执行
3. ✅ 实现重新规划逻辑

## 五、优势与挑战

### 5.1 优势

1. **任务分解清晰**：复杂任务被分解为可管理的子任务
2. **专业化**：每个 Agent 专注于特定领域，提高准确性
3. **可扩展性**：易于添加新的专门化 Agent
4. **可维护性**：模块化设计，易于维护和调试
5. **灵活性**：支持串行/并行执行，支持迭代规划

### 5.2 挑战

1. **复杂度增加**：需要管理多个 Agent 和路由逻辑
2. **延迟增加**：多 Agent 协调可能增加响应时间
3. **错误处理**：需要处理 Agent 执行失败的情况
4. **成本**：多个 Agent 调用可能增加 API 成本

### 5.3 优化建议

1. **缓存机制**：缓存 Planner 的结果，避免重复规划
2. **并行执行**：对于无依赖的任务，并行执行以提高效率
3. **降级策略**：如果 Planning 模式失败，降级到单一 Agent 模式
4. **监控和日志**：使用 Logfire 监控各 Agent 的执行情况

## 六、总结

### 6.1 可行性评估

✅ **完全可行**：当前项目基于 Pydantic AI，完全支持 Planning Design 模式所需的所有特性。

### 6.2 关键点

1. **结构化输出**：使用 Pydantic 模型定义计划结构
2. **多 Agent 架构**：创建专门的 Planner 和多个专门化 Agent
3. **路由机制**：实现任务分发和结果汇总
4. **渐进式实施**：可以先实现基础版本，再逐步完善

### 6.3 建议

1. **先实现 MVP**：实现基础的单次规划-执行-汇总流程
2. **逐步完善**：再添加迭代规划、并行执行等高级特性
3. **保持兼容**：保留原有的单一 Agent 模式作为备选
4. **充分测试**：测试各种场景，确保稳定性

---

**参考资源**：
- [Microsoft AI Agents for Beginners - Planning Design](https://github.com/microsoft/ai-agents-for-beginners/blob/main/07-planning-design/README.md)
- [Pydantic AI 官方文档](https://ai.pydantic.dev/)
- [Pydantic AI Multi-Agent Patterns](https://ai.pydantic.dev/multi-agent/)
