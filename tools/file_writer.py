"""
文件写入工具

提供将字符串内容（代码、markdown等）写入指定文件的功能。
自动创建目录（如果不存在）。
"""

import os
from pathlib import Path


def write_file(file_path: str, content: str, overwrite: bool = True) -> str:
    """
    将字符串内容写入指定文件

    支持写入代码、markdown等任何文本内容。
    如果目录不存在，会自动创建。

    Args:
        file_path (str): 目标文件路径（可以是相对路径或绝对路径）
        content (str): 要写入的内容字符串
        overwrite (bool): 如果文件已存在，是否覆盖。默认为True

    Returns:
        str: 操作结果描述

    Raises:
        ValueError: 文件路径无效
        PermissionError: 没有写入权限
        IOError: 文件写入错误
    """
    try:
        # 验证文件路径
        if not file_path or not file_path.strip():
            raise ValueError("文件路径不能为空")

        # 规范化路径
        file_path = os.path.normpath(file_path)

        # 获取目录路径
        directory = os.path.dirname(file_path)

        # 如果目录不为空且不存在，则创建目录
        if directory and not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
            except OSError as e:
                raise IOError(f"无法创建目录 {directory}: {str(e)}")

        # 检查文件是否已存在
        if os.path.exists(file_path) and not overwrite:
            return f"⚠️ 文件已存在且未设置覆盖: {file_path}"

        # 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        # 返回成功信息
        file_size = len(content.encode("utf-8"))
        return f"✅ 成功写入文件: {file_path} (大小: {file_size} 字节)"

    except (ValueError, PermissionError):
        # 重新抛出已知的异常类型
        raise
    except Exception as e:
        raise IOError(f"写入文件时发生错误: {str(e)}")


def write_file_safe(file_path: str, content: str, overwrite: bool = True) -> str:
    """
    安全地将字符串内容写入指定文件（不抛出异常）

    这是 write_file 的安全版本，不会抛出异常，而是返回错误信息。

    Args:
        file_path (str): 目标文件路径
        content (str): 要写入的内容字符串
        overwrite (bool): 如果文件已存在，是否覆盖。默认为True

    Returns:
        str: 操作结果描述（成功或错误信息）
    """
    try:
        return write_file(file_path, content, overwrite)
    except ValueError as e:
        return f"❌ 参数错误: {str(e)}"
    except PermissionError as e:
        return f"❌ 权限错误: {str(e)}"
    except IOError as e:
        return f"❌ 写入错误: {str(e)}"
    except Exception as e:
        return f"❌ 未知错误: {str(e)}"


if __name__ == "__main__":
    """
    命令行接口
    使用方法:
    python file_writer.py <文件路径> <内容>

    示例:
    python file_writer.py test.py "print('hello')"
    python file_writer.py docs/readme.md "# 标题\n\n这是内容"
    """
    import sys
    import argparse

    def main():
        parser = argparse.ArgumentParser(
            description="将字符串内容写入指定文件",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
使用示例:
  %(prog)s test.py "print('hello')"
  %(prog)s docs/readme.md "# 标题\\n\\n这是内容"
  %(prog)s --no-overwrite existing.txt "新内容"
            """,
        )

        parser.add_argument("file_path", help="目标文件路径")
        parser.add_argument("content", help="要写入的内容")
        parser.add_argument(
            "--no-overwrite",
            action="store_true",
            help="如果文件已存在，不覆盖",
        )

        args = parser.parse_args()

        try:
            result = write_file(
                args.file_path, args.content, overwrite=not args.no_overwrite
            )
            print(result)
        except Exception as e:
            print(f"❌ 错误: {e}")
            sys.exit(1)

    main()
