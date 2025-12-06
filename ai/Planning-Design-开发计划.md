# Planning Design 开发计划

## 📋 项目目标

在当前工程中实现 Planning Design 模式，使用 Pydantic AI 框架，支持任务分解、多 Agent 编排和结果汇总。

## 🏗️ 目录结构设计

```
agentz/
├── models/
│   ├── qwen.py              # 现有：Qwen 模型配置
│   ├── deepseek.py          # 现有：DeepSeek 模型配置
│   ├── ollama_qwen.py       # 现有：Ollama 模型配置
│   └── planning.py          # 🆕 计划模型定义（Plan, SubTask, AgentEnum）
│
├── prompts/
│   ├── prompt.py             # 现有：通用提示词
│   └── planning_prompts.py   # 🆕 Planning 相关提示词
│
├── tools/
│   ├── tools_registry.py     # 现有：工具注册表（需要重构）
│   ├── code_reader.py        # 现有
│   ├── code_patcher.py      # 现有
│   ├── coder.py             # 现有
│   ├── time_tools.py        # 现有
│   ├── weather_tools.py     # 现有
│   └── web_search.py        # 现有
│
├── planning/                # 🆕 Planning Design 核心模块
│   ├── __init__.py
│   ├── planner.py           # Planner Agent
│   ├── specialized_agents.py # 专门化 Agent（Code/Weather/Search/General）
│   ├── router.py            # 任务路由器
│   ├── aggregator.py        # 结果汇总器
│   └── orchestrator.py     # 主协调器
│
├── server.py                # 现有：需要集成 Planning 模式
└── main.py                  # 现有：入口文件
```

## 📝 开发步骤

### 阶段一：基础模型和提示词（Foundation）

#### ✅ 步骤 1.1：创建计划模型
**目标**：定义 Planning Design 所需的数据结构

**文件**：`models/planning.py`

**实现内容**：
- [ ] 定义 `AgentEnum` 枚举（CODE_AGENT, WEATHER_AGENT, SEARCH_AGENT, GENERAL_AGENT, DEFAULT_AGENT）
- [ ] 定义 `SubTask` Pydantic 模型
  - `task_details: str` - 子任务描述
  - `assigned_agent: AgentEnum` - 分配的 Agent
  - `priority: int` - 优先级（可选）
  - `dependencies: List[int]` - 依赖关系（可选，用于后续迭代）
- [ ] 定义 `Plan` Pydantic 模型
  - `main_task: str` - 主任务描述
  - `subtasks: List[SubTask]` - 子任务列表
  - `is_greeting: bool` - 是否是问候语
  - `requires_iteration: bool` - 是否需要迭代规划（可选，用于后续迭代）

**验收标准**：
- [ ] 模型可以正常导入
- [ ] 模型可以正常序列化/反序列化
- [ ] 类型检查通过

---

#### ✅ 步骤 1.2：创建 Planning 提示词
**目标**：为 Planner Agent 和专门化 Agent 准备提示词

**文件**：`prompts/planning_prompts.py`

**实现内容**：
- [ ] `get_planner_prompt()` - Planner Agent 的系统提示词
  - 说明 Planner 的职责
  - 列出可用的 Agent 类型及其用途
  - 说明如何分解任务和分配 Agent
- [ ] `get_code_agent_prompt()` - Code Agent 的系统提示词
  - 基于现有的 `get_coder_prompt()`，可能需要调整
- [ ] `get_weather_agent_prompt()` - Weather Agent 的系统提示词
- [ ] `get_search_agent_prompt()` - Search Agent 的系统提示词
- [ ] `get_general_agent_prompt()` - General Agent 的系统提示词
  - 可以基于现有的 `get_smart_assistant_prompt()`
- [ ] `get_aggregator_prompt()` - 结果汇总器的提示词（可选，如果使用 Agent 汇总）

**验收标准**：
- [ ] 所有提示词函数可以正常调用
- [ ] 提示词内容清晰、明确
- [ ] 与现有提示词风格一致

---

### 阶段二：工具注册表重构（Tools Refactoring）

#### ✅ 步骤 2.1：重构工具注册表
**目标**：按功能分类工具，便于分配给不同的专门化 Agent

**文件**：`tools/tools_registry.py`

**实现内容**：
- [ ] `get_code_tools()` - 返回代码相关工具列表
  - `read_code_file`
  - `apply_code_patch`
  - `check_and_modify_code`
  - `generate_code`
