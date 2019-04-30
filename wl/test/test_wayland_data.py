import unittest
from wl import *
import util
from output import stream

class TestMessage(unittest.TestCase):
    def setUp(self):
        assert hasattr(Message, 'base_time')
        Message.base_time = None

    def test_create_message(self):
        o = Object.Unresolved(7, None)
        m = Message(12.5, o, False, "some_msg", [])

    def test_message_calculates_timestamp_offset(self):
        o = Object.Unresolved(7, None)
        m0 = Message(4.0, o, False, "some_msg", [])
        m1 = Message(6.0, o, False, "other_msg", [])
        self.assertEqual(m0.timestamp, 0.0)
        self.assertEqual(m1.timestamp, 2.0)

class TestConnection(unittest.TestCase):
    def setUp(self):
        self.out = util.Output(False, False, stream.String(), stream.String())
        self.c = Connection('A', False, None, 0, self.out)

    def test_create_empty_connection(self):
        pass

    def test_default_connection_has_display(self):
        obj = self.c.look_up_most_recent(1)
        self.assertTrue(obj)
        self.assertTrue(isinstance(obj, Object))
        self.assertEquals(obj.type, 'wl_display')
        self.assertTrue(obj.resolved())
