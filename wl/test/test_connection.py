import unittest
from wl import *
import output
from output import Output

class TestConnection(unittest.TestCase):
    def setUp(self):
        self.out = output.Strict()
        self.c = Connection('A', False, None, 0, self.out)

    def test_create_empty_connection(self):
        pass

    def test_default_connection_has_display(self):
        obj = self.c.look_up_most_recent(1)
        self.assertTrue(obj)
        self.assertTrue(isinstance(obj, Object))
        self.assertEquals(obj.type, 'wl_display')
        self.assertTrue(obj.resolved())

class TestConnectionNameGenerator(unittest.TestCase):
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

class TestMockConnection(unittest.TestCase):
    def setUp(self):
        self.c = connection.Mock()

    def test_call_mock_methods(self):
        self.c = connection.Mock()
        self.c.close(1.0)
        self.c.set_title('foo')
        self.assertIsInstance(self.c.description(), str)
        self.c.message(message.Mock())

    def test_look_up_specific(self):
        self.assertIsInstance(self.c.look_up_specific(2, 4), object.Base)

    def test_look_up_most_recent(self):
        self.assertIsInstance(self.c.look_up_most_recent(7), object.Base)
