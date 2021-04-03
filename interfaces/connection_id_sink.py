from abc import abstractmethod
from typing import Optional
from core import wl
from . import Connection

class ConnectionIDSink:
    '''Receives messages and connection created/deleted events based on a unique connection ID'''

    @abstractmethod
    def open_connection(self, time: float, connection_id: str, is_server: Optional[bool]) -> Connection:
        '''Open a new client-server connection
        time: what is returned by time.perf_counter() will do
        connection_id: unique identifier of the connection (only used internally, never shown to user)
        is_server: if this connection is a server or a client (can be None if value is unknown)
        returns: the newly created connection
        '''
        # TODO: make return None
        raise NotImplementedError()

    @abstractmethod
    def close_connection(self, time: float, connection_id: str) -> None:
        '''Close the given connection
        time: what is returned by time.perf_counter() will do
        connection_id: the unique ID the connection was created with
        '''
        raise NotImplementedError()

    @abstractmethod
    def message(self, connection_id: str, message: wl.Message) -> None:
        '''Process a new message
        connection_id: the unique ID of the connection this message was on
        message: the message
        '''
        raise NotImplementedError()