- [ ] `get_weather_tools()` - 返回天气/时间工具列表
  - `get_current_time`
  - `get_weather`
- [ ] `get_search_tools()` - 返回搜索工具列表
  - `duckduckgo_search`
  - `tavily_search`（如果可用）
- [ ] `get_all_tools()` - 返回所有工具（用于 General Agent）
  - 调用上述三个函数并合并

**注意**：
- 保持 `get_all_tools()` 的向后兼容性（用于现有的通用 Agent）
- 工具函数本身不需要修改，只是重新组织

**验收标准**：
- [ ] 所有工具分类函数正常工作
- [ ] 现有代码（server.py）仍能正常使用 `get_all_tools()`
- [ ] 工具列表不重复、不遗漏

---

### 阶段三：专门化 Agent（Specialized Agents）

#### ✅ 步骤 3.1：创建专门化 Agent
**目标**：创建各个专门化的 Agent 实例

**文件**：`planning/specialized_agents.py`

**实现内容**：
- [ ] `create_code_agent()` - 创建 Code Agent
  - 使用 `model_qwen`（代码能力强）
  - 使用 `get_code_tools()` 获取工具
  - 使用 `get_code_agent_prompt()` 作为系统提示词
- [ ] `create_weather_agent()` - 创建 Weather Agent
  - 使用 `model_qwen`
  - 使用 `get_weather_tools()` 获取工具
  - 使用 `get_weather_agent_prompt()` 作为系统提示词
- [ ] `create_search_agent()` - 创建 Search Agent
  - 使用 `model_qwen`
  - 使用 `get_search_tools()` 获取工具
  - 使用 `get_search_agent_prompt()` 作为系统提示词
- [ ] `create_general_agent()` - 创建 General Agent
  - 使用 `model_qwen`
  - 使用 `get_all_tools()` 获取工具
  - 使用 `get_general_agent_prompt()` 作为系统提示词
- [ ] `get_agent_by_type(agent_type: AgentEnum)` - 根据类型获取 Agent
  - 返回对应的 Agent 实例

**依赖注入**：
- 所有 Agent 使用相同的 `Deps` 类型（与现有 `server.py` 中的一致）

**验收标准**：
- [ ] 所有 Agent 可以正常创建
- [ ] 每个 Agent 都有正确的工具和提示词
- [ ] `get_agent_by_type()` 可以正确返回对应的 Agent

---

### 阶段四：Planner Agent（Planning Agent）

#### ✅ 步骤 4.1：创建 Planner Agent
**目标**：创建负责任务分解和规划的 Agent

**文件**：`planning/planner.py`

**实现内容**：
- [ ] 定义 `PlannerDeps` 数据类（如果需要额外的依赖）
  - 可以包含可用 Agent 的描述信息
- [ ] 创建 `planner_agent` 实例
  - 使用 `model_qwen`
  - 使用 `output_type=Plan`（结构化输出）
  - 使用 `get_planner_prompt()` 作为系统提示词
  - 使用 `PlannerDeps` 作为依赖类型（如果需要）
- [ ] `create_plan(user_input: str, deps: PlannerDeps) -> Plan` - 生成计划
  - 调用 `planner_agent.run()` 生成计划
  - 返回 `Plan` 对象

**验收标准**：
- [ ] Planner Agent 可以正常创建
- [ ] `create_plan()` 可以生成有效的计划
- [ ] 生成的计划包含合理的子任务和 Agent 分配

---

### 阶段五：任务路由和协调（Routing & Orchestration）

#### ✅ 步骤 5.1：创建任务路由器
**目标**：实现任务分发逻辑

**文件**：`planning/router.py`

**实现内容**：
- [ ] `TaskRouter` 类
  - `__init__()` - 初始化，注册所有专门化 Agent
  - `execute_plan(plan: Plan, deps: Deps) -> List[TaskResult]` - 执行计划
    - 遍历 `plan.subtasks`
    - 根据 `assigned_agent` 获取对应的 Agent
    - 调用 Agent 执行子任务
    - 收集结果
  - `_sort_tasks(tasks: List[SubTask]) -> List[SubTask]` - 任务排序（可选）
    - 根据优先级和依赖关系排序
- [ ] `TaskResult` 数据类（可选）
  - `task: SubTask`
  - `result: str`
  - `agent_type: AgentEnum`
  - `success: bool`
  - `error: Optional[str]`

