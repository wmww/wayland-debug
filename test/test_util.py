import unittest
from util import *
import os

class TestParseMessage(unittest.TestCase):

    def test_project_root(self):
        import inspect
        self_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        os.chdir(self_dir) # make sure we're not relying on the working directory
        self.assertEqual(os.path.basename(self_dir), 'test')
        self.assertEqual(project_root(), os.path.dirname(self_dir))
