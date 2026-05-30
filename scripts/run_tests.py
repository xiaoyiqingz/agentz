#!/usr/bin/env python3
"""
测试运行脚本
用于运行项目中的所有测试
"""

import sys
import unittest
from pathlib import Path

# 添加项目根目录到 Python 路径
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))


def discover_and_run_tests():
    """发现并运行所有测试"""
    test_dir = repo_root / "tests"

    if not test_dir.exists():
        print("测试目录不存在: tests/")
        return False

    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(test_dir), pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


def run_specific_test(test_name):
    """运行特定的测试文件"""
    test_file = repo_root / "tests" / f"test_{test_name}.py"

    if not test_file.exists():
        print(f"测试文件不存在: {test_file}")
        return False

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(f"tests.test_{test_name}")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    print("开始运行测试...")
    print("=" * 50)

    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        print(f"运行测试: {test_name}")
        success = run_specific_test(test_name)
    else:
        print("运行所有测试...")
        success = discover_and_run_tests()

    print("=" * 50)
    if success:
        print("所有测试通过")
        sys.exit(0)
    else:
        print("部分测试失败")
        sys.exit(1)
