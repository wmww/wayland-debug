import unittest
from backends.gdb_plugin import runner

class TestRunnerParseArgs(unittest.TestCase):
    def test_parse_args_no_g(self):
        args = runner.parse_args(['aaa', '-l', 'bbb'])
        self.assertEqual(args, None)

    def test_parse_args_g_simple(self):
        args = runner.parse_args(['aaa', '-g', 'bbb'])
        self.assertTrue(args)
        self.assertEqual(args.wldbg, ['aaa'])
        self.assertEqual(args.gdb, ['bbb'])

    def test_parse_args_g_simple(self):
        args = runner.parse_args(['aaa', '--gdb', 'bbb'])
        self.assertTrue(args)
        self.assertEqual(args.wldbg, ['aaa'])
        self.assertEqual(args.gdb, ['bbb'])

    def test_parse_args_g_more_args(self):
        args = runner.parse_args(['something.py', '-f', 'aaa', '-g', 'bbb', '--nh'])
        self.assertTrue(args)
        self.assertEqual(args.wldbg, ['something.py', '-f', 'aaa'])
        self.assertEqual(args.gdb, ['bbb', '--nh'])

    def test_parse_args_uses_first_g(self):
        args = runner.parse_args(['aaa', '-g', 'bbb', '-g'])
        self.assertTrue(args)
        self.assertEqual(args.wldbg, ['aaa'])
        self.assertEqual(args.gdb, ['bbb', '-g'])

    def test_parse_args_g_in_multi_arg(self):
        args = runner.parse_args(['aaa', '-vCg', 'bbb'])
        self.assertTrue(args)
        self.assertEqual(args.wldbg, ['aaa', '-vC'])
        self.assertEqual(args.gdb, ['bbb'])

    def test_parse_args_g_in_multi_arg_not_at_end_throws(self):
        with self.assertRaises(RuntimeError):
            args = runner.parse_args(['aaa', '-vgC', 'bbb'])

class TestRunner(unittest.TestCase):
    def test_basic_gdb_run(self):
        # This may pass even if the wayland-debug plugin has crashed (see test_basic_gdb_run_with_wldbg_command)
        args = runner.Args(['main.py'], ['--batch-silent', '--ex', 'r', '--args', 'cat', '/dev/null'])
        return_code = runner.run_gdb(args, quiet=True)
        self.assertEqual(return_code, 0)

    def test_basic_gdb_run_with_wl_command(self):
        # `--ex wlq` will run the quit wayland-debug command, which will cause gdb to fail if wayland-debug has crashed
        args = runner.Args(['main.py'], ['--batch-silent', '--ex', 'r', '--ex', 'wlq', '--args', 'cat', '/dev/null'])
        return_code = runner.run_gdb(args, quiet=True)
        self.assertEqual(return_code, 0)

    def test_basic_gdb_run_with_wl_subcommand(self):
        # `--ex wl quit` will run the quit wayland-debug command, which will cause gdb to fail if wayland-debug has crashed
        args = runner.Args(['main.py'], ['--batch-silent', '--ex', 'r', '--ex', 'wl quit', '--args', 'cat', '/dev/null'])
        return_code = runner.run_gdb(args, quiet=True)
        self.assertEqual(return_code, 0)

    # This works but there are some issues
    # * Output needs to be switched to gdb.write or else it spams stdout
    # * Breaks if weston-terminal isn't installed or there is no open wayland display
    '''
    def test_gdb_run_with_weston_term(self):
        args = runner.Args(['main.py'], ['--batch-silent', '--ex', 'r', '--args', 'weston-terminal', '--shell=""'])
        return_code = runner.run_gdb(args)
        self.assertEqual(return_code, 0)
    '''
