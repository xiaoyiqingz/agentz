"""
输出格式化工具

使用 rich 库美化输出，支持 Markdown 渲染和语法高亮。
"""

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from typing import Optional, Union
import time


class MarkdownStreamFormatter:
    """Markdown 流式输出格式化器"""

    def __init__(self):
        self.console = Console()
        self.buffer = ""
        self.last_render_length = 0

    def add_text(self, text: str) -> None:
        """
        添加文本到缓冲区

        Args:
            text: 要添加的文本
        """
        self.buffer += text

    def render(self, final: bool = False) -> None:
        """
        渲染缓冲区中的 Markdown 内容

        Args:
            final: 是否为最终渲染（流式结束时）
        """
        if not self.buffer.strip() and not final:
            return

        try:
            # 使用 rich 渲染 Markdown
            markdown = Markdown(self.buffer, code_theme="monokai")
            self.console.print(markdown, end="")
        except Exception:
            # 如果渲染失败，直接输出原始文本
            self.console.print(self.buffer, end="")

    def flush(self) -> None:
        """刷新缓冲区并渲染"""
        if self.buffer:
            self.render(final=True)
            self.buffer = ""

    def reset(self) -> None:
        """重置缓冲区"""
        self.buffer = ""
        self.last_render_length = 0


class SimpleMarkdownFormatter:
    """
    简单的 Markdown 格式化器

    用于流式输出，累积内容并在流式输出结束时渲染为美观的 Markdown。
    流式输出过程中显示原始文本，结束时渲染为格式化的 Markdown。
    """

    def __init__(self, show_stream: bool = True):
        """
        初始化格式化器

        Args:
            show_stream: 是否在流式输出时显示原始文本（默认 True）
        """
        self.console = Console()
        self.buffer = ""
        self.show_stream = show_stream

    def add_chunk(self, chunk: str) -> None:
        """
        添加文本块

        Args:
            chunk: 文本块
        """
        self.buffer += chunk
        # 如果启用流式显示，实时输出原始文本
        if self.show_stream:
            self.console.print(chunk, end="", markup=False)

    def render_if_needed(self) -> None:
        """流式输出过程中的占位方法（实际渲染在 render_final 中完成）"""
        pass

    def render_final(self) -> None:
        """最终渲染所有内容为格式化的 Markdown"""
        if not self.buffer:
            return

        # 如果启用了流式显示，需要清除之前输出的原始文本
        # 但由于流式输出已经完成，这里直接渲染格式化版本
        if self.show_stream:
            # 清除之前输出的原始文本（通过换行和重新渲染）
            self.console.print()  # 换行

        try:
            # 使用 rich 渲染 Markdown，支持语法高亮
            markdown = Markdown(self.buffer, code_theme="monokai")
            self.console.print(markdown)
        except Exception as e:
            # 如果渲染失败，直接输出原始文本
            self.console.print(self.buffer)

    def reset(self) -> None:
        """重置缓冲区"""
        self.buffer = ""


class LiveMarkdownFormatter:
    """
    使用 rich.live.Live 实现的实时 Markdown 格式化器

    在流式输出过程中实时渲染 Markdown，兼顾流式效果和格式化显示。
    """

    def __init__(self):
        """初始化格式化器"""
        self.console = Console()
        self.buffer = ""
        self.live: Optional[Live] = None
        self.last_update_time = 0.0

    def add_chunk(self, chunk: str) -> None:
        """
        添加文本块到缓冲区

        Args:
            chunk: 文本块
        """
        self.buffer += chunk

    def _update_display(self) -> None:
        """更新 Live 显示"""
        if not self.buffer.strip() and not self.live:
            return

        # 如果 Live 还未启动，先启动它
        if self.live is None:
            self.live = Live(
                Markdown("", code_theme="monokai"),
                console=self.console,
                refresh_per_second=30,  # 提高刷新率以获得更流畅的效果
                transient=False,  # 不自动清除，保留最终内容
            )
            self.live.start()

        # 更新显示内容
        try:
            markdown = Markdown(self.buffer, code_theme="monokai")
            self.live.update(markdown)
        except Exception:
            # 如果渲染失败，显示原始文本
            self.live.update(self.buffer)

    def render_if_needed(self) -> None:
        """流式输出过程中实时更新显示（限制更新频率）"""
        # 限制更新频率，避免过于频繁的渲染
        current_time = time.time()
        if current_time - self.last_update_time > 0.1:  # 最多每 0.1 秒更新一次
            self._update_display()
            self.last_update_time = current_time

    def render_final(self) -> None:
        """最终渲染所有内容"""
        if not self.buffer:
            if self.live:
                self.live.stop()
                self.live = None
            return

        # 强制更新一次显示（忽略时间限制）
        if self.live is None:
            self._update_display()
        else:
            # 直接更新，确保最终内容显示
            try:
                markdown = Markdown(self.buffer, code_theme="monokai")
                self.live.update(markdown)
            except Exception:
                self.live.update(self.buffer)

        # 停止 Live 显示，保留最终内容
        if self.live:
            self.live.stop()
            self.live = None

    def reset(self) -> None:
        """重置缓冲区"""
        if self.live:
            self.live.stop()
            self.live = None
        self.buffer = ""
        self.last_update_time = 0.0


