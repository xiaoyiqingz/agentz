# 流式 Thinking 功能实现

## 概述

这个实现展示了如何在 Pydantic AI 中实现流式显示 thinking 内容。当模型进行思考时，thinking 内容会实时流式显示，而不是等待完整内容生成后再显示。

## 核心实现

### 1. 导入必要的消息类型

```python
from pydantic_ai.messages import (
    AgentStreamEvent,
    PartStartEvent,
    PartDeltaEvent,
    ThinkingPartDelta,
    ThinkingPart,
    # ... 其他类型
)
```

### 2. 流式事件处理

```python
async for event in result:
    if isinstance(event, PartStartEvent):
        if isinstance(event.part, ThinkingPart):
            thinking_started = True
            thinking_content = event.part.content
            print(f"🤔 Thinking：{thinking_content}", end="", flush=True)
    elif isinstance(event, PartDeltaEvent):
        if isinstance(event.delta, ThinkingPartDelta) and thinking_started:
            if event.delta.content_delta:
                thinking_content += event.delta.content_delta
                print(event.delta.content_delta, end="", flush=True)
```

## 关键特性

### 1. 实时流式显示
- 当模型开始思考时，立即显示 "🤔 Thinking：" 前缀
- 思考内容以增量方式实时显示，无需等待完整内容

### 2. 状态管理
- 使用 `thinking_started` 标志跟踪是否正在显示思考内容
- 确保思考内容和其他内容（如工具调用、回答）正确分隔

### 3. 视觉区分
- 使用表情符号区分不同类型的内容：
  - 🤔 Thinking：思考过程
  - 🔧 调用tool：工具调用
  - 📤 tool返回：工具返回结果
  - 💬 回答：最终回答

## 使用方法

### 运行测试脚本

```bash
python test_thinking_stream.py
```

### 或者直接运行服务器

```bash
python server.py
```

## 技术细节

### 事件类型

1. **PartStartEvent**: 当新的消息部分开始时触发
   - 包含 `ThinkingPart` 时表示开始思考
   - 包含 `ToolCallPart` 时表示开始工具调用

2. **PartDeltaEvent**: 当消息部分有增量更新时触发
   - 包含 `ThinkingPartDelta` 时表示思考内容有新增

### 流式处理流程

1. 监听 `AgentStreamEvent` 事件
2. 检测 `PartStartEvent` 中的 `ThinkingPart`
3. 开始流式显示思考内容
4. 监听 `PartDeltaEvent` 中的 `ThinkingPartDelta`
5. 实时追加新的思考内容
6. 当其他类型事件开始时，结束思考显示

## 注意事项

1. **模型支持**: 不是所有模型都支持 thinking 功能，需要确认你的模型支持
2. **性能**: 流式显示会增加一些处理开销，但提供更好的用户体验
3. **错误处理**: 代码中包含了基本的错误处理，但可以根据需要扩展

## 扩展功能

你可以根据需要扩展这个实现：

1. **自定义格式化**: 修改显示格式和表情符号
2. **日志记录**: 将 thinking 内容记录到日志文件
3. **条件显示**: 根据配置决定是否显示 thinking 内容
4. **多语言支持**: 支持不同语言的提示文本

## 参考文档

- [Pydantic AI Messages API](https://ai.pydantic.dev/api/messages/#pydantic_ai.messages.ThinkingPart)
- [Pydantic AI Streaming](https://ai.pydantic.dev/core-concepts/streaming/)

