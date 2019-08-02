import unittest
from wl import *
from output import stream
from output import Output

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
        self.out = Output(False, False, stream.String(), stream.String())
        self.c = Connection('A', False, None, 0, None, self.out)

    def test_create_empty_connection(self):
        pass

    def test_default_connection_has_display(self):
        obj = self.c.look_up_most_recent(1)
        self.assertTrue(obj)
        self.assertTrue(isinstance(obj, Object))
        self.assertEquals(obj.type, 'wl_display')
        self.assertTrue(obj.resolved())

    def test_name_generator(self):
        gen = Connection.NameGenerator()
        self.assertEquals(gen.next(), 'A')
        self.assertEquals(gen.next(), 'B')
        self.assertEquals(gen.next(), 'C')

    def test_name_generator_big(self):
        gen = Connection.NameGenerator()
        self.assertEquals(gen.next(), 'A')
        for i in range(22):
            gen.next()
        self.assertEquals(gen.next(), 'X')
        self.assertEquals(gen.next(), 'Y')
        self.assertEquals(gen.next(), 'Z')
        self.assertEquals(gen.next(), 'AA')
        self.assertEquals(gen.next(), 'AB')
        for i in range(23):
            gen.next()
        self.assertEquals(gen.next(), 'AZ')
        self.assertEquals(gen.next(), 'BA')
        for i in range(23 + 26 * 24):
            gen.next()
        self.assertEquals(gen.next(), 'ZY')
        self.assertEquals(gen.next(), 'ZZ')
        self.assertEquals(gen.next(), 'AAA')
