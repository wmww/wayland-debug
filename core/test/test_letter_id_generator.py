import unittest
from core import LetterIdGenerator, number_to_letter_id, letter_id_to_number

loop_to = 10000

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

    def test_number_to_letter_id_caps(self):
        self.assertEqual(number_to_letter_id(0, True), 'A')
        self.assertEqual(number_to_letter_id(25, True), 'Z')
        self.assertEqual(number_to_letter_id(26, True), 'AA')

    def test_number_to_letter_id_no_caps(self):
        self.assertEqual(number_to_letter_id(0, False), 'a')
        self.assertEqual(number_to_letter_id(25, False), 'z')
        self.assertEqual(number_to_letter_id(26, False), 'aa')

    def test_number_to_letter_id_does_not_repeat(self):
        seen = set()
        for i in range(loop_to):
            a = number_to_letter_id(i, False)
            self.assertNotIn(a, seen)
            seen.add(a)
        self.assertEqual(len(seen), loop_to)

    def test_number_to_letter_id_raises_on_negative_input(self):
        with self.assertRaises(AssertionError):
            number_to_letter_id(-1, False)

    def test_letter_id_to_number_simple(self):
        self.assertEqual(letter_id_to_number('a'), 0)
        self.assertEqual(letter_id_to_number('b'), 1)
        self.assertEqual(letter_id_to_number('c'), 2)

    def test_letter_id_to_number_multi_digit(self):
        self.assertEqual(letter_id_to_number('aa'), 26)
        self.assertEqual(letter_id_to_number('ab'), 27)
        self.assertEqual(letter_id_to_number('ba'), 52)

    def test_letter_id_to_number_caps(self):
        self.assertEqual(letter_id_to_number('A'), 0)
        self.assertEqual(letter_id_to_number('AB'), 27)

    def test_letter_id_to_number_raises_on_invalid_input(self):
        with self.assertRaises(AssertionError):
            letter_id_to_number('a b')
        with self.assertRaises(AssertionError):
            letter_id_to_number('')

    def test_back_and_forth(self):
        past = set()
        for i in range(loop_to):
            text = number_to_letter_id(i, False)
            generated = letter_id_to_number(text)
            self.assertEqual(generated, i)
