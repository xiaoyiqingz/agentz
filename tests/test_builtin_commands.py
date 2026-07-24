import unittest

from commands.builtin_commands import CommandType, process_builtin_command


class TestBuiltinCommands(unittest.TestCase):
    def test_slash_command_is_handled_directly(self):
        handled, result, command_type = process_builtin_command("/help")

        self.assertTrue(handled)
        self.assertEqual(command_type, CommandType.DIRECT)
        self.assertIn("/help", result)

    def test_slash_command_is_converted_to_agent_input(self):
        handled, result, command_type = process_builtin_command("/weather")

        self.assertTrue(handled)
        self.assertEqual(command_type, CommandType.CONVERT)
        self.assertEqual(result, "请告诉我今天的天气情况，并给我一些穿衣建议")

    def test_plain_word_is_not_a_builtin_command(self):
        handled, result, command_type = process_builtin_command("weather")

        self.assertFalse(handled)
        self.assertIsNone(result)
        self.assertEqual(command_type, CommandType.NONE)
