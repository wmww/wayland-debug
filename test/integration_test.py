import pytest
import unittest

from integration_helpers import *

class PartialIntegrationTests(unittest.TestCase):
    def test_bin_exists_works(self):
        self.assertTrue(bin_exists('ls'))
        self.assertFalse(bin_exists('doesnotexist'))

    def test_load_from_file_doesnt_crash(self):
        run(['-l', short_log_file()])

    def test_load_from_file_shows_messages(self):
        result = run(['-l', short_log_file()])
        self.assertIn('get_registry', result)
        self.assertIn('create_surface', result)

    def test_load_from_file_with_filter(self):
        result = run(['-l', short_log_file(), '-f', 'wl_compositor'])
        self.assertNotIn('get_registry', result)
        self.assertIn('create_surface', result)

    @pytest.mark.xfail(reason='see https://github.com/wmww/wayland-debug/issues/17')
    def test_load_from_file_with_break(self):
        result = run(['-l', short_log_file(), '-b', '[global]'])
        self.assertIn('get_registry', result)
        self.assertNotIn('create_surface', result)

class MockProgramTests(unittest.TestCase):
    def setUp(self):
        self.prog = build_mock_program()

    def test_gdb_plugin_starts(self):
        run(['-g', self.prog, '-ex', 'q'], error_on_input=True)

    def test_gdb_plugin_runs(self):
        '''
        These tests look nice, but they don't seem to detect any errors inside GDB
        Luckily we also have test_runner.py which does
        '''
        run(['-g', self.prog, '--ex', 'r'], error_on_input=True)