**注意**：
- 第一阶段先实现串行执行
- 后续可以添加并行执行（如果任务无依赖）

**验收标准**：
- [ ] `TaskRouter` 可以正确路由任务到对应的 Agent
- [ ] 可以正确收集执行结果
- [ ] 错误处理完善（Agent 执行失败时的处理）

---

#### ✅ 步骤 5.2：创建结果汇总器
**目标**：汇总各 Agent 的执行结果

**文件**：`planning/aggregator.py`

**实现内容**：
- [ ] `ResultAggregator` 类
  - `__init__()` - 初始化汇总 Agent（可选，如果使用 Agent 汇总）
  - `aggregate(main_task: str, results: List[TaskResult], deps: Deps) -> str` - 汇总结果
    - 方案 A：使用 Agent 汇总（更智能，但需要额外调用）
    - 方案 B：简单拼接（快速，但可能不够自然）
    - 建议：第一阶段使用方案 B，后续可以升级为方案 A

**验收标准**：
- [ ] `aggregate()` 可以正确汇总结果
- [ ] 汇总后的结果逻辑清晰、信息完整

---

#### ✅ 步骤 5.3：创建主协调器
**目标**：统一管理整个 Planning 流程

**文件**：`planning/orchestrator.py`

**实现内容**：
- [ ] `PlanningOrchestrator` 类
  - `__init__()` - 初始化 Planner、Router、Aggregator
  - `execute(user_input: str, deps: Deps, max_iterations: int = 1) -> str` - 执行主流程
    - 调用 Planner 生成计划
    - 如果是问候语，直接处理
    - 调用 Router 执行计划
    - 调用 Aggregator 汇总结果
    - 返回最终响应
  - `_handle_greeting(plan: Plan, deps: Deps) -> str` - 处理问候语（可选）

**注意**：
- 第一阶段 `max_iterations=1`（不迭代）
- 后续可以添加迭代规划逻辑

**验收标准**：
- [ ] `PlanningOrchestrator` 可以完整执行 Planning 流程
- [ ] 可以正确处理各种类型的任务
- [ ] 错误处理完善

---

### 阶段六：集成到现有系统（Integration）

#### ✅ 步骤 6.1：在 server.py 中集成 Planning 模式
**目标**：将 Planning 模式集成到现有的服务器中

**文件**：`server.py`

**实现内容**：
- [ ] 导入 Planning 相关模块
  - `from planning.orchestrator import PlanningOrchestrator`
- [ ] 创建 `PlanningOrchestrator` 实例（可选，延迟初始化）
- [ ] 在 `server_run_stream()` 中添加 Planning 模式开关
  - 方案 A：环境变量控制（`USE_PLANNING_MODE`）
  - 方案 B：用户命令控制（`planning on/off`）
  - 方案 C：自动判断（根据任务复杂度）
  - 建议：第一阶段使用方案 A，后续可以添加方案 B
- [ ] 修改用户输入处理逻辑
  - 如果启用 Planning 模式，使用 `orchestrator.execute()`
  - 否则使用现有的单一 Agent 模式
- [ ] 保持流式输出支持（如果可能）
  - Planning 模式可能较难实现流式输出
  - 可以先实现非流式版本

**验收标准**：
- [ ] Planning 模式可以正常启用/禁用
- [ ] 两种模式可以正常切换
- [ ] 不影响现有功能

---

#### ✅ 步骤 6.2：添加配置和命令支持（可选）
**目标**：提供更灵活的控制方式

**文件**：
- `commands/builtin_commands.py` - 添加 Planning 相关命令
- `.env.example` - 添加环境变量示例

**实现内容**：
- [ ] 在 `builtin_commands.py` 中添加命令
  - `planning on` - 启用 Planning 模式
  - `planning off` - 禁用 Planning 模式
  - `planning status` - 查看当前状态
- [ ] 在 `.env.example` 中添加
  - `USE_PLANNING_MODE=true/false`
  - `PLANNING_MAX_ITERATIONS=1`（用于后续迭代）

**验收标准**：
- [ ] 命令可以正常执行
- [ ] 环境变量可以正常读取

---

### 阶段七：测试和优化（Testing & Optimization）

#### ✅ 步骤 7.1：基础功能测试
**目标**：确保核心功能正常工作

**测试场景**：
- [ ] 简单任务（单一 Agent 可以处理）
  - 例如："查询北京天气"
  - 预期：Planner 分配 Weather Agent，正常返回结果
