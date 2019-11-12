import unittest
from wl import *
from libwayland_logs import parse

class TestParseMessage(unittest.TestCase):
    def setUp(self):
        assert hasattr(Message, 'base_time')
        Message.base_time = None

    def test_parse_empty_raises(self):
        with self.assertRaises(RuntimeError):
            m = parse.message('')

    def test_parse_trash_raises(self):
        with self.assertRaises(RuntimeError):
            m = parse.message('asfjgdsfk')

    def test_parse_in_message_no_args(self):
        conn_id, m = parse.message('[1234567.890] some_object@12.some_message()')
        self.assertIsInstance(m, Message)
        self.assertEqual(m.timestamp, 0)
        self.assertEqual(m.obj.type, 'some_object')
        self.assertEqual(m.obj.id, 12)
        self.assertEqual(m.sent, False)
        self.assertEqual(m.name, 'some_message')
        self.assertEqual(m.args, [])
        self.assertEqual(m.destroyed_obj, None)

    def test_parse_out_message_no_args(self):
        conn_id, m = parse.message('[1234567.890]  -> some_object@12.some_message()')
        self.assertIsInstance(m, Message)
        self.assertEqual(m.timestamp, 0)
        self.assertEqual(m.obj.type, 'some_object')
        self.assertEqual(m.obj.id, 12)
        self.assertEqual(m.sent, True)
        self.assertEqual(m.name, 'some_message')
        self.assertEqual(m.args, [])
        self.assertEqual(m.destroyed_obj, None)

    def parse_message_with_args(self, args_str):
        conn_id, m = parse.message('[1234567.890] some_object@12.some_message(' + args_str + ')')
        self.assertIsInstance(m, Message)
        self.assertEqual(m.timestamp, 0)
        self.assertEqual(m.obj.type, 'some_object')
        self.assertEqual(m.obj.id, 12)
        self.assertEqual(m.sent, False)
        self.assertEqual(m.name, 'some_message')
        return m.args

    def test_parse_args_int_new_id_string(self):
        args = self.parse_message_with_args('22, new id some_type@47, "foo"')
        self.assertEqual(len(args), 3)

        self.assertIsInstance(args[0], Arg.Int)
        self.assertEqual(args[0].value, 22)

        self.assertIsInstance(args[1], Arg.Object)
        self.assertEqual(args[1].obj.type, 'some_type')
        self.assertEqual(args[1].obj.id, 47)
        self.assertEqual(args[1].is_new, True)

        self.assertIsInstance(args[2], Arg.String)
        self.assertEqual(args[2].value, 'foo')

    def test_parse_string_with_comma(self):
        args = self.parse_message_with_args('8, "some, string", 9')
        self.assertEqual(len(args), 3)

        self.assertIsInstance(args[1], Arg.String)
        self.assertEqual(args[1].value, 'some, string')

class TestParseArg(unittest.TestCase):
    def parse_arg(self, raw):
        conn_id, m = parse.message('[1234567.890] some_object@12.some_message(' + raw + ')')
        self.assertEqual(len(m.args), 1)
        return m.args[0]

    def test_parse_int_arg(self):
        a = self.parse_arg('74')
        self.assertIsInstance(a, Arg.Int)
        self.assertEqual(a.value, 74)

    def test_parse_negative_int_arg(self):
        a = self.parse_arg('-12')
        self.assertIsInstance(a, Arg.Int)
        self.assertEqual(a.value, -12)

    def test_parse_float_arg(self):
        a = self.parse_arg('129.04')
        self.assertIsInstance(a, Arg.Float)
        self.assertEqual(a.value, 129.04)

    def test_parse_negative_float_arg(self):
        a = self.parse_arg('-0.293')
        self.assertIsInstance(a, Arg.Float)
        self.assertEqual(a.value, -0.293)

    def test_parse_string_arg(self):
        a = self.parse_arg('"foo bar"')
        self.assertIsInstance(a, Arg.String)
        self.assertEqual(a.value, 'foo bar')

    def test_parse_string_looks_like_number_arg(self):
        a = self.parse_arg('"29"')
        self.assertIsInstance(a, Arg.String)
        self.assertEqual(a.value, '29')

    def test_parse_string_looks_like_obj_arg(self):
        a = self.parse_arg('"my_obj@4"')
        self.assertIsInstance(a, Arg.String)
        self.assertEqual(a.value, 'my_obj@4')

    def test_parse_null_arg(self):
        a = self.parse_arg('nil')
        self.assertIsInstance(a, Arg.Null)

    def test_parse_fd_arg(self):
        a = self.parse_arg('fd 7')
        self.assertIsInstance(a, Arg.Fd)
        self.assertEqual(a.value, 7)

    def test_parse_array_arg(self):
        a = self.parse_arg('array')
        self.assertIsInstance(a, Arg.Array)

    def test_parse_obj_arg(self):
        a = self.parse_arg('some_type@47')
        self.assertIsInstance(a, Arg.Object)
        self.assertEqual(a.obj.type, 'some_type')
        self.assertEqual(a.obj.id, 47)
        self.assertEqual(a.is_new, False)

    def test_parse_new_id_arg(self):
        a = self.parse_arg('new id some_type@47')
        self.assertIsInstance(a, Arg.Object)
        self.assertEqual(a.obj.type, 'some_type')
        self.assertEqual(a.obj.id, 47)
        self.assertEqual(a.is_new, True)

    def test_parse_unknown_new_id_arg(self):
        a = self.parse_arg('new id [unknown]@47')
        self.assertIsInstance(a, Arg.Object)
        self.assertEqual(a.obj.type, None)
        self.assertEqual(a.obj.id, 47)
        self.assertEqual(a.is_new, True)
