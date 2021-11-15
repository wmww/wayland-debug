import unittest
from core import LetterIdGenerator

class TestLetterIdGenerator(unittest.TestCase):
    def test_name_generator(self):
        gen = LetterIdGenerator()
        self.assertEqual(gen.next(), 'A')
        self.assertEqual(gen.next(), 'B')
        self.assertEqual(gen.next(), 'C')

    def test_name_generator_big(self):
        gen = LetterIdGenerator()
        self.assertEqual(gen.next(), 'A')
        for i in range(22):
            gen.next()
        self.assertEqual(gen.next(), 'X')
        self.assertEqual(gen.next(), 'Y')
        self.assertEqual(gen.next(), 'Z')
        self.assertEqual(gen.next(), 'AA')
        self.assertEqual(gen.next(), 'AB')
        for i in range(23):
            gen.next()
        self.assertEqual(gen.next(), 'AZ')
        self.assertEqual(gen.next(), 'BA')
        for i in range(23 + 26 * 24):
            gen.next()
        self.assertEqual(gen.next(), 'ZY')
        self.assertEqual(gen.next(), 'ZZ')
        self.assertEqual(gen.next(), 'AAA')
