"""
目录操作工具

提供列出目录下文件和文件夹的功能。
"""

import os
from pathlib import Path
from typing import List, Dict, Any


def list_directory(directory_path: str, include_hidden: bool = False) -> str:
    """
    列出指定目录下的文件和文件夹

    Args:
        directory_path (str): 目录路径（可以是相对路径或绝对路径）
        include_hidden (bool): 是否包含隐藏文件（以.开头的文件/文件夹）。默认为False

    Returns:
        str: 格式化的目录内容列表，包含文件和文件夹信息

    Raises:
        ValueError: 路径无效
        FileNotFoundError: 目录不存在
        PermissionError: 没有读取权限
        IOError: 读取目录时发生错误
    """
    try:
        # 验证路径
        if not directory_path or not directory_path.strip():
            raise ValueError("目录路径不能为空")

        # 规范化路径
        directory_path = os.path.normpath(directory_path)

        # 验证目录是否存在
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"目录不存在: {directory_path}")

        # 验证是否为目录
        if not os.path.isdir(directory_path):
            raise ValueError(f"路径不是目录: {directory_path}")

        # 获取目录内容
        try:
            entries = os.listdir(directory_path)
        except PermissionError:
            raise PermissionError(f"没有权限读取目录: {directory_path}")

        # 分离文件和文件夹
        files = []
        directories = []

        for entry in entries:
            # 过滤隐藏文件
            if not include_hidden and entry.startswith("."):
                continue

            entry_path = os.path.join(directory_path, entry)
            try:
                if os.path.isdir(entry_path):
                    directories.append(entry)
                else:
                    files.append(entry)
            except (OSError, PermissionError):
                # 如果无法访问某个条目，跳过它
                continue

        # 排序
        directories.sort()
        files.sort()

        # 格式化输出
        result_lines = [f"📁 目录: {directory_path}\n"]
        result_lines.append("=" * 60 + "\n")

        if directories:
            result_lines.append(f"📂 文件夹 ({len(directories)} 个):\n")
            for dir_name in directories:
                result_lines.append(f"  📁 {dir_name}/\n")
            result_lines.append("\n")

        if files:
            result_lines.append(f"📄 文件 ({len(files)} 个):\n")
            for file_name in files:
                file_path = os.path.join(directory_path, file_name)
                try:
                    file_size = os.path.getsize(file_path)
                    # 格式化文件大小
                    if file_size < 1024:
                        size_str = f"{file_size} B"
                    elif file_size < 1024 * 1024:
                        size_str = f"{file_size / 1024:.2f} KB"
                    else:
                        size_str = f"{file_size / (1024 * 1024):.2f} MB"
                    result_lines.append(f"  📄 {file_name} ({size_str})\n")
                except (OSError, PermissionError):
                    result_lines.append(f"  📄 {file_name} (无法获取大小)\n")
            result_lines.append("\n")

        if not directories and not files:
            result_lines.append("  (目录为空)\n")

        result_lines.append("=" * 60)

        return "".join(result_lines)

    except (ValueError, FileNotFoundError, PermissionError):
        # 重新抛出已知的异常类型
        raise
    except Exception as e:
        raise IOError(f"读取目录时发生错误: {str(e)}")


def list_directory_safe(directory_path: str, include_hidden: bool = False) -> str:
    """
    安全地列出指定目录下的文件和文件夹（不抛出异常）

    这是 list_directory 的安全版本，不会抛出异常，而是返回错误信息。

    Args:
        directory_path (str): 目录路径
        include_hidden (bool): 是否包含隐藏文件。默认为False

    Returns:
        str: 操作结果描述（成功或错误信息）
    """
    try:
        return list_directory(directory_path, include_hidden)
    except ValueError as e:
        return f"❌ 参数错误: {str(e)}"
    except FileNotFoundError as e:
        return f"❌ 目录不存在: {str(e)}"
    except PermissionError as e:
        return f"❌ 权限错误: {str(e)}"
    except IOError as e:
        return f"❌ 读取错误: {str(e)}"
    except Exception as e:
        return f"❌ 未知错误: {str(e)}"


if __name__ == "__main__":
    """
    命令行接口
    使用方法:
    python directory_tools.py <目录路径> [--include-hidden]

    示例:
    python directory_tools.py .
    python directory_tools.py /Users/zhangzhe/Documents
    python directory_tools.py . --include-hidden
    """
    import sys
    import argparse

    def main():
        parser = argparse.ArgumentParser(
            description="列出指定目录下的文件和文件夹",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
使用示例:
  %(prog)s .                          # 列出当前目录
  %(prog)s /Users/zhangzhe/Documents  # 列出指定目录
  %(prog)s . --include-hidden         # 包含隐藏文件
            """,
        )

        parser.add_argument("directory_path", help="要列出的目录路径")
        parser.add_argument(
            "--include-hidden",
            action="store_true",
            help="包含隐藏文件（以.开头的文件/文件夹）",
        )

        args = parser.parse_args()

        try:
            result = list_directory(args.directory_path, args.include_hidden)
            print(result)
        except Exception as e:
            print(f"❌ 错误: {e}")
            sys.exit(1)

    main()
