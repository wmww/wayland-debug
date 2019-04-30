import unittest
import os
from output import Output
from output import stream

class TestOutput(unittest.TestCase):
    def setUp(self):
        self.out = stream.String()
        self.err = stream.String()

    def test_show(self):
        o = Output(True, True, self.out, self.err)
        o.show('abc')
        o.show('xyz')
        self.assertEquals(self.out.buffer, 'abc\nxyz\n')
        self.assertEquals(self.err.buffer, '')

    def test_show_multi(self):
        o = Output(True, True, self.out, self.err)
        o.show('abc', 24, True)
        self.assertEquals(self.out.buffer, 'abc 24 True\n')
        self.assertEquals(self.err.buffer, '')

    def test_warn(self):
        o = Output(True, True, self.out, self.err)
        o.warn('abc')
        self.assertIn('Warning:', self.err.buffer)
        self.assertIn('abc', self.err.buffer)
        self.assertEquals(self.out.buffer, '')

    def test_error(self):
        o = Output(True, True, self.out, self.err)
        o.error('abc')
        self.assertIn('Error:', self.err.buffer)
        self.assertIn('abc', self.err.buffer)
        self.assertEquals(self.out.buffer, '')

    def test_log(self):
        o = Output(True, True, self.out, self.err)
        o.log('abc')
        self.assertIn('abc', self.out.buffer)
        self.assertEquals(self.err.buffer, '')

    def test_no_log_if_not_verbose(self):
        o = Output(False, True, self.out, self.err)
        o.log('abc')
        self.assertEquals(self.out.buffer, '')
        self.assertEquals(self.err.buffer, '')

    def test_unprocessed(self):
        o = Output(True, True, self.out, self.err)
        o.unprocessed('abc')
        self.assertIn('abc', self.out.buffer)
        self.assertEquals(self.err.buffer, '')

    def test_no_unprocessed_if_disabled(self):
        o = Output(True, False, self.out, self.err)
        o.unprocessed('abc')
        self.assertEquals(self.out.buffer, '')
        self.assertEquals(self.err.buffer, '')
