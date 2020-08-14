import pytest
import unittest

from integration_helpers import *

class IntegrationTests(unittest.TestCase):
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

    @pytest.mark.skipif(not bin_exists('weston-info'), reason='weston-info not installed')
    def test_gdb_plugin_without_running(self):
        run(['-g', 'weston-info', '-ex', 'q'], error_on_input=True)

    @pytest.mark.skipif(not bin_exists('weston-info'), reason='weston-info not installed')
    @pytest.mark.skipif(not wayland_socket_exists(), reason='no Wayland compositor running')
    def test_gdb_plugin_runs(self):
        '''
        These tests look nice, but they don't seem to detect any errors inside GDB
        Luckily we also have test_runner.py which does
        '''
        run(['-g', 'weston-info', '--ex', 'r'], error_on_input=True)
