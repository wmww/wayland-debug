import unittest
from wl import *
import util

class TestWaylandData(unittest.TestCase):
    def setUp(self):
        self.out = util.Output(False, False, lambda m: (), lambda m: ())

    def test_create_empty_connection(self):
        c = Connection('A', False, None, 0, self.out)

    def test_default_connection_has_display(self):
        c = Connection('A', False, None, 0, self.out)
        obj = c.look_up_most_recent(1)
        self.assertTrue(obj)
        self.assertTrue(isinstance(obj, Object))
        self.assertEquals(obj.type, 'wl_display')
        self.assertTrue(obj.resolved())
