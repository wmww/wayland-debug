import pytest
import unittest

import integration_helpers as helpers

class FileLoadTests(unittest.TestCase):
    def test_load_from_file_doesnt_crash(self):
        helpers.run_main(['-l', helpers.short_log_file()])

    def test_load_from_file_shows_messages(self):
        result = helpers.run_main(['-l', helpers.short_log_file()])
        self.assertIn('get_registry', result)
        self.assertIn('create_surface', result)

    def test_load_from_file_with_filter(self):
        result = helpers.run_main(['-l', helpers.short_log_file(), '-f', 'wl_compositor'])
        self.assertNotIn('get_registry', result)
        self.assertIn('create_surface', result)

    @pytest.mark.xfail(reason='see https://github.com/wmww/wayland-debug/issues/17')
    def test_load_from_file_with_break(self):
        result = helpers.run_main(['-l', helpers.short_log_file(), '-b', '[global]'])
        self.assertIn('get_registry', result)
        self.assertNotIn('create_surface', result)

class MockProgramInGDBTests(unittest.TestCase):
    def setUp(self):
        self.prog = helpers.build_mock_program()

    def run_prog_in_gdb(self, wldbg_args=[]):
        return helpers.run_in_gdb(wldbg_args, [self.prog, '--ex', 'r'])

    def test_gdb_plugin_starts(self):
        helpers.run_in_gdb([], [self.prog, '-ex', 'q'])

    def test_gdb_plugin_runs(self):
        '''
        These tests look nice, but they don't seem to detect any errors inside GDB
        Luckily we also have test_runner.py which does
        '''
        self.run_prog_in_gdb()

    def test_detects_get_registry(self):
        result = self.run_prog_in_gdb()
        self.assertIn('get_registry', result)
