from typing import Optional
from interfaces import ConnectionIDSink, ConnectionList, Connection
from .connection_impl import ConnectionImpl
from .name_generator import NameGenerator
from . import wl
from .util import new_disseminator_of_type

class ConnectionManager(ConnectionIDSink, ConnectionList):
    '''The basic implementation of MessageSink and ConnectionList'''

    def __init__(self) -> None:
        self.connection_list: list[ConnectionImpl] = [] # List of all connections (open and closed) in the order they were created
        self.open_connections: dict[str, ConnectionImpl] = {} # Maps open connection ids to connection objects
        self.connection_name_generator = NameGenerator()
        self.listener = new_disseminator_of_type(ConnectionList.Listener)

    def open_connection(self, time: float, connection_id: str, is_server: Optional[bool]) -> Connection:
        '''Overries method in ConnectionIDSink'''
        assert connection_id
        # TODO: replace the close_connection call with this
        # assert connection_id not in self.open_connections
        self.close_connection(time, connection_id)
        name = self.connection_name_generator.next()
        connection = ConnectionImpl(time, name, is_server)
        self.open_connections[connection_id] = connection
        self.connection_list.append(connection)
        self.listener.connection_opened(self, connection)
        return connection

    def close_connection(self, time: float, connection_id: str) -> None:
        '''Overries method in ConnectionIDSink'''
        connection = self.open_connections.get(connection_id)
        if connection:
            del self.open_connections[connection_id]
            # Connection will still be in connection list
            connection.close(time)

    def message(self, connection_id: str, message: wl.Message) -> None:
        '''Overries method in ConnectionIDSink'''
        connection = self.open_connections.get(connection_id)
        assert connection, 'Message sent to connection with ID "' + connection_id + '" which has not been opened'
        connection.message(message)

    def connections(self) -> tuple[Connection, ...]:
        '''Overries method in ConnectionList'''
        return tuple(self.connection_list)

    def add_connection_list_listener(self, listener: ConnectionList.Listener, catch_up: bool) -> None:
        '''Overries method in ConnectionList'''
        if catch_up:
            for conn in self.connection_list:
                listener.connection_opened(self, conn)
        self.listener.add_listener(listener)

    def remove_connection_list_listener(self, listener: ConnectionList.Listener) -> None:
        '''Overries method from ConnectionList'''
        self.listener.remove_listener(listener)
