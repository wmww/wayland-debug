from abc import abstractmethod
from typing import Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from . import Connection

class ConnectionList:
    '''Simply a list of wl.Connections that supports adding listeners'''

    class Listener:
        '''Gets notified when connections are opened
        To be notified when connections are closed, register a connection listener
        '''

        @abstractmethod
        def connection_opened(self, connection_list: 'ConnectionList', connection: 'Connection') -> None:
            '''A new connection has been opened'''
            raise NotImplementedError()

    @abstractmethod
    def connections(self) -> Tuple['Connection', ...]:
        '''Get all connections (open and closed) in order they were created'''
        raise NotImplementedError()

    @abstractmethod
    def add_connection_list_listener(self, listener: Listener, catch_up: bool) -> None:
        '''Add a listener to be notified of opened and closed connections
        listener: a ConnectionList.Listener
        catch_up: if to send connection_opened() events for all open and closed connections
        '''
        raise NotImplementedError()

    @abstractmethod
    def remove_connection_list_listener(self, listener: Listener) -> None:
        '''Remove the given listener so it no longer gets notifications'''
        raise NotImplementedError()
