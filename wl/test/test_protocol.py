import unittest
from wl.protocol import *
import output
from datetime import datetime, date
from os import path
import re

def readme_path():
    return path.join(protocols_path(), 'README')

class TestProtocol(unittest.TestCase):
    def test_protocol_dir_exists(self):
        self.assertTrue(path.isdir(protocols_path()))

    def test_protocol_dir_readme_exists(self):
        self.assertTrue(path.isfile(readme_path()))

    def test_protocols_are_up_to_data(self):
        readme = open(readme_path()).read()
        matches = re.findall('Last updated .* \[(\d+)\]', readme)
        self.assertEquals(len(matches), 1)
        timestamp = int(matches[0])
        now = datetime.now()
        last_update = datetime.fromtimestamp(timestamp)
        delta = now - last_update
        if delta.days > 160:
            raise RuntimeError(
                'It has been ' + str(delta.days) + ' days since the protocols were updated. ' +
                'Please run update-protocols.sh and commit any changes')

    def test_load_all(self):
        out = output.Strict()
        load_all(out)
