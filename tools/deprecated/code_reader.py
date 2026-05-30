def read_file_lines(file_path: str, start_line: int, end_line: int = None) -> str:
    """
    读取指定文件的指定行数代码

    Args:
        file_path (str): 文件路径
        start_line (int): 起始行号（从1开始）
        end_line (int, optional): 结束行号（从1开始），如果为None则只返回start_line行

    Returns:
        str: 指定行数的代码内容

    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 行号参数无效
        IOError: 文件读取错误
    """
    try:
        # 验证文件是否存在
        import os

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 验证行号参数
        if start_line < 1:
            raise ValueError("起始行号必须大于等于1")

        if end_line is not None and end_line < start_line:
            raise ValueError("结束行号不能小于起始行号")

        # 读取文件
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        total_lines = len(lines)
        if total_lines == 0:
            raise ValueError("文件为空，无法读取指定行")
        if start_line > total_lines:
            raise ValueError("起始行号超出文件范围")
        if end_line is not None and end_line > total_lines:
            raise ValueError("结束行号超出文件范围")

        # 提取指定行数（转换为0基索引）
        start_idx = start_line - 1
        end_idx = end_line if end_line is None else end_line

        # 返回指定行数的代码
        selected_lines = lines[start_idx:end_idx]
        return "".join(selected_lines)

    except (FileNotFoundError, ValueError):
        # 重新抛出已知的异常类型
        raise
    except Exception as e:
        raise IOError(f"读取文件时发生错误: {str(e)}")


def read_file_line(file_path: str, line_number: int) -> str:
    """
    读取指定文件的单行代码

    Args:
        file_path (str): 文件路径
        line_number (int): 行号（从1开始）

    Returns:
        str: 指定行的代码内容（包含换行符）
    """
    return read_file_lines(file_path, line_number, line_number)


if __name__ == "__main__":
    """
    命令行接口
    使用方法:
    python code_reader.py <文件路径> <起始行号> [结束行号]

    示例:
    python code_reader.py main.py 1 10    # 读取第1-10行
    python code_reader.py main.py 5       # 读取第5行
    python code_reader.py main.py 1 -1    # 读取第1行到最后一行
    """
    import sys
    import argparse

    def main():
        parser = argparse.ArgumentParser(
            description="读取指定文件的指定行数代码",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
使用示例:
  %(prog)s main.py 1 10     # 读取第1-10行
  %(prog)s main.py 5        # 读取第5行
  %(prog)s main.py 1 -1     # 读取第1行到最后一行
  %(prog)s main.py 10 20    # 读取第10-20行
            """,
        )

        parser.add_argument("file_path", help="要读取的文件路径")
        parser.add_argument("start_line", type=int, help="起始行号（从1开始）")
        parser.add_argument(
            "end_line",
            type=int,
            nargs="?",
            default=None,
            help="结束行号（从1开始），可选。使用-1表示到最后一行",
        )

        args = parser.parse_args()

        try:
            # 处理结束行号
            end_line = args.end_line
            if end_line == -1:
                end_line = None  # 读取到最后一行
            elif end_line is not None and end_line < args.start_line:
                print(
                    f"❌ 错误: 结束行号 {end_line} 不能小于起始行号 {args.start_line}"
                )
                sys.exit(1)

            # 读取文件内容
            content = read_file_lines(args.file_path, args.start_line, end_line)

            # 显示结果
            if end_line is None:
                if args.end_line == -1:
                    print(
                        f"📄 文件: {args.file_path} (第 {args.start_line} 行到最后一行)"
                    )
                else:
                    print(f"📄 文件: {args.file_path} (第 {args.start_line} 行)")
            else:
                print(f"📄 文件: {args.file_path} (第 {args.start_line}-{end_line} 行)")

            print("=" * 50)
            print(content, end="")  # end="" 避免额外的换行符
            print("=" * 50)

        except FileNotFoundError as e:
            print(f"❌ 文件错误: {e}")
            sys.exit(1)
        except ValueError as e:
            print(f"❌ 参数错误: {e}")
            sys.exit(1)
        except IOError as e:
            print(f"❌ 读取错误: {e}")
            sys.exit(1)
        except KeyboardInterrupt:
            print("\n👋 操作已取消")
            sys.exit(0)
        except Exception as e:
            print(f"❌ 未知错误: {e}")
            sys.exit(1)

    main()
