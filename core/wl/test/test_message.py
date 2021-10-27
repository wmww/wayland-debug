from unittest import TestCase, mock
from core.wl import *
import interfaces

class TestMessage(TestCase):
    def setUp(self):
        assert hasattr(Message, 'base_time')
        Message.base_time = None

    def test_create_message(self):
        o = UnresolvedObject(7, None)
        m = Message(12.5, o, False, "some_msg", [])

    def test_message_calculates_timestamp_offset(self):
        o = UnresolvedObject(7, None)
        m0 = Message(4.0, o, False, "some_msg", [])
        m1 = Message(6.0, o, False, "other_msg", [])
        self.assertEqual(m0.timestamp, 0.0)
        self.assertEqual(m1.timestamp, 2.0)

class TestMockMessage(TestCase):
    def setUp(self):
        self.m = message.Mock()

    def test_convert_to_str(self):
        self.assertTrue(str(self.m))

    def test_resolve(self):
        db = mock.Mock(spec=interfaces.ObjectDB)
        self.m.resolve(db)

    def test_used_objects(self):
        self.assertEqual(self.m.used_objects(), ())
