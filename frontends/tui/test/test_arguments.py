import unittest
from frontends.tui.arguments import _split_command

commands = [['-g', '--gdb'], ['-r', '--run']]

class TestSplitCommand(unittest.TestCase):
    def test_without_command_arg(self):
        args = _split_command(['aaa', '-l', 'bbb'], commands)
        wayland_debug_args, command_id, command_args = args
        self.assertEqual(wayland_debug_args, ['aaa', '-l', 'bbb'])
        self.assertEqual(command_id, '')
        self.assertEqual(command_args, [])

    def test_with_g_arg(self):
        args = _split_command(['aaa', '-g', 'bbb'], commands)
        wayland_debug_args, command_id, command_args = args
        self.assertEqual(wayland_debug_args, ['aaa'])
        self.assertEqual(command_id, 'g')
        self.assertEqual(command_args, ['bbb'])

    def test_with_gdb_arg(self):
        args = _split_command(['aaa', '--gdb', 'bbb'], commands)
        wayland_debug_args, command_id, command_args = args
        self.assertEqual(wayland_debug_args, ['aaa'])
        self.assertEqual(command_id, 'g')
        self.assertEqual(command_args, ['bbb'])

    def test_with_more_args_before_and_after_g(self):
        args = _split_command(['something.py', '-f', 'aaa', '-g', 'bbb', '--nh'], commands)
        wayland_debug_args, command_id, command_args = args
        self.assertEqual(wayland_debug_args, ['something.py', '-f', 'aaa'])
        self.assertEqual(command_id, 'g')
        self.assertEqual(command_args, ['bbb', '--nh'])

    def test_that_parse_args_ignores_subsequent_gs(self):
        args = _split_command(['aaa', '-g', 'bbb', '-g'], commands)
        wayland_debug_args, command_id, command_args = args
        self.assertEqual(wayland_debug_args, ['aaa'])
        self.assertEqual(command_id, 'g')
        self.assertEqual(command_args, ['bbb', '-g'])

    def test_g_detected_when_part_of_compound_arg(self):
        args = _split_command(['aaa', '-vCg', 'bbb'], commands)
        wayland_debug_args, command_id, command_args = args
        self.assertEqual(wayland_debug_args, ['aaa', '-vC'])
        self.assertEqual(command_id, 'g')
        self.assertEqual(command_args, ['bbb'])

    def test_with_r_arg(self):
        args = _split_command(['aaa', '-r', 'bbb'], commands)
        wayland_debug_args, command_id, command_args = args
        self.assertEqual(wayland_debug_args, ['aaa'])
        self.assertEqual(command_id, 'r')
        self.assertEqual(command_args, ['bbb'])

    def test_that_parse_args_raises_error_when_g_in_middle_of_compound_arg(self):
        with self.assertRaises(RuntimeError):
            args = _split_command(['aaa', '-vgC', 'bbb'], commands)
