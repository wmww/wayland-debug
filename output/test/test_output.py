import unittest
import os
from output import Output, Null, Strict
from output import stream

class TestOutput(unittest.TestCase):
    def setUp(self):
        self.out = stream.String()
        self.err = stream.String()

    def test_show(self):
        o = Output(True, True, self.out, self.err)
        o.show('abc')
        o.show('xyz')
        self.assertEqual(self.out.buffer, 'abc\nxyz\n')
        self.assertEqual(self.err.buffer, '')

    def test_show_multi(self):
        o = Output(True, True, self.out, self.err)
        o.show('abc', 24, True)
        self.assertEqual(self.out.buffer, 'abc 24 True\n')
        self.assertEqual(self.err.buffer, '')

    def test_warn(self):
        o = Output(True, True, self.out, self.err)
        o.warn('abc')
        self.assertIn('Warning:', self.err.buffer)
        self.assertIn('abc', self.err.buffer)
        self.assertEqual(self.out.buffer, '')

    def test_error(self):
        o = Output(True, True, self.out, self.err)
        o.error('abc')
        self.assertIn('Error:', self.err.buffer)
        self.assertIn('abc', self.err.buffer)
        self.assertEqual(self.out.buffer, '')

    def test_unprocessed(self):
        o = Output(True, True, self.out, self.err)
        o.unprocessed('abc')
        self.assertIn('abc', self.out.buffer)
        self.assertEqual(self.err.buffer, '')

    def test_no_unprocessed_if_disabled(self):
        o = Output(True, False, self.out, self.err)
        o.unprocessed('abc')
        self.assertEqual(self.out.buffer, '')
        self.assertEqual(self.err.buffer, '')

    def test_null_output(self):
        o = Null()
        o.show('abc')
        o.warn('abc')
        o.error('abc')
        o.unprocessed('abc')
        # It's difficult to test that nothing whatsoever happened

    def test_strict_output_does_nothing_for_normal_output(self):
        o = Strict()
        o.show('abc')
        o.unprocessed('abc')
        # It's difficult to test that nothing whatsoever happened

    def test_strict_output_raises_on_error(self):
        o = Strict()
        with self.assertRaises(RuntimeError):
            o.warn('abc')
        with self.assertRaises(RuntimeError):
            o.error('xyz')
