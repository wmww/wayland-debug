import unittest
from frontends.tui import parse_command

commands = [['-g', '--gdb'], ['-r', '--run']]

class TestParseCommand(unittest.TestCase):
    def test_without_command_arg(self):
        args = parse_command(['aaa', '-l', 'bbb'], commands)
        self.assertEqual(args.wayland_debug_args, ['aaa', '-l', 'bbb'])
        self.assertEqual(args.command, '')
        self.assertEqual(args.command_args, [])

    def test_with_g_arg(self):
        args = parse_command(['aaa', '-g', 'bbb'], commands)
        self.assertTrue(args)
        self.assertEqual(args.wayland_debug_args, ['aaa'])
        self.assertEqual(args.command, 'g')
        self.assertEqual(args.command_args, ['bbb'])

    def test_with_gdb_arg(self):
        args = parse_command(['aaa', '--gdb', 'bbb'], commands)
        self.assertTrue(args)
        self.assertEqual(args.wayland_debug_args, ['aaa'])
        self.assertEqual(args.command, 'g')
        self.assertEqual(args.command_args, ['bbb'])

    def test_with_more_args_before_and_after_g(self):
        args = parse_command(['something.py', '-f', 'aaa', '-g', 'bbb', '--nh'], commands)
        self.assertTrue(args)
        self.assertEqual(args.wayland_debug_args, ['something.py', '-f', 'aaa'])
        self.assertEqual(args.command, 'g')
        self.assertEqual(args.command_args, ['bbb', '--nh'])

    def test_that_parse_args_ignores_subsequent_gs(self):
        args = parse_command(['aaa', '-g', 'bbb', '-g'], commands)
        self.assertTrue(args)
        self.assertEqual(args.wayland_debug_args, ['aaa'])
        self.assertEqual(args.command, 'g')
        self.assertEqual(args.command_args, ['bbb', '-g'])

    def test_g_detected_when_part_of_compound_arg(self):
        args = parse_command(['aaa', '-vCg', 'bbb'], commands)
        self.assertTrue(args)
        self.assertEqual(args.wayland_debug_args, ['aaa', '-vC'])
        self.assertEqual(args.command, 'g')
        self.assertEqual(args.command_args, ['bbb'])

    def test_with_r_arg(self):
        args = parse_command(['aaa', '-r', 'bbb'], commands)
        self.assertTrue(args)
        self.assertEqual(args.wayland_debug_args, ['aaa'])
        self.assertEqual(args.command, 'r')
        self.assertEqual(args.command_args, ['bbb'])

    def test_that_parse_args_raises_error_when_g_in_middle_of_compound_arg(self):
        with self.assertRaises(RuntimeError):
            args = parse_command(['aaa', '-vgC', 'bbb'], commands)
