from unittest import TestCase, mock, expectedFailure
from wl import *
import connection
from connection import ConnectionImpl, Connection
import output
from output import Output

class TestConnectionImpl(TestCase):
    def setUp(self):
        self.name = 'FOO'
        self.out = output.Strict()
        self.c = ConnectionImpl(0.0, self.name, False)
        self.l = mock.Mock(spec=Connection.Listener)

    def test_connection_impl_is_connection(self):
        self.assertIsInstance(self.c, Connection)

    def test_connection_impl_is_connection_sink(self):
        self.assertIsInstance(self.c, Connection.Sink)

    def test_default_connection_has_display(self):
        obj = self.c.look_up_most_recent(1)
        self.assertTrue(obj)
        self.assertTrue(isinstance(obj, Object))
        self.assertEquals(obj.type, 'wl_display')
        self.assertTrue(obj.resolved())

    def test_by_default_is_open(self):
        self.assertTrue(self.c.is_open())

    def test_by_default_has_no_messages(self):
        self.assertEqual(self.c.messages(), ())

    def test_name(self):
        self.assertEqual(self.c.name(), self.name)

    def test_str_works(self):
        self.assertTrue(str(self.c))

    @expectedFailure
    def test_str_contains_name(self):
        self.assertIn(self.name, str(self.c))

    def test_str_not_just_name(self):
        self.assertNotEqual(self.name, str(self.c))

    def test_messages_returns_tuple(self):
        self.c.message(message.Mock())
        self.c.message(message.Mock())
        self.assertIsInstance(self.c.messages(), tuple)

    def test_messages_are_stored(self):
        m0 = message.Mock()
        m1 = message.Mock()
        self.c.message(m0)
        self.c.message(m1)
        self.assertEqual(self.c.messages(), (m0, m1))

    def test_connection_can_be_closed(self):
        self.assertTrue(self.c.is_open())
        self.c.close(1.0)
        self.assertFalse(self.c.is_open())

    @expectedFailure
    def test_description_changed_when_closed(self):
        before = str(self.c)
        self.c.close(1.0)
        self.assertNotEqual(before, str(self.c))

    def test_description_includes_title_from_message(self):
        title = 'some_app_title'
        m = message.Mock()
        m.name = 'set_title'
        m.args = [Arg.String(title)]
        self.c.message(m)
        self.assertIn(title, str(self.c))

    @expectedFailure
    def test_description_includes_layer_namespace_from_message(self):
        title = 'some_app_title'
        m = message.Mock()
        m.name = 'get_layer_surface'
        m.args = [Arg.Null(), Arg.Null(), Arg.Null(), Arg.Null(), Arg.String(title)]
        self.c.message(m)
        self.assertIn(title, str(self.c))

    def test_description_includes_app_id_from_message(self):
        last_part = 'last_part'
        app_id = 'some.app.id.' + last_part
        m = message.Mock()
        m.name = 'set_app_id'
        m.args = [Arg.String(app_id)]
        self.c.message(m)
        self.assertIn(last_part, str(self.c))

    @expectedFailure
    def test_description_only_includes_last_part_of_app_id(self):
        last_part = 'last_part'
        app_id = 'some.app.id.' + last_part
        m = message.Mock()
        m.name = 'set_app_id'
        m.args = [Arg.String(app_id)]
        self.c.message(m)
        self.assertNotIn(app_id, str(self.c))

    def test_title_does_not_overrite_app_id(self):
        last_part = 'last_part'
        app_id = 'some.app.id.' + last_part
        m0 = message.Mock()
        m0.name = 'set_app_id'
        m0.args = [Arg.String(app_id)]
        self.c.message(m0)
        title = 'some_app_title'
        m1 = message.Mock()
        m1.name = 'set_title'
        m1.args = [Arg.String(title)]
        self.c.message(m1)
        self.assertNotIn(title, str(self.c))
        self.assertIn(last_part, str(self.c))

    @expectedFailure
    def test_listener_notified_of_title_description_change(self):
        title = 'some_app_title'
        m = message.Mock()
        m.name = 'set_title'
        m.args = [Arg.String(title)]
        self.c.add_connection_listener(self.l)
        self.c.message(m)
        self.l.connection_str_changed.assert_called_once_with(self.c)

    @expectedFailure
    def test_listener_notified_of_closed_description_change(self):
        self.c.add_connection_listener(self.l)
        self.c.close(1.0)
        self.l.connection_str_changed.assert_called_once_with(self.c)

    @expectedFailure
    def test_listener_not_notified_on_no_description_change(self):
        m = message.Mock()
        self.c.add_connection_listener(self.l)
        self.c.message(m)
        self.l.connection_str_changed.assert_not_called()

    @expectedFailure
    def test_listener_notified_of_message(self):
        self.c.add_connection_listener(self.l)
        m = message.Mock()
        self.c.message(m)
        self.l.connection_got_new_message.assert_called_once_with(self.c, m)

    @expectedFailure
    def test_remove_listener(self):
        self.c.add_connection_listener(self.l)
        self.c.remove_connection_listener(self.l)
        m = message.Mock()
        self.c.message(m)
        self.l.connection_got_new_message.assert_not_called()

    @expectedFailure
    def test_listener_notified_of_close(self):
        self.c.add_connection_listener(self.l)
        self.c.close(1.0)
        self.l.connection_got_new_message.connection_closed(self.c)

class TestMockConnection(TestCase):
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
