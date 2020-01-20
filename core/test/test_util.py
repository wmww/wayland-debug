import unittest
from core.util import *
import os

class TestParseMessage(unittest.TestCase):

    def test_project_root(self):
        import inspect
        initial_cwd = os.getcwd()
        os.chdir(os.path.join(initial_cwd, 'core', 'test')) # make sure we're not relying on the working directory
        self.assertTrue(os.path.isfile(os.path.join(project_root(), '.gitignore')))
        os.chdir(initial_cwd) # so we don't fuck up other tests
