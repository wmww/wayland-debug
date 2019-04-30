import unittest
import os
from output import stream

class TestStream(unittest.TestCase):
    def test_stream_string_write_string(self):
        s = stream.String()
        s.write('abc')
        s.write('xyz')
        self.assertEquals(s.buffer, 'abc\nxyz\n')

    def test_stream_std_to_file(self):
        file_name = 'stream_test_tmp_file.txt'
        f = open(file_name, 'w')
        s = stream.Std(f)
        s.write('abc')
        s.write('xyz')
        f.close()
        f = open(file_name)
        self.assertEquals(f.read(), 'abc\nxyz\n')
        f.close()
        os.remove(file_name)
