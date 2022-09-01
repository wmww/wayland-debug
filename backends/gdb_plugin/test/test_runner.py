import unittest
from backends.gdb_plugin import runner

class TestRunner(unittest.TestCase):
    def test_basic_gdb_run(self):
        # This may pass even if the wayland-debug plugin has crashed (see test_basic_gdb_run_with_wldbg_command)
        return_code = runner.run_gdb(['main.py'], ['--batch-silent', '--ex', 'r', '--args', 'cat', '/dev/null'], quiet=True)
        self.assertEqual(return_code, 0)

    def test_basic_gdb_run_with_wl_command(self):
        # `--ex wlq` will run the quit wayland-debug command, which will cause gdb to fail if wayland-debug has crashed
        return_code = runner.run_gdb(['main.py'], ['--batch-silent', '--ex', 'r', '--ex', 'wlq', '--args', 'cat', '/dev/null'], quiet=True)
        self.assertEqual(return_code, 0)

    def test_basic_gdb_run_with_wl_subcommand(self):
        # `--ex wl quit` will run the quit wayland-debug command, which will cause gdb to fail if wayland-debug has crashed
        return_code = runner.run_gdb(['main.py'], ['--batch-silent', '--ex', 'r', '--ex', 'wl quit', '--args', 'cat', '/dev/null'], quiet=True)
        self.assertEqual(return_code, 0)

    # This works but there are some issues
    # * Output needs to be switched to gdb.write or else it spams stdout
    # * Breaks if weston-terminal isn't installed or there is no open wayland display
    '''
    def test_gdb_run_with_weston_term(self):
        return_code = runner.run_gdb(['main.py'], ['--batch-silent', '--ex', 'r', '--args', 'weston-terminal', '--shell=""'], quiet=True)
        self.assertEqual(return_code, 0)
    '''