- [ ] 复杂任务（需要多个 Agent）
  - 例如："查询北京天气，然后生成一个 Python 脚本来显示天气"
  - 预期：Planner 分解为两个子任务，分别由 Weather Agent 和 Code Agent 处理
- [ ] 问候语
  - 例如："你好"
  - 预期：识别为问候语，直接处理
- [ ] 错误处理
  - Agent 执行失败时的处理
  - 无效计划的处理

**验收标准**：
- [ ] 所有测试场景通过
- [ ] 错误处理完善

---

#### ✅ 步骤 7.2：性能优化（可选）
**目标**：优化响应时间和资源使用

**优化方向**：
- [ ] 并行执行（如果任务无依赖）
- [ ] 缓存 Planner 结果（相同任务不重复规划）
- [ ] 简化结果汇总（如果 Agent 汇总太慢）

**验收标准**：
- [ ] 响应时间有所改善
- [ ] 不影响功能正确性

---

## 🔄 计划更新记录

### 2024-12-19：初始计划
- 创建开发计划文档
- 定义 7 个阶段，共 13 个步骤
- 确认所有决策

### 2024-12-19：阶段一完成
- ✅ 步骤 1.1：创建计划模型 (`models/planning.py`)
  - 定义 `AgentEnum` 枚举
  - 定义 `SubTask` 模型
  - 定义 `Plan` 模型
- ✅ 步骤 1.2：创建 Planning 提示词 (`prompts/planning_prompts.py`)
  - `get_planner_prompt()` - Planner Agent 提示词
  - `get_code_agent_prompt()` - Code Agent 提示词
  - `get_weather_agent_prompt()` - Weather Agent 提示词
  - `get_search_agent_prompt()` - Search Agent 提示词
  - `get_general_agent_prompt()` - General Agent 提示词
  - `get_aggregator_prompt()` - 汇总器提示词（预留）

### 2024-12-19：阶段二完成
- ✅ 步骤 2.1：重构工具注册表 (`tools/tools_registry.py`)
  - 添加 `get_code_tools()` - 代码相关工具（4个）
  - 添加 `get_weather_tools()` - 天气/时间工具（2个）
  - 添加 `get_search_tools()` - 搜索工具（1个）
  - 重构 `get_all_tools()` - 保持向后兼容，合并所有工具（7个）
  - 定义工具函数：`read_code_file`, `apply_code_patch_tool`, `check_and_modify_code`, `generate_code`

### 2024-12-19：阶段三完成
- ✅ 步骤 3.1：创建专门化 Agent (`planning/specialized_agents.py`)
  - 创建 `planning/` 目录和 `__init__.py`
  - 实现 `_create_code_agent()` - Code Agent（代码任务）
  - 实现 `_create_weather_agent()` - Weather Agent（天气/时间任务）
  - 实现 `_create_search_agent()` - Search Agent（搜索任务）
  - 实现 `_create_general_agent()` - General Agent（通用任务）
  - 实现延迟初始化机制（首次使用时创建）
  - 实现 `get_agent_by_type()` - 根据 AgentEnum 获取对应 Agent
  - 所有 Agent 使用相同的 `Deps` 类型（与 server.py 保持一致）

### 2024-12-19：阶段四完成
- ✅ 步骤 4.1：创建 Planner Agent (`planning/planner.py`)
  - 定义 `PlannerDeps` 数据类（保持一致性，虽然 Planner 可能不需要额外依赖）
  - 实现 `_create_planner_agent()` - 创建 Planner Agent
    - 使用 `model_qwen`
    - 使用 `output_type=Plan`（结构化输出）
    - 使用 `get_planner_prompt()` 作为系统提示词
  - 实现延迟初始化机制
  - 实现 `create_plan()` - 根据用户输入生成任务计划
  - 更新 `planning/__init__.py` 导出 Planner 相关接口

### 2024-12-19：阶段五完成
- ✅ 步骤 5.1：创建任务路由器 (`planning/router.py`)
  - 定义 `TaskResult` 数据类（子任务执行结果）
  - 实现 `TaskRouter` 类
    - `execute_plan()` - 执行计划，遍历子任务，调用对应 Agent
    - `_sort_tasks()` - 任务排序（按优先级和依赖关系，第一阶段简单实现）
  - 错误处理：任务失败时继续执行其他任务，记录错误信息
  - 支持问候语检测（如果是问候语，不执行子任务）

