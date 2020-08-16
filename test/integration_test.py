import pytest
import unittest
import re

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

    def run_server_in_gdb(self, mode, wldbg_args=[]):
        return helpers.run_in_gdb(wldbg_args, ['--ex', 'r', '--args', self.prog, 'server'], [self.prog, mode])

    def test_gdb_plugin_starts(self):
        helpers.run_in_gdb([], [self.prog, '-ex', 'q'], None)

    def test_client_and_server_in_gdb(self):
        result = helpers.run_in_gdb(
            [],
            ['--ex', 'r', '--args', self.prog, 'client-and-server'],
            None)
        self.assertIn('get_registry', result)

    def test_gdb_plugin_runs(self):
        '''
        These tests look nice, but they don't seem to detect any errors inside GDB
        Luckily we also have test_runner.py which does
        '''
        self.run_client_in_gdb('simple-client')

    def test_detects_get_registry_from_client(self):
        result = self.run_client_in_gdb('simple-client')
        self.assertIn('get_registry', result)

    def test_detects_get_registry_from_server(self):
        result = self.run_server_in_gdb('simple-client')
        self.assertIn('get_registry', result)

    def test_correctly_extracts_fixed_point_numbers(self):
        result = self.run_server_in_gdb('pointer-move')
        # This list should match test_fixed_sequence in mock_server.c
        matches = re.findall(r'surface_y=(.*)\)', result)
        expected_values = [0.0, 1.0, 0.5, -1.0, 280.0, -12.5, 16.3, 425.87, -100000.0, 0.001]
        self.assertEqual(len(matches), len(expected_values))
        for i in range(len(matches)):
            match = float(matches[i])
            expected = expected_values[i]
            # TODO: figure out why we're only getting 2 decimal places of accuracy
            self.assertAlmostEqual(match, expected, places = 2)
