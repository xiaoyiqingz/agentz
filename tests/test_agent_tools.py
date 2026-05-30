import unittest

from prompts.prompt import get_smart_assistant_prompt
from server import create_agent
from config import load_settings
from tools.tools_registry import (
    get_all_tools,
    get_hidden_tool_result_names,
    get_tool_status_labels,
)


class TestAgentTools(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = load_settings(
            {
                "SKILLS_DIR": "./.agents/skills",
                "MCP_CONFIG_PATH": "/tmp/nonexistent-mcp.json",
            }
        )

    def test_legacy_code_editing_tools_are_not_registered_by_default(self):
        agent = create_agent(self.settings)
        tool_names = set(agent._function_toolset.tools.keys())

        self.assertNotIn("read_code_file", tool_names)
        self.assertNotIn("apply_code_patch", tool_names)
        self.assertNotIn("check_and_modify_code", tool_names)
        self.assertNotIn("generate_code", tool_names)

    def test_review_tools_remain_registered(self):
        agent = create_agent(self.settings)
        tool_names = set(agent._function_toolset.tools.keys())

        self.assertIn("read_project_file", tool_names)
        self.assertIn("git_status_summary", tool_names)
        self.assertIn("git_diff_summary", tool_names)
        self.assertIn("git_diff_file", tool_names)
        self.assertIn("search_repo", tool_names)
        self.assertIn("exec_review_command", tool_names)

    def test_review_tools_are_registered_via_tools_registry(self):
        tools = get_all_tools(self.settings)
        tool_names = {
            getattr(tool, "name", getattr(tool, "__name__", None)) for tool in tools
        }

        self.assertIn("read_project_file", tool_names)
        self.assertIn("git_status_summary", tool_names)
        self.assertIn("git_diff_summary", tool_names)
        self.assertIn("git_diff_file", tool_names)
        self.assertIn("search_repo", tool_names)
        self.assertIn("exec_review_command", tool_names)

    def test_tool_status_labels_are_provided_by_tools_registry(self):
        labels = get_tool_status_labels()

        self.assertEqual(labels["read_project_file"], "正在读取项目文件")
        self.assertEqual(labels["git_status_summary"], "正在检查项目变更摘要")
        self.assertEqual(labels["exec_review_command"], "正在执行只读 review 命令")

    def test_hidden_tool_result_names_are_provided_by_tools_registry(self):
        hidden_names = get_hidden_tool_result_names()

        self.assertIn("list_skills", hidden_names)
        self.assertIn("load_skill", hidden_names)
        self.assertIn("read_skill_resource", hidden_names)
        self.assertIn("run_skill_script", hidden_names)

    def test_smart_prompt_no_longer_mentions_legacy_code_editing_tools(self):
        prompt = get_smart_assistant_prompt()

        self.assertNotIn("`read_code_file`", prompt)
        self.assertNotIn("`apply_code_patch`", prompt)
        self.assertNotIn("`check_and_modify_code`", prompt)
        self.assertNotIn("`generate_code`", prompt)


if __name__ == "__main__":
    unittest.main()