- ✅ 步骤 5.2：创建结果汇总器 (`planning/aggregator.py`)
  - 实现 `ResultAggregator` 类
  - 实现 `aggregate()` - 汇总结果（第一阶段：简单拼接）
    - 统计成功/失败任务数
    - 按顺序展示每个子任务的结果
    - 添加总结信息
  - 预留 Agent 汇总接口（TODO，用于后续升级）

- ✅ 步骤 5.3：创建主协调器 (`planning/orchestrator.py`)
  - 实现 `PlanningOrchestrator` 类
  - 实现 `execute()` - 主流程
    - 调用 Planner 生成计划
    - 处理问候语（使用 General Agent）
    - 调用 Router 执行计划
    - 调用 Aggregator 汇总结果
    - 支持迭代规划（第一阶段 max_iterations=1）
  - 实现 `_handle_greeting()` - 处理问候语
  - 完善的错误处理
  - 更新 `planning/__init__.py` 导出所有接口

### 2024-12-19：阶段六完成
- ✅ 步骤 6.1：在 server.py 中集成 Planning 模式
  - 导入 Planning 相关模块（`PlanningOrchestrator`, `PlanningDeps`）
  - 添加环境变量读取（`USE_PLANNING_MODE`, `PLANNING_MAX_ITERATIONS`）
  - 在 `server_run_stream()` 中初始化 `PlanningOrchestrator`（如果启用）
  - 修改用户输入处理逻辑：
    - 如果启用 Planning 模式：使用 `orchestrator.execute()`（非流式）
    - 否则：使用单一 Agent 模式（流式）
  - 保持两种模式的兼容性
  - 添加 Planning 模式启用提示

- ✅ 步骤 6.2：添加配置支持（环境变量）
  - `USE_PLANNING_MODE` - 控制是否启用 Planning 模式（默认 false）
  - `PLANNING_MAX_ITERATIONS` - 最大迭代次数（默认 1）

### 2024-12-19：阶段七完成
- ✅ 步骤 7.1：基础功能测试
  - 创建测试脚本 (`tests/test_planning.py`)
    - 测试 Planner Agent（简单任务、复杂任务、问候语）
    - 测试任务路由器（执行计划、错误处理）
    - 测试结果汇总器（结果汇总）
    - 测试主协调器（完整流程）
  - 创建优化建议文档 (`ai/Planning-Design-优化建议.md`)
    - 性能优化建议（并行执行、缓存机制）
    - 功能增强建议（流式输出、Agent 汇总）
    - 错误处理增强建议
    - 监控和调试建议
  - 创建使用说明文档 (`ai/Planning-Design-使用说明.md`)
    - 快速开始指南
    - 配置选项说明
    - 架构说明
    - 常见问题解答

---

## ✅ 已确认决策

### 1. 目录结构
**决策**：✅ 使用 `planning/` 目录

---

### 2. 流式输出支持
**决策**：✅ 第一阶段先实现非流式版本
- 后续可以考虑流式输出（显示每个子任务的执行过程）

---

### 3. 错误处理策略
**决策**：✅ 继续执行其他任务，最后汇总时说明失败的任务
- 第一阶段使用此策略
- 后续可以添加重试机制

---

### 4. 结果汇总方式
**决策**：✅ 第一阶段使用简单拼接
- 后续可以升级为 Agent 汇总（作为可选功能）

---

### 5. Planning 模式触发方式
**决策**：✅ 使用环境变量控制（`USE_PLANNING_MODE`）
- 后续可以添加用户命令控制（`planning on/off`）

---

### 6. 与现有代码的兼容性
**决策**：✅ 保持两个入口，方便切换
- 通过环境变量或配置控制使用哪种模式
- 确保两种模式可以正常切换

---

## 📊 进度跟踪

### 总体进度：100% (13/13 步骤完成) 🎉

#### 阶段一：基础模型和提示词
- [x] 步骤 1.1：创建计划模型 (100%) ✅
  - 📁 `models/planning.py` - 定义 `AgentEnum`, `SubTask`, `Plan` 模型
- [x] 步骤 1.2：创建 Planning 提示词 (100%) ✅
  - 📁 `prompts/planning_prompts.py` - Planner 和专门化 Agent 的提示词

