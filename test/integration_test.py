import pytest
import unittest
import re

import integration_helpers as helpers

# This list should match test_fixed_sequence in mock_server.c
test_fixed_sequence = [0.0, 1.0, 0.5, -1.0, 280.0, -12.5, 16.3, 425.87, -100000.0, 0.001]

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

    def test_load_from_file_with_server_obj(self):
        helpers.run_main(['-l', helpers.server_obj_log_file()])

    @pytest.mark.xfail(reason='see https://github.com/wmww/wayland-debug/issues/17')
    def test_load_from_file_with_break(self):
        result = helpers.run_main(['-l', helpers.short_log_file(), '-b', '[global]'])
        self.assertIn('get_registry', result)
        self.assertNotIn('create_surface', result)

class MockProgramInGDBTests(unittest.TestCase):
    def setUp(self):
        mock_client, mock_server = helpers.build_mock_program()
        self.mock_client = mock_client
        self.mock_server = mock_server

    def run_client_in_gdb(self, mode, wldbg_args=[]):
        return helpers.run_in_gdb(
            wldbg_args,
            ['--ex', 'r', '--args', self.mock_client, mode],
            [self.mock_server])

    def run_server_in_gdb(self, mode, wldbg_args=[]):
        return helpers.run_in_gdb(
            wldbg_args,
            ['--ex', 'r', '--args', self.mock_server],
            [self.mock_client, mode])

    def test_gdb_plugin_starts(self):
        helpers.run_in_gdb([], [self.mock_client, '-ex', 'q'], None)

    def test_gdb_plugin_runs(self):
        '''
        These tests look nice, but they don't seem to detect any errors inside GDB
        Luckily we also have test_runner.py which does
        '''
        self.run_client_in_gdb('simple-client')

    def test_detects_get_registry_from_client(self):
        result = self.run_client_in_gdb('simple-client')
        self.assertIn('get_registry', result)
        self.assertIn('global', result)

    def test_detects_get_registry_from_server(self):
        result = self.run_server_in_gdb('simple-client')
        self.assertIn('get_registry', result)
        self.assertIn('global', result)

    def test_extracts_enum_values(self):
        result = self.run_server_in_gdb('simple-client')
        self.assertIn('capabilities=5:pointer&touch', result)

    def test_extracts_fixed_point_numbers_with_low_accuracy(self):
        result = self.run_server_in_gdb('pointer-move')
        matches = re.findall(r'surface_y=(.*)\)', result)
        self.assertEqual(len(matches), len(test_fixed_sequence))
        for i in range(len(matches)):
            match = float(matches[i])
            expected = test_fixed_sequence[i]
            self.assertAlmostEqual(match, expected, places = 2)

    @pytest.mark.xfail(reason='see https://github.com/wmww/wayland-debug/issues/24')
    def test_extracts_fixed_point_numbers_with_high_accuracy(self):
        result = self.run_server_in_gdb('pointer-move')
        matches = re.findall(r'surface_y=(.*)\)', result)
        self.assertEqual(len(matches), len(test_fixed_sequence))
        for i in range(len(matches)):
            match = float(matches[i])
            expected = test_fixed_sequence[i]
            self.assertAlmostEqual(match, expected, places = 5)

    def check_result_of_server_created_obj(self, result):
        matches = re.findall(r'new wl_data_offer@(.*)\.\d+', result)
        self.assertEqual(len(matches), 1)
        data_offer_id = matches[0]
        matches = re.findall(r'.*wl_data_offer@(.*)\..*mock-meme-type', result)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0], data_offer_id)

    def test_client_with_server_created_obj(self):
        result = self.run_client_in_gdb('server-created-obj')
        self.check_result_of_server_created_obj(result)

    def test_server_with_server_created_obj(self):
        result = self.run_server_in_gdb('server-created-obj')
        self.check_result_of_server_created_obj(result)

    def test_client_with_dispatcher(self):
        result = self.run_client_in_gdb('dispatcher')
        self.assertIn('attach', result)
        self.assertIn('enter', result)

    def test_server_with_dispatcher(self):
        result = self.run_server_in_gdb('dispatcher')
        self.assertIn('attach', result)
        self.assertIn('enter', result)
