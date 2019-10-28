from .message_sink import MessageSink
from output import Output
import wl

class ConnectionManager(MessageSink):
    '''The basic implementation of MessageSink'''

    def __init__(self, output):
        assert isinstance(output, Output)
        self.out = output
        self.connection_list = [] # List of all connections (open and closed) in the order they were created
        self.open_connections = {} # Maps open connection ids to connection objects
        self.connection_name_generator = wl.Connection.NameGenerator()

    def open_connection(self, time, connection_id, is_server):
        '''Overries method from MessageSink'''
        assert isinstance(time, float)
        assert isinstance(connection_id, str) and connection_id
        assert isinstance(is_server, bool) or is_server == None # can be none if the value is unknown
        # TODO: replace the close_connection call with this
        # assert connection_id not in self.open_connections
        self.close_connection(time, connection_id)
        name = self.connection_name_generator.next()
        connection = wl.Connection(name, is_server, None, time, self.out)
        self.open_connections[connection_id] = connection
        self.connection_list.append(connection)
        return connection

    def close_connection(self, time, connection_id):
        '''Overries method from MessageSink'''
        assert isinstance(time, float)
        assert isinstance(connection_id, str)
        connection = self.open_connections.get(connection_id)
        if connection:
            del self.open_connections[connection_id]
            # Connection will still be in connection list
            connection.close(time)

    def message(self, connection_id, message):
        '''Overries method from MessageSink'''
        assert isinstance(connection_id, str)
        assert isinstance(message, wl.Message)
        connection = self.open_connections.get(connection_id)
        assert connection, 'Message sent to connection with ID "' + connection_id + '" which has not been opened'
        connection.message(message)
