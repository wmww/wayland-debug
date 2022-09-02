import unittest
import os
import re
from datetime import datetime, date

import integration_helpers

def readme_path():
    return os.path.join(integration_helpers.get_project_path(), 'resources', 'protocols', 'README')

class ProtocolsUpToDateTest(unittest.TestCase):
    def test_protocol_dir_readme_exists(self):
        self.assertTrue(os.path.isfile(readme_path()))

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
