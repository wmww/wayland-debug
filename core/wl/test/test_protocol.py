import unittest
from datetime import datetime, date
from os import path
import re

from core.wl.protocol import *
from core import output

def readme_path():
    return path.join(protocols_path(), 'README')

class TestProtocol(unittest.TestCase):
    def tearDown(self):
        dump_all()

    def test_protocol_dir_exists(self):
        self.assertTrue(path.isdir(protocols_path()))

    def test_protocol_dir_readme_exists(self):
        self.assertTrue(path.isfile(readme_path()))

    def test_protocols_are_up_to_data(self):
        readme = open(readme_path()).read()
        matches = re.findall(r'Last updated .* \[(\d+)\]', readme)
        self.assertEqual(len(matches), 1)
        timestamp = int(matches[0])
        now = datetime.now()
        last_update = datetime.fromtimestamp(timestamp)
        delta = now - last_update
        if delta.days > 160:
            raise RuntimeError(
                'It has been ' + str(delta.days) + ' days since the protocols were updated. ' +
                'Please run resources/update-protocols.sh and commit any changes')

    def test_load_all(self):
        out = output.Strict()
        load_all(out)

    def test_get_arg_fails_with_no_protocols_loaded(self):
        self.assertEqual(get_arg('wl_surface', 'attach', 0), None)

    def test_parse_base_10_enum_value(self):
        self.assertEqual(parse_enum_value('37'), 37)

    def test_parse_hex_enum_value(self):
        self.assertEqual(parse_enum_value('0x37'), 55)

    def test_parse_bitwise_expr_enum_value(self):
        self.assertEqual(parse_enum_value('1 << 4'), 16)

    def test_enum_value_isnt_evaled_because_that_would_be_fucking_stupid(self):
        with self.assertRaises(Exception):
            parse_enum_value('int("0")')

class TestLoadedProtocols(unittest.TestCase):
    def setUp(self):
        out = output.Strict()
        load_all(out)

    def tearDown(self):
        dump_all()

    def test_get_arg_succeeds(self):
        arg = get_arg('wl_surface', 'attach', 0)
        self.assertIsInstance(arg, Arg)

    def test_get_arg_returns_different_args_for_message(self):
        first = get_arg('wl_surface', 'attach', 0)
        second = get_arg('wl_surface', 'attach', 1)
        self.assertIsInstance(first, Arg)
        self.assertIsInstance(second, Arg)
        self.assertNotEqual(first, second)

    def test_get_arg_returns_non_on_unknown_protocol(self):
        arg = get_arg('not_a_real_protocol', 'attach', 0)
        self.assertIs(arg, None)

    def test_get_arg_errors_on_known_protocol_unknwon_message(self):
        with self.assertRaises(RuntimeError):
            get_arg('wl_surface', 'bad_message', 0)

    def test_get_arg_errors_on_bad_arg_index(self):
        with self.assertRaises(RuntimeError):
            get_arg('wl_surface', 'attach', 4)
