# 测试目录

这个目录包含项目的所有单元测试文件。

## 📁 目录结构

```
tests/
├── __init__.py              # 使tests成为Python包
├── test_code_reader.py      # code_reader模块的测试
└── README.md               # 本说明文件
```

## 🚀 运行测试

### ⚡ 快速开始

**最简单的运行方式**（推荐）:
```bash
# 在项目根目录运行所有测试
uv run python scripts/run_tests.py
```

### 为什么使用 uv？

`uv` 是一个快速的Python包管理器和项目管理工具，具有以下优势：
- ⚡ **速度快**: 比 pip 快 10-100 倍
- 🔒 **依赖管理**: 自动管理虚拟环境和依赖
- 📦 **项目隔离**: 每个项目独立的依赖环境
- 🛠️ **工具集成**: 内置测试、构建等工具支持

### 使用 uv 运行测试（推荐）
```bash
# 运行所有测试
uv run python scripts/run_tests.py

# 运行特定测试文件
uv run python scripts/run_tests.py code_reader

# 直接使用unittest运行所有测试
uv run python -m unittest discover tests/

# 运行特定测试文件
uv run python -m unittest tests.test_code_reader

# 运行特定测试方法
uv run python -m unittest tests.test_code_reader.TestCodeReader.test_read_single_line
```

### 使用标准Python运行测试
```bash
# 使用测试运行脚本
python3 scripts/run_tests.py

# 或者直接使用unittest
python3 -m unittest discover tests/
```

### 运行特定测试
```bash
# 运行特定测试文件
python3 scripts/run_tests.py code_reader

# 或者直接运行特定测试文件
python3 -m unittest tests.test_code_reader
```

### 运行特定测试方法
```bash
python3 -m unittest tests.test_code_reader.TestCodeReader.test_read_single_line
```

## 📋 测试文件命名规范

- 测试文件以 `test_` 开头
- 测试类以 `Test` 开头
- 测试方法以 `test_` 开头

## 🔧 添加新测试

1. 在 `tests/` 目录下创建新的测试文件
2. 文件名格式：`test_<模块名>.py`
3. 继承 `unittest.TestCase`
4. 使用 `unittest` 的断言方法

## 📝 测试示例

```python
import unittest
from commands.your_module import your_function

class TestYourModule(unittest.TestCase):
    def test_your_function(self):
        result = your_function("input")
        self.assertEqual(result, "expected_output")
```

## 🎯 测试覆盖率

当前测试覆盖：
- ✅ 正常功能测试
- ✅ 异常情况测试
- ✅ 边界条件测试
- ✅ 性能测试

## 🔧 uv 完整使用指南

### 安装 uv
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 或者使用 pip
pip install uv
```

### 项目初始化
```bash
# 在项目根目录初始化 uv 项目
uv init

# 添加依赖
uv add pytest  # 添加测试依赖
uv add requests  # 添加其他依赖
```

### 运行测试的完整命令

**强烈推荐**: 使用 `scripts/run_tests.py` 脚本（最简单可靠）

```bash
# 1. 运行所有测试
uv run python scripts/run_tests.py

# 2. 运行特定测试文件
uv run python scripts/run_tests.py code_reader
```

**注意**: 如果遇到路径问题，可以使用绝对路径：
```bash
# 使用绝对路径运行测试
uv run python /path/to/your/project/scripts/run_tests.py
uv run python /path/to/your/project/scripts/run_tests.py code_reader
```

**其他方式**: 直接运行测试文件

```bash
# 3. 直接运行测试文件（使用绝对路径）
uv run python /path/to/your/project/tests/test_code_reader.py
```

**高级用法**: 测试覆盖率报告

```bash
# 4. 生成测试覆盖率报告（需要安装 coverage）
uv add coverage
uv run coverage run tests/test_code_reader.py
uv run coverage report
uv run coverage html  # 生成HTML报告
```

### 如果不在项目根目录运行
```bash
# 使用绝对路径运行测试
uv run python /path/to/your/project/scripts/run_tests.py

# 使用绝对路径运行特定测试文件
uv run python /path/to/your/project/tests/test_code_reader.py
```

### uv 的其他有用命令
```bash
# 查看项目依赖
uv tree

# 同步依赖
uv sync

# 运行脚本
uv run python main.py

# 添加开发依赖
uv add --dev pytest pytest-cov

# 查看已安装的包
uv pip list
```

### 与 CI/CD 集成
```yaml
# GitHub Actions 示例
- name: Run tests with uv
  run: |
    curl -LsSf https://astral.sh/uv/install.sh | sh
    uv run python scripts/run_tests.py
```
