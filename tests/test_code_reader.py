#!/usr/bin/env python3
"""
测试 code_reader 模块的功能
"""

import os
import sys
import tempfile
import unittest

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.deprecated.code_reader import read_file_lines, read_file_line


class TestCodeReader(unittest.TestCase):
    """测试 code_reader 模块的测试类"""

    def setUp(self):
        """测试前的准备工作，创建临时测试文件"""
        # 创建临时文件内容
        self.test_content = """#!/usr/bin/env python3
# 这是第一行注释
def hello_world():
    \"\"\"这是一个测试函数\"\"\"
    print("Hello, World!")
    return "success"

class TestClass:
    def __init__(self):
        self.value = 42
    
    def get_value(self):
        return self.value

if __name__ == "__main__":
    # 主程序入口
    hello_world()
    obj = TestClass()
    print(f"Value: {obj.get_value()}")
"""

        # 创建临时文件
        self.temp_file = tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".py"
        )
        self.temp_file.write(self.test_content)
        self.temp_file.close()
        self.temp_file_path = self.temp_file.name

    def tearDown(self):
        """测试后的清理工作"""
        # 删除临时文件
        if os.path.exists(self.temp_file_path):
            os.unlink(self.temp_file_path)

    def test_read_single_line(self):
        """测试读取单行"""
        # 测试读取第1行
        line1 = read_file_line(self.temp_file_path, 1)
        self.assertEqual(line1, "#!/usr/bin/env python3\n")

        # 测试读取第3行
        line3 = read_file_line(self.temp_file_path, 3)
        self.assertEqual(line3, "def hello_world():\n")

        # 测试读取最后一行
        last_line = read_file_line(self.temp_file_path, 19)
        self.assertEqual(last_line, '    print(f"Value: {obj.get_value()}")\n')

    def test_read_multiple_lines(self):
        """测试读取多行"""
        # 测试读取第1-3行
        lines_1_3 = read_file_lines(self.temp_file_path, 1, 3)
        expected = "#!/usr/bin/env python3\n# 这是第一行注释\ndef hello_world():\n"
        self.assertEqual(lines_1_3, expected)

        # 测试读取第4-6行
        lines_4_6 = read_file_lines(self.temp_file_path, 4, 6)
        expected = '    """这是一个测试函数"""\n    print("Hello, World!")\n    return "success"\n'
        self.assertEqual(lines_4_6, expected)

    def test_read_single_line_with_read_file_lines(self):
        """测试使用 read_file_lines 读取单行"""
        # 只指定起始行，不指定结束行
        line5 = read_file_lines(self.temp_file_path, 5, 5)
        self.assertEqual(line5, '    print("Hello, World!")\n')

    def test_read_all_lines(self):
        """测试读取所有行"""
        all_lines = read_file_lines(self.temp_file_path, 1, 19)
        self.assertEqual(all_lines, self.test_content)

    def test_file_not_found(self):
        """测试文件不存在的情况"""
        with self.assertRaises(FileNotFoundError):
            read_file_lines("nonexistent_file.py", 1, 5)

    def test_invalid_line_numbers(self):
        """测试无效的行号参数"""
        # 测试起始行号小于1
        with self.assertRaises(ValueError):
            read_file_lines(self.temp_file_path, 0, 5)

        # 测试起始行号小于1（单行）
        with self.assertRaises(ValueError):
            read_file_line(self.temp_file_path, 0)

        # 测试结束行号小于起始行号
        with self.assertRaises(ValueError):
            read_file_lines(self.temp_file_path, 5, 3)

    def test_line_number_out_of_range(self):
        """测试行号超出文件范围"""
        # 测试起始行号超出范围
        with self.assertRaises(ValueError):
            read_file_lines(self.temp_file_path, 100, 105)

        # 测试结束行号超出范围
        with self.assertRaises(ValueError):
            read_file_lines(self.temp_file_path, 15, 100)

        # 测试单行超出范围
        with self.assertRaises(ValueError):
            read_file_line(self.temp_file_path, 100)

    def test_edge_cases(self):
        """测试边界情况"""
        # 测试读取最后一行
        last_line = read_file_lines(self.temp_file_path, 19, 19)
        self.assertEqual(last_line, '    print(f"Value: {obj.get_value()}")\n')

        # 测试读取第一行
        first_line = read_file_lines(self.temp_file_path, 1, 1)
        self.assertEqual(first_line, "#!/usr/bin/env python3\n")

    def test_empty_file(self):
        """测试空文件"""
        # 创建空文件
        empty_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py")
        empty_file.close()
        empty_file_path = empty_file.name

        try:
            # 测试读取空文件
            with self.assertRaises(ValueError):
                read_file_lines(empty_file_path, 1, 1)
        finally:
            os.unlink(empty_file_path)

    def test_encoding_handling(self):
        """测试编码处理"""
        # 创建包含中文内容的文件
        chinese_content = (
            "#!/usr/bin/env python3\n# 这是中文注释\nprint('你好，世界！')\n"
        )
        chinese_file = tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".py", encoding="utf-8"
        )
        chinese_file.write(chinese_content)
        chinese_file.close()
        chinese_file_path = chinese_file.name

        try:
            # 测试读取包含中文的文件
            content = read_file_lines(chinese_file_path, 1, 3)
            self.assertEqual(content, chinese_content)
        finally:
            os.unlink(chinese_file_path)


def run_performance_test():
    """运行性能测试"""
    import time

    # 创建大文件进行性能测试
    large_content = "#!/usr/bin/env python3\n" + "# 这是测试行\n" * 10000
    large_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py")
    large_file.write(large_content)
    large_file.close()
    large_file_path = large_file.name

    try:
        # 测试读取大文件的性能
        start_time = time.time()
        content = read_file_lines(large_file_path, 1, 1000)
        end_time = time.time()

        print(f"读取1000行代码耗时: {end_time - start_time:.4f}秒")
        print(f"读取的字符数: {len(content)}")

    finally:
        os.unlink(large_file_path)


if __name__ == "__main__":
    print("开始运行 code_reader 测试...")
    print("=" * 50)

    # 运行单元测试
    unittest.main(verbosity=2, exit=False)

    print("\n" + "=" * 50)
    print("运行性能测试...")
    run_performance_test()

    print("\n测试完成！")