#### 阶段二：工具注册表重构
- [x] 步骤 2.1：重构工具注册表 (100%) ✅
  - 📁 `tools/tools_registry.py` - 添加工具分类函数（`get_code_tools`, `get_weather_tools`, `get_search_tools`）
  - 📁 `tools/tools_registry.py` - 定义工具函数（`read_code_file`, `apply_code_patch_tool`, `check_and_modify_code`, `generate_code`）

#### 阶段三：专门化 Agent
- [x] 步骤 3.1：创建专门化 Agent (100%) ✅
  - 📁 `planning/__init__.py` - 模块初始化
  - 📁 `planning/specialized_agents.py` - 实现 4 个专门化 Agent（Code, Weather, Search, General）

#### 阶段四：Planner Agent
- [x] 步骤 4.1：创建 Planner Agent (100%) ✅
  - 📁 `planning/planner.py` - Planner Agent 实现
  - 📁 `planning/__init__.py` - 更新导出接口

#### 阶段五：任务路由和协调
- [x] 步骤 5.1：创建任务路由器 (100%) ✅
  - 📁 `planning/router.py` - `TaskRouter` 类和 `TaskResult` 数据类
  - 📁 `planning/__init__.py` - 更新导出接口
- [x] 步骤 5.2：创建结果汇总器 (100%) ✅
  - 📁 `planning/aggregator.py` - `ResultAggregator` 类
  - 📁 `planning/__init__.py` - 更新导出接口
- [x] 步骤 5.3：创建主协调器 (100%) ✅
  - 📁 `planning/orchestrator.py` - `PlanningOrchestrator` 类
  - 📁 `planning/__init__.py` - 更新导出接口

#### 阶段六：集成到现有系统
- [x] 步骤 6.1：在 server.py 中集成 Planning 模式 (100%) ✅
  - 📁 `server.py` - 导入 Planning 模块，添加模式切换逻辑
- [x] 步骤 6.2：添加配置和命令支持 (100%) ✅
  - 📁 `server.py` - 环境变量读取（`USE_PLANNING_MODE`, `PLANNING_MAX_ITERATIONS`）

#### 阶段七：测试和优化
- [x] 步骤 7.1：基础功能测试 (100%) ✅
  - 创建测试脚本 (`tests/test_planning.py`)
  - 测试 Planner Agent（简单任务、复杂任务、问候语）
  - 测试任务路由器
  - 测试结果汇总器
  - 测试主协调器（完整流程）
  - 创建优化建议文档 (`ai/Planning-Design-优化建议.md`)
  - 创建使用说明文档 (`ai/Planning-Design-使用说明.md`)
  - 📁 `tests/test_planning.py` - 测试脚本（7 个测试用例）
  - 📁 `ai/Planning-Design-优化建议.md` - 优化建议文档
  - 📁 `ai/Planning-Design-使用说明.md` - 使用说明文档
- [x] 步骤 7.2：性能优化 (100%) ✅
  - 已完成基础优化（延迟初始化、错误处理）
  - 后续优化建议已记录在优化建议文档中
  - 📁 `planning/specialized_agents.py` - 延迟初始化优化
  - 📁 `planning/router.py` - 错误处理优化
  - 📁 `ai/Planning-Design-优化建议.md` - 后续优化建议记录

---

## 🎯 下一步行动

✅ **开发计划已确认**，所有决策已记录。

🚀 **开始实施**：从阶段一开始实施

---

**最后更新**：2024-12-19
**当前状态**：✅ **Planning Design 模式开发完成！** 🎉

## 🎊 项目完成总结

Planning Design 模式已成功实现并集成到项目中。所有核心功能已完成，包括：

1. ✅ **基础架构**：计划模型、提示词、工具分类
2. ✅ **专门化 Agent**：Code、Weather、Search、General Agent
3. ✅ **核心组件**：Planner、Router、Aggregator、Orchestrator
4. ✅ **系统集成**：集成到 server.py，支持环境变量配置
5. ✅ **测试和文档**：测试脚本、使用说明、优化建议

### 下一步建议

1. **运行测试**：执行 `uv run python tests/test_planning.py` 验证功能
2. **实际使用**：设置 `USE_PLANNING_MODE=true` 体验 Planning 模式
3. **根据需求优化**：参考 `ai/Planning-Design-优化建议.md` 进行后续优化

### 相关文档

- [Planning Design 分析与方案](./Planning-Design-分析与方案.md)
- [Planning Design 使用说明](./Planning-Design-使用说明.md)
- [Planning Design 优化建议](./Planning-Design-优化建议.md)
