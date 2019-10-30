from unittest import TestCase, mock
from connection import ConnectionManager, ConnectionIDSink, ConnectionList, Connection
import wl
import output

def mock_listener():
    return mock.Mock(spec=ConnectionList.Listener)

class TestConnectionManager(TestCase):

    def setUp(self):
        self.cm = ConnectionManager()

    def test_connection_manager_is_a_message_sink(self):
        self.assertTrue(isinstance(self.cm, ConnectionIDSink))

    def test_does_not_allow_empty_connection_id(self):
        with self.assertRaises(AssertionError):
            self.cm.open_connection(0.0, '', True)

    def test_client_connection(self):
        self.cm.open_connection(0.0, 'foo', False)
        self.cm.message('foo', wl.message.Mock())
        self.cm.close_connection(0.0, 'foo')

    def test_server_connection(self):
        self.cm.open_connection(0.0, 'foo', True)
        self.cm.message('foo', wl.message.Mock())
        self.cm.close_connection(0.0, 'foo')

    def test_connection_of_unknown_type(self):
        self.cm.open_connection(0.0, 'foo', None)
        self.cm.message('foo', wl.message.Mock())
        self.cm.close_connection(0.0, 'foo')

    # TODO: replace test_open_connection_returns_connection with this
    # def test_open_connection_returns_none(self):
    #     self.assertIs(self.cm.open_connection(0.0, 'foo', False), None)

    # TODO: remove
    def test_open_connection_returns_connection(self):
        self.assertIsInstance(self.cm.open_connection(0.0, 'foo', False), Connection)

    def test_keep_track_of_multiple_sessions(self):
        self.cm.open_connection(0.0, 'foo', True)
        self.cm.open_connection(0.5, 'bar', False)
        self.cm.close_connection(1.0, 'bar')
        self.cm.open_connection(1.5, 'baz', None)
        self.assertEquals(len(self.cm.open_connections), 2)
        self.assertEquals(len(self.cm.connection_list), 3)
        self.assertIn('foo', self.cm.open_connections)
        self.assertIn('baz', self.cm.open_connections)
        self.assertNotIn('bar', self.cm.open_connections)

    def test_close_actually_closes_connection(self):
        self.cm.open_connection(0.0, 'foo', False)
        conn = self.cm.connection_list[-1]
        self.assertTrue(conn.open)
        self.cm.close_connection(1.0, 'foo')
        self.assertFalse(conn.open)

    def test_can_close_nonexistent_connection(self):
        self.cm.close_connection(1.0, 'bar')
        self.cm.close_connection(1.0, 'bar')

    # TODO: replace test_opening_duplicate_connections_closes_previous with this
    # def test_can_not_open_duplicate_connection(self):
    #     self.cm.open_connection(0.0, 'foo', True)
    #     with self.assertRaises(AssertionError):
    #         self.cm.open_connection(0.0, 'foo', True)

    # TODO: remove
    def test_opening_duplicate_connections_closes_previous(self):
        self.cm.open_connection(0.0, 'foo', False)
        conn0 = self.cm.connection_list[-1]
        self.cm.open_connection(0.0, 'foo', False)
        conn1 = self.cm.connection_list[-1]
        self.assertFalse(conn0.open)
        self.assertTrue(conn1.open)

    def test_can_not_send_message_to_nonexistent_connection(self):
        with self.assertRaises(AssertionError):
            self.cm.message('foo', wl.message.Mock())

    def test_can_not_send_message_to_closed_connection(self):
        self.cm.open_connection(0.0, 'foo', True)
        self.cm.close_connection(1.0, 'foo')
        with self.assertRaises(AssertionError):
            self.cm.message('foo', wl.message.Mock())

    def test_connections_returns_tuple(self):
        self.assertIsInstance(self.cm.connections(), tuple)

    def test_connections_returns_all_connections(self):
        self.cm.open_connection(0.0, 'foo', False)
        conn0 = self.cm.connection_list[-1]
        self.cm.open_connection(0.0, 'bar', True)
        conn1 = self.cm.connection_list[-1]
        self.cm.close_connection(1.0, 'foo')
        self.assertEqual(self.cm.connections(), (conn0, conn1))

    def test_add_connection_list_listener(self):
        listener = mock_listener()
        self.cm.add_connection_list_listener(listener, False)
        self.cm.open_connection(0.0, 'foo', False)
        listener.connection_opened.assert_called_once()
        listener.connection_closed.assert_not_called()

    def test_connection_list_listener_connection_closed(self):
        listener = mock_listener()
        self.cm.add_connection_list_listener(listener, False)
        self.cm.open_connection(0.0, 'foo', False)
        self.cm.close_connection(0.0, 'foo')
        listener.connection_opened.assert_called_once()
        listener.connection_closed.assert_called_once()

    def test_remove_connection_list_listener(self):
        listener = mock_listener()
        self.cm.add_connection_list_listener(listener, False)
        self.cm.remove_connection_list_listener(listener)
        self.cm.open_connection(0.0, 'foo', False)
        listener.connection_opened.assert_not_called()
        listener.connection_closed.assert_not_called()

    def test_connection_list_listener_dont_catch_up(self):
        self.cm.open_connection(0.0, 'foo', False)
        self.cm.open_connection(0.0, 'bar', False)
        self.cm.close_connection(0.0, 'foo')
        listener = mock_listener()
        self.cm.add_connection_list_listener(listener, False)
        listener.connection_opened.assert_not_called()
        listener.connection_closed.assert_not_called()

    def test_connection_list_listener_catch_up(self):
        self.cm.open_connection(0.0, 'foo', False)
        self.cm.open_connection(0.0, 'bar', False)
        self.cm.close_connection(0.0, 'foo')
        listener = mock_listener()
        self.cm.add_connection_list_listener(listener, True)
        self.assertEqual(len(listener.connection_opened.call_args_list), 2)
        self.assertEqual(len(listener.connection_closed.call_args_list), 1)
