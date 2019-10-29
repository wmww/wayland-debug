import unittest
from connection.name_generator import NameGenerator

class TestNameGenerator(unittest.TestCase):
    def test_name_generator(self):
        gen = NameGenerator()
        self.assertEquals(gen.next(), 'A')
        self.assertEquals(gen.next(), 'B')
        self.assertEquals(gen.next(), 'C')

    def test_name_generator_big(self):
        gen = NameGenerator()
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
