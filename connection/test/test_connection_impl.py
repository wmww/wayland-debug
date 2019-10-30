from unittest import TestCase, expectedFailure, mock, skip
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

    def test_by_default_is_open(self):
        self.assertTrue(self.c.is_open())

    def test_can_create_client_connection(self):
        c = ConnectionImpl(0.0, self.name, False)
        self.assertEqual(c.is_server(), False)

    def test_can_create_server_connection(self):
        c = ConnectionImpl(0.0, self.name, True)
        self.assertEqual(c.is_server(), True)

    def test_can_create_connection_of_unknown_type(self):
        c = ConnectionImpl(0.0, self.name, None)
        self.assertEqual(c.is_server(), None)

    def test_by_default_has_no_messages(self):
        self.assertEqual(self.c.messages(), ())

    def test_name(self):
        self.assertEqual(self.c.name(), self.name)

    def test_str_works(self):
        self.assertTrue(str(self.c))

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

    @skip('We need to use the standard logging system for this to work')
    def test_warning_on_message_after_close(self):
        self.c.close(0.0)
        m = message.Mock()
        self.c.message(m)
        # TODO: assert that this logs a warning

    def test_app_id_none_by_defalt(self):
        self.assertEqual(self.c.app_id(), None)

    def test_detects_app_id(self):
        app_id = 'some.app.id'
        m = message.Mock()
        m.name = 'set_app_id'
        m.args = [Arg.String(app_id)]
        self.c.message(m)
        self.assertEqual(self.c.app_id(), app_id)

    def test_listener_notified_of_app_id_change(self):
        app_id = 'some.app.id'
        m = message.Mock()
        m.name = 'set_app_id'
        m.args = [Arg.String(app_id)]
        self.c.add_connection_listener(self.l)
        self.c.message(m)
        self.l.connection_app_id_set.assert_called_once_with(self.c, app_id)

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

    def test_listener_notified_of_title_description_change(self):
        title = 'some_app_title'
        m = message.Mock()
        m.name = 'set_title'
        m.args = [Arg.String(title)]
        self.c.add_connection_listener(self.l)
        self.c.message(m)
        self.l.connection_str_changed.assert_called_once_with(self.c)

    def test_listener_notified_of_closed_description_change(self):
        self.c.add_connection_listener(self.l)
        self.c.close(1.0)
        self.l.connection_str_changed.assert_called_once_with(self.c)

    def test_listener_not_notified_on_no_description_change(self):
        m = message.Mock()
        self.c.add_connection_listener(self.l)
        self.c.message(m)
        self.l.connection_str_changed.assert_not_called()

    def test_listener_notified_of_message(self):
        self.c.add_connection_listener(self.l)
        m = message.Mock()
        self.c.message(m)
        self.l.connection_got_new_message.assert_called_once_with(self.c, m)

    def test_remove_listener(self):
        self.c.add_connection_listener(self.l)
        self.c.remove_connection_listener(self.l)
        m = message.Mock()
        self.c.message(m)
        self.l.connection_got_new_message.assert_not_called()

    def test_listener_notified_of_close(self):
        self.c.add_connection_listener(self.l)
        self.c.close(1.0)
        self.l.connection_got_new_message.connection_closed(self.c)

class TestObjectIDImpl(TestCase):
    def setUp(self):
        self.c = ConnectionImpl(0.0, 'BAR', False)

    def test_can_create_registry(self):
        self.c.create_object(0.0, self.c.wl_display(), 2, 'wl_registry')

    def test_create_object_fails_with_no_parent(self):
        with self.assertRaises(AssertionError):
            self.c.create_object(0.0, None, 2, 'wl_registry')

    def test_create_object_fails_with_no_type(self):
        with self.assertRaises(AssertionError):
            self.c.create_object(0.0, self.c.wl_display(), 2, None)

    def test_can_not_create_2nd_display(self):
        with self.assertRaises(RuntimeError):
            self.c.create_object(0.0, self.c.wl_display(), 1, 'wl_display')

    @skip('Prints warning to stdout instead of just raising exception')
    def test_can_not_create_2nd_registry(self):
        self.c.create_object(0.0, self.c.wl_display(), 2, 'wl_registry')
        with self.assertRaises(RuntimeError):
            self.c.create_object(0.0, self.c.wl_display(), 2, 'wl_registry')

    def test_can_not_create_2nd_anything_with_same_id(self):
        self.c.create_object(0.0, self.c.wl_display(), 3, 'first_thing')
        with self.assertRaises(RuntimeError):
            self.c.create_object(0.0, self.c.wl_display(), 3, 'second_thing')

    def test_retrieve_object_raises_on_invalid_id(self):
        with self.assertRaises(RuntimeError):
            self.c.retrieve_object(2, -1, None)

    def test_retrieve_object_raises_on_invalid_generation(self):
        with self.assertRaises(RuntimeError):
            self.c.retrieve_object(1, 1, None)

    def test_retrieve_object_raises_on_invalid_type(self):
        with self.assertRaises(RuntimeError):
            self.c.retrieve_object(1, -1, 'not_wl_display')

    def test_retrieve_object_with_type(self):
        self.assertEqual(self.c.retrieve_object(1, -1, 'wl_display'), self.c.wl_display())

    def test_retrieve_object_with_type_wildcards(self):
        self.assertEqual(self.c.retrieve_object(1, -1, 'wl*disp*'), self.c.wl_display())

    def test_wl_display(self):
        self.assertIsInstance(self.c.wl_display(), Object)
        self.assertEqual(self.c.wl_display().type, 'wl_display')
        self.assertEqual(self.c.wl_display().id, 1)
        self.assertEqual(self.c.wl_display().generation, 0)

    def test_wl_display_in_db(self):
        self.assertEqual(self.c.retrieve_object(1, -1, None), self.c.wl_display())
