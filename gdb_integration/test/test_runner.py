import unittest
import gdb_integration

class TestRunner(unittest.TestCase):
    def test_parse_args_no_g(self):
        args = gdb_integration.runner.parse_args(['aaa', '-l', 'bbb'])
        self.assertEquals(args, None)

    def test_parse_args_g_simple(self):
        args = gdb_integration.runner.parse_args(['aaa', '-g', 'bbb'])
        self.assertTrue(args)
        self.assertEquals(args.wldbg, ['aaa'])
        self.assertEquals(args.gdb, ['bbb'])

    def test_parse_args_g_simple(self):
        args = gdb_integration.runner.parse_args(['aaa', '--gdb', 'bbb'])
        self.assertTrue(args)
        self.assertEquals(args.wldbg, ['aaa'])
        self.assertEquals(args.gdb, ['bbb'])

    def test_parse_args_g_more_args(self):
        args = gdb_integration.runner.parse_args(['something.py', '-f', 'aaa', '-g', 'bbb', '--nh'])
        self.assertTrue(args)
        self.assertEquals(args.wldbg, ['something.py', '-f', 'aaa'])
        self.assertEquals(args.gdb, ['bbb', '--nh'])

    def test_parse_args_uses_first_g(self):
        args = gdb_integration.runner.parse_args(['aaa', '-g', 'bbb', '-g'])
        self.assertTrue(args)
        self.assertEquals(args.wldbg, ['aaa'])
        self.assertEquals(args.gdb, ['bbb', '-g'])

    def test_parse_args_g_in_multi_arg(self):
        args = gdb_integration.runner.parse_args(['aaa', '-vCg', 'bbb'])
        self.assertTrue(args)
        self.assertEquals(args.wldbg, ['aaa', '-vC'])
        self.assertEquals(args.gdb, ['bbb'])

    def test_parse_args_g_in_multi_arg_not_at_end_throws(self):
        with self.assertRaises(RuntimeError):
            args = gdb_integration.runner.parse_args(['aaa', '-vgC', 'bbb'])

