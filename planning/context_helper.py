"""
Context Agent 辅助函数

提供格式化历史记录等功能，帮助 Context Agent 处理历史相关任务。
"""

from typing import List, Optional
from pydantic_ai.messages import ModelMessage, UserPromptPart, SystemPromptPart


def format_history_for_context_agent(
    message_history: Optional[List[ModelMessage]] = None,
) -> str:
    """
    将历史消息格式化为 Context Agent 可以理解的文本格式

    Args:
        message_history: 历史消息列表

    Returns:
        str: 格式化后的历史记录文本
    """
    if not message_history:
        return "暂无历史记录。"

    formatted_parts = []
    turn_number = 0

    for message in message_history:
        # 提取用户输入和助手响应
        user_inputs = []
        assistant_responses = []

        for part in message.parts:
            if isinstance(part, UserPromptPart):
                # 收集所有用户输入
                user_inputs.append(part.content)
            elif isinstance(part, SystemPromptPart):
                # 跳过系统提示词
                continue
            else:
                # 尝试提取 Assistant 响应
                # 对于结构化输出（如 Plan），尝试转换为文本
                if hasattr(part, "content"):
                    content = part.content
                    if isinstance(content, str):
                        assistant_responses.append(content)
                    elif hasattr(content, "model_dump"):
                        # Pydantic 模型，转换为 JSON 字符串
                        try:
                            assistant_responses.append(
                                f"[结构化数据] {content.model_dump_json(indent=2)}"
                            )
                        except:
                            assistant_responses.append(str(content))
                    else:
                        assistant_responses.append(str(content))
                elif hasattr(part, "text"):
                    assistant_responses.append(part.text)
                elif hasattr(part, "__str__"):
                    assistant_responses.append(str(part))

        # 如果找到用户输入，记录这一轮对话
        if user_inputs:
            turn_number += 1
            formatted_parts.append(f"第 {turn_number} 轮对话：")

            # 合并多个用户输入（如果有）
            user_text = " ".join(user_inputs)
            formatted_parts.append(f"用户：{user_text}")

            if assistant_responses:
                # 合并多个响应（如果有）
                response_text = "\n".join(assistant_responses)
                # 限制响应长度，避免过长
                if len(response_text) > 1000:
                    response_text = response_text[:1000] + "\n...（内容已截断）"
                formatted_parts.append(f"助手：{response_text}")
            else:
                formatted_parts.append("助手：（已响应，但内容无法提取）")

            formatted_parts.append("")  # 空行分隔

    if not formatted_parts:
        return "历史记录为空或格式无法识别。"

    return "\n".join(formatted_parts)
