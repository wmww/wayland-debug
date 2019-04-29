import unittest
import gdb_integration

class TestRunner(unittest.TestCase):
    def test_parse_args_no_g(self):
        args = gdb_integration.runner.parse_args(['aaa', '-l', 'bbb'])
        self.assertEquals(args, None)

    def test_parse_args_with_g_simple(self):
        args = gdb_integration.runner.parse_args(['aaa', '-g', 'bbb'])
        self.assertTrue(args)
        self.assertEquals(args.wldbg, ['aaa', '-g'])
        self.assertEquals(args.gdb, ['bbb'])
