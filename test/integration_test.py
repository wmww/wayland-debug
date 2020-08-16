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

    def run_client_in_gdb(self, mode, wldbg_args=[]):
        return helpers.run_in_gdb(wldbg_args, ['--ex', 'r', '--args', self.prog, mode], [self.prog, 'server'])

    def test_gdb_plugin_starts(self):
        helpers.run_in_gdb([], [self.prog, '-ex', 'q'])

    def test_server_in_gdb(self):
        result = helpers.run_in_gdb(
            [],
            ['--ex', 'r', '--args', self.prog, 'server'],
            [self.prog, 'simple-client'])
        self.assertIn('get_registry', result)

    def test_gdb_plugin_runs(self):
        '''
        These tests look nice, but they don't seem to detect any errors inside GDB
        Luckily we also have test_runner.py which does
        '''
        self.run_client_in_gdb('simple-client')

    def test_detects_get_registry(self):
        result = self.run_client_in_gdb('simple-client')
        self.assertIn('get_registry', result)
