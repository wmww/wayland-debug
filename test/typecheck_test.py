import unittest
import subprocess
import os

import integration_helpers
reset_color = '\x1b[0m'

class TypecheckTest(unittest.TestCase):
    def test_project_typechecks(self):
        mypy = integration_helpers.find_bin('mypy')
        assert mypy, 'Could not find mypy executable'
        project_path = integration_helpers.get_project_path()
        os.environ['MYPY_FORCE_COLOR'] = '1'
        result = subprocess.run([mypy, project_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if result.returncode != 0:
            raise RuntimeError('`$ mypy ' + project_path + '` failed:\n\n' + reset_color + result.stdout)
