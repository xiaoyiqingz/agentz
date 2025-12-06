# Planning Design 模式使用说明

## 📖 简介

Planning Design 模式是一种将复杂任务分解为可管理子任务的 Agent 设计模式。通过任务规划、多 Agent 编排和结果汇总，可以更有效地处理复杂任务。

## 🚀 快速开始

### 1. 启用 Planning 模式

在 `.env` 文件中设置：

```bash
USE_PLANNING_MODE=true
PLANNING_MAX_ITERATIONS=1
```

### 2. 运行程序

```bash
uv run python main.py
```

如果 Planning 模式已启用，启动时会显示：
```
✓ Planning Design 模式已启用
```

### 3. 使用示例

#### 简单任务（单一 Agent）
```
> 查询北京天气
```

Planner 会识别这是一个天气查询任务，分配给 Weather Agent 处理。

#### 复杂任务（多 Agent）
```
> 查询北京天气，然后生成一个 Python 脚本来显示天气
```

Planner 会分解为：
1. 查询北京天气（Weather Agent）
2. 生成显示天气的 Python 脚本（Code Agent）

#### 问候语
```
> 你好
```

Planner 会识别为问候语，直接使用 General Agent 处理。

## ⚙️ 配置选项

### 环境变量

| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| `USE_PLANNING_MODE` | 是否启用 Planning 模式 | `false` | `true` |
| `PLANNING_MAX_ITERATIONS` | 最大迭代次数 | `1` | `3` |

### 模式切换

**当前版本**：通过环境变量控制

**后续版本**：将支持运行时命令切换：
- `planning on` - 启用 Planning 模式
- `planning off` - 禁用 Planning 模式
- `planning status` - 查看当前状态

## 🏗️ 架构说明

### 工作流程

```
用户输入
  ↓
Planner Agent（生成结构化计划）
  ↓
任务分解（识别子任务和分配的 Agent）
  ↓
任务路由（根据 assigned_agent 分发任务）
  ↓
专门化 Agent 执行（串行）
  ↓
结果汇总（生成最终响应）
  ↓
返回给用户
```

### 专门化 Agent

| Agent 类型 | 用途 | 工具 |
|-----------|------|------|
| `code_agent` | 代码生成、修改、文件操作 | 代码相关工具 |
| `weather_agent` | 天气查询、时间查询 | 天气/时间工具 |
| `search_agent` | 网络搜索、信息查询 | 搜索工具 |
| `general_agent` | 通用对话、问答 | 所有工具 |
| `default_agent` | 兜底 Agent | 所有工具 |

## 📝 使用建议

### 适合使用 Planning 模式的场景

1. **复杂任务**：需要多个步骤或多个工具的任务
2. **多领域任务**：涉及代码、搜索、天气等多个领域的任务
3. **需要明确步骤的任务**：希望看到任务分解和执行过程的任务

### 适合使用单一 Agent 模式的场景

1. **简单任务**：单一工具可以完成的简单任务
2. **需要流式输出**：希望实时看到响应过程
3. **对话场景**：多轮对话、上下文保持

## 🔍 调试和监控

### 日志

Planning 模式使用 Logfire 进行日志记录。日志文件位置请查看 `pyproject.toml` 配置。

### 测试

运行测试脚本：

```bash
uv run python tests/test_planning.py
```

## ❓ 常见问题

### Q: Planning 模式和单一 Agent 模式有什么区别？

**A**: 
- Planning 模式：先规划再执行，适合复杂任务，可以看到任务分解过程
- 单一 Agent 模式：直接执行，适合简单任务，支持流式输出

### Q: 如何选择使用哪种模式？

**A**: 
- 简单任务：使用单一 Agent 模式（默认）
- 复杂任务：启用 Planning 模式
- 可以通过环境变量或后续的命令切换

### Q: Planning 模式支持流式输出吗？

**A**: 
- 当前版本：不支持（第一阶段实现）
- 后续版本：将支持流式输出，显示每个子任务的执行过程

### Q: 如果某个子任务失败怎么办？

**A**: 
- 当前策略：继续执行其他任务，最后在汇总中说明失败的任务
- 后续版本：将支持重试机制

## 📚 相关文档

- [Planning Design 分析与方案](./Planning-Design-分析与方案.md)
- [Planning Design 开发计划](./Planning-Design-开发计划.md)
- [Planning Design 优化建议](./Planning-Design-优化建议.md)

---

**最后更新**：2024-12-19
