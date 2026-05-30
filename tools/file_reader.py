from __future__ import annotations

from pathlib import Path


def read_file_lines(
    file_path: str | Path,
    start_line: int,
    end_line: int | None = None,
) -> str:
    """
    读取文件的指定行范围。

    当 end_line 为 None 时，默认只读取 start_line 对应的单行。
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    if start_line < 1:
        raise ValueError("起始行号必须大于等于1")

    effective_end_line = start_line if end_line is None else end_line
    if effective_end_line < start_line:
        raise ValueError("结束行号不能小于起始行号")

    selected_lines: list[str] = []
    total_lines = 0

    try:
        with path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                total_lines = line_number
                if line_number < start_line:
                    continue
                if line_number > effective_end_line:
                    break
                selected_lines.append(line)
    except (FileNotFoundError, ValueError):
        raise
    except Exception as exc:
        raise IOError(f"读取文件时发生错误: {exc}") from exc

    if total_lines == 0:
        raise ValueError("文件为空，无法读取指定行")
    if start_line > total_lines:
        raise ValueError("起始行号超出文件范围")
    if effective_end_line > total_lines:
        raise ValueError("结束行号超出文件范围")

    return "".join(selected_lines)
