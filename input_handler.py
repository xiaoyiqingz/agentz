"""
命令行输入处理器模块

封装 readline 功能，提供增强的命令行输入体验：
- 支持中文删除显示
- 历史记录管理
- 自动保存和加载历史记录
"""

import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

from pydantic_ai import ModelMessagesTypeAdapter
from pydantic_ai.messages import ModelMessage


def _import_readline() -> Optional[object]:
    """
    导入 readline 模块

    Returns:
        readline 模块对象，如果不可用则返回 None
    """
    try:
        import readline

        return readline
    except ImportError:
        # 某些系统可能没有 readline，尝试导入 gnureadline（macOS 上可能需要）
        try:
            import gnureadline as readline  # type: ignore[import-untyped]

            return readline
        except ImportError:
            # 如果都没有，返回 None，但不影响基本功能
            return None


class InputHandler:
    """命令行输入处理器，封装 readline 功能"""

    def __init__(self, project_root: Path):
        """
        初始化输入处理器

        Args:
            project_root: 项目根目录路径，用于确定历史记录文件位置
        """
        self.project_root = project_root
        self.readline_module = _import_readline()
        self.history_file: Optional[Path] = None
        self.message_history_file: Optional[Path] = None
        self._initialized = False

    def is_available(self) -> bool:
        """
        检查 readline 是否可用

        Returns:
            bool: 如果 readline 可用返回 True，否则返回 False
        """
        return self.readline_module is not None

    def initialize(self) -> None:
        """
        初始化 readline 功能

        包括：
        - 设置历史记录文件路径
        - 加载历史记录
        - 配置 readline 选项
        """
        # 设置历史记录文件路径为项目目录下的 data 目录
        data_dir = self.project_root / "data"
        # 确保 data 目录存在
        data_dir.mkdir(exist_ok=True)
        self.history_file = data_dir / "agentz_history"
        self.message_history_file = data_dir / "agentz_message_history.json"

        if not self.is_available():
            self._initialized = True
            return

        try:
            # 尝试加载历史记录
            self.readline_module.read_history_file(str(self.history_file))
        except FileNotFoundError:
            # 历史记录文件不存在，这是正常的（首次运行）
            pass
        except Exception as e:
            # 其他错误（如权限问题）也忽略，不影响程序运行
            print(f"警告：无法加载历史记录文件: {e}")

        # 设置历史记录最大长度
        self.readline_module.set_history_length(1000)

        # 配置 readline 选项以改善中文输入体验
        # 这些设置有助于正确处理多字节字符（如中文）
        if hasattr(self.readline_module, "parse_and_bind"):
            # 启用更好的编辑功能
            self.readline_module.parse_and_bind("set editing-mode emacs")
            # macOS 上可能需要这个设置
            if hasattr(self.readline_module, "set_completer_delims"):
                self.readline_module.set_completer_delims(
                    self.readline_module.get_completer_delims().replace("/", "")
                )

        self._initialized = True

    def load_message_history(self) -> list[ModelMessage]:
        """
        加载 Pydantic AI 消息历史。

        Returns:
            list[ModelMessage]: 反序列化后的消息历史，失败时返回空列表。
        """
        if self.message_history_file is None:
            return []

        try:
            if not self.message_history_file.exists():
                return []
            return ModelMessagesTypeAdapter.validate_json(
                self.message_history_file.read_bytes()
            )
        except Exception as e:
            print(f"警告：无法加载消息历史文件: {e}", file=sys.stderr)
            return []

    def save_message_history(self, messages: Sequence[ModelMessage]) -> None:
        """
        保存 Pydantic AI 消息历史到文件。

        Args:
            messages: 需要持久化的消息列表。
        """
        if self.message_history_file is None:
            return

        try:
            self.message_history_file.parent.mkdir(parents=True, exist_ok=True)
            self.message_history_file.write_bytes(
                ModelMessagesTypeAdapter.dump_json(list(messages), indent=2)
            )
        except Exception as e:
            print(
                f"\n警告：无法保存消息历史到 {self.message_history_file}: {e}",
                file=sys.stderr,
            )

    def save_history(self) -> None:
        """
        保存 readline 历史记录到文件

        如果 readline 不可用或未初始化，则不执行任何操作。
        """
        if not self.is_available() or self.history_file is None:
            return

        try:
            # 确保目录存在
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            # 保存历史记录（即使为空也会创建文件）
            self.readline_module.write_history_file(str(self.history_file))
        except Exception as e:
            # 打印错误信息以便调试，但不影响程序运行
            print(
                f"\n警告：无法保存历史记录到 {self.history_file}: {e}",
                file=sys.stderr,
            )

    def cleanup(self) -> None:
        """
        清理资源，保存历史记录

        通常在程序退出时调用。
        """
        self.save_history()