class UnifiedFormatter:
    """
    统一的输出格式化器

    封装所有美化输出功能，包括：
    - 用户输入提示
    - 各种消息输出（工具调用、返回、系统提示等）
    - 分隔线和布局
    - Markdown 流式输出
    """

    def __init__(self, use_live: bool = True):
        """
        初始化统一格式化器

        Args:
            use_live: 是否使用 Live 实时渲染 Markdown（默认 True）
        """
        self.console = Console()
        # 内部包含 Markdown 流式格式化器
        if use_live:
            self.markdown_formatter: Union[
                LiveMarkdownFormatter, SimpleMarkdownFormatter
            ] = LiveMarkdownFormatter()
        else:
            self.markdown_formatter = SimpleMarkdownFormatter(show_stream=True)

    def print_tool_call(self, tool_name: str) -> None:
        """
        打印工具调用信息（替代 console.print）

        Args:
            tool_name: 工具名称
        """
        self.console.print(
            f"[bold yellow]🔧 调用tool：[/bold yellow][cyan]{tool_name}[/cyan]"
        )

    def print_tool_result(self, content: str) -> None:
        """
        打印工具返回结果（替代 console.print）

        Args:
            content: 返回内容
        """
        self.console.print(
            f"[bold green]📤 tool返回：[/bold green][dim]{content}[/dim]"
        )

    def print_system_prompt(self, content: str) -> None:
        """
        打印系统提示（替代 console.print）

        Args:
            content: 系统提示内容
        """
        self.console.print(
            f"[bold magenta]💬 系统提示：[/bold magenta][dim]{content}[/dim]"
        )

    def print_user_input(self, content: str) -> None:
        """
        打印用户输入（替代 console.print）

        Args:
            content: 用户输入内容
        """
        self.console.print(f"[bold blue]👤 用户输入：[/bold blue][dim]{content}[/dim]")

    def print_unknown(self, obj_type: type) -> None:
        """
        打印未知类型（替代 console.print）

        Args:
            obj_type: 未知对象的类型
        """
        self.console.print(f"[dim]未知类型：[/dim][yellow]{obj_type}[/yellow]")

    def print_blank_line(self) -> None:
        """
        打印空行（替代 console.print()）
        """
        self.console.print()

    def print_rule(
        self, text: str = "[bold cyan]AI 响应[/bold cyan]", style: str = "cyan"
    ) -> None:
        """
        打印分隔线（替代 console.rule）

        Args:
            text: 分隔线中央的文本，支持 rich markup
            style: 分隔线样式
        """
        self.console.rule(text, style=style)

    def add_chunk(self, chunk: str) -> None:
        """
        添加文本块到 Markdown 流式输出缓冲区

        Args:
            chunk: 文本块
        """
        self.markdown_formatter.add_chunk(chunk)

    def render_if_needed(self) -> None:
        """流式输出过程中实时更新显示（限制更新频率）"""
        self.markdown_formatter.render_if_needed()

    def render_final(self) -> None:
        """最终渲染所有 Markdown 内容"""
        self.markdown_formatter.render_final()

    def reset(self) -> None:
        """重置 Markdown 格式化器缓冲区"""
        self.markdown_formatter.reset()


def create_formatter(
    use_live: bool = True,
) -> UnifiedFormatter:
    """
    创建统一的格式化器实例

    Args:
        use_live: 是否使用 Live 实时渲染（默认 True）
                 - True: 使用 LiveMarkdownFormatter，流式输出时实时渲染 Markdown（推荐）
                 - False: 使用 SimpleMarkdownFormatter，流式输出时显示原始文本，结束时渲染 Markdown

    Returns:
        UnifiedFormatter 实例，提供统一的输出美化接口
    """
    return UnifiedFormatter(use_live=use_live)
