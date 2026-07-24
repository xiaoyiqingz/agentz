import unittest
from pathlib import Path

from pydantic_ai_harness.compaction import TieredCompaction
from pydantic_ai_harness.planning import Planning

from config.settings import load_settings
from core.readonly_filesystem import READ_ONLY_FILESYSTEM_TOOLS
from core.server import create_agent
from prompts.prompt import get_smart_assistant_prompt
from tools.register import build_agent_tools


class TestAgentTools(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = load_settings(
            {
                "SKILLS_DIR": "./.agents/skills",
                "MCP_CONFIG_PATH": "/tmp/nonexistent-mcp.json",
            }
        )

    def test_legacy_code_editing_tools_are_not_registered_by_default(self):
        agent = create_agent(self.settings, Path.cwd())
        tool_names = set(agent._function_toolset.tools.keys())

        self.assertNotIn("read_code_file", tool_names)
        self.assertNotIn("apply_code_patch", tool_names)
        self.assertNotIn("check_and_modify_code", tool_names)
        self.assertNotIn("generate_code", tool_names)

    def test_git_readonly_replaces_the_old_project_review_tools(self):
        agent = create_agent(self.settings, Path.cwd())
        tool_names = {
            name
            for toolset in agent.toolsets
            for name in getattr(toolset, "tools", {})
        }

        self.assertIn("git_readonly", tool_names)
        self.assertNotIn("read_project_file", tool_names)
        self.assertNotIn("search_repo", tool_names)
        self.assertNotIn("exec_review_command", tool_names)

    def test_agent_registers_harness_compaction(self):
        agent = create_agent(self.settings, Path.cwd())

        self.assertTrue(
            any(
                isinstance(capability, TieredCompaction)
                for capability in agent.root_capability.capabilities
            )
        )

    def test_agent_registers_harness_planning_by_default(self):
        agent = create_agent(self.settings, Path.cwd())

        self.assertTrue(
            any(
                isinstance(capability, Planning)
                for capability in agent.root_capability.capabilities
            )
        )

    def test_review_tools_are_registered_via_toolset_registry(self):
        registered = build_agent_tools(self.settings)
        local_toolsets = registered.toolsets[:3]
        tool_names = {
            name for toolset in local_toolsets for name in toolset.tools
        }

        self.assertIn("git_readonly", tool_names)

    def test_tool_status_labels_are_provided_by_registry(self):
        labels = build_agent_tools(self.settings).status_labels

        self.assertEqual(labels["read_file"], "正在读取项目文件")
        self.assertEqual(labels["search_files"], "正在搜索项目代码")
        self.assertEqual(labels["git_readonly"], "正在检查 Git 仓库")
        self.assertEqual(labels["write_plan"], "正在更新执行计划")

    def test_readonly_filesystem_exposes_no_write_tools(self):
        self.assertEqual(
            READ_ONLY_FILESYSTEM_TOOLS,
            {"read_file", "list_directory", "search_files", "find_files", "file_info"},
        )

    def test_hidden_tool_result_names_are_provided_by_registry(self):
        hidden_names = build_agent_tools(self.settings).hidden_result_names

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
