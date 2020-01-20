import interfaces
from .connection_impl import ConnectionImpl
from .name_generator import NameGenerator
from . import wl
from .util import new_disseminator_of_type

class ConnectionManager(interfaces.ConnectionIDSink, interfaces.ConnectionList):
    '''The basic implementation of MessageSink and ConnectionList'''

    def __init__(self):
        self.connection_list = [] # List of all connections (open and closed) in the order they were created
        self.open_connections = {} # Maps open connection ids to connection objects
        self.connection_name_generator = NameGenerator()
        self.listener = new_disseminator_of_type(interfaces.ConnectionList.Listener)

    def open_connection(self, time, connection_id, is_server):
        '''Overries method in ConnectionIDSink'''
        assert isinstance(time, float)
        assert isinstance(connection_id, str) and connection_id
        assert isinstance(is_server, bool) or is_server == None # can be none if the value is unknown
        # TODO: replace the close_connection call with this
        # assert connection_id not in self.open_connections
        self.close_connection(time, connection_id)
        name = self.connection_name_generator.next()
        connection = ConnectionImpl(time, name, is_server)
        self.open_connections[connection_id] = connection
        self.connection_list.append(connection)
        self.listener.connection_opened(self, connection)
        return connection

    def close_connection(self, time, connection_id):
        '''Overries method in ConnectionIDSink'''
        assert isinstance(time, float)
        assert isinstance(connection_id, str)
        connection = self.open_connections.get(connection_id)
        if connection:
            del self.open_connections[connection_id]
            # Connection will still be in connection list
            connection.close(time)

    def message(self, connection_id, message):
        '''Overries method in ConnectionIDSink'''
        assert isinstance(connection_id, str)
        assert isinstance(message, wl.Message)
        connection = self.open_connections.get(connection_id)
        assert connection, 'Message sent to connection with ID "' + connection_id + '" which has not been opened'
        connection.message(message)

    def connections(self):
        '''Overries method in ConnectionList'''
        return tuple(self.connection_list)

    def add_connection_list_listener(self, listener, catch_up):
        '''Overries method in ConnectionList'''
        assert isinstance(catch_up, bool)
        if catch_up:
            for conn in self.connection_list:
                listener.connection_opened(self, conn)
        self.listener.add_listener(listener)

    def remove_connection_list_listener(self, listener):
        '''Overries method from ConnectionList'''
        self.listener.remove_listener(listener)
