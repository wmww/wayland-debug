from abc import abstractmethod
from typing import Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core import wl

class Connection():
    '''A single Wayland client-server connection'''

    class Sink:
        '''Used to update connection state'''

        @abstractmethod
        def message(self, message: 'wl.Message') -> None:
            '''Process a new message'''
            raise NotImplementedError()

        @abstractmethod
        def close(self, time: float) -> None:
            '''Close the connection
            time: the time the connection was closed
            '''
            raise NotImplementedError()

    class Listener:
        '''Implement to be notified of connection state changes'''

        @abstractmethod
        def connection_str_changed(self, connection: 'Connection') -> None:
            '''Called whenever str(connection) may return different output'''
            raise NotImplementedError()

        @abstractmethod
        def connection_app_id_set(self, connection: 'Connection', new_app_id: str) -> None:
            '''Called when connection.app_id has been changed'''
            raise NotImplementedError()

        @abstractmethod
        def connection_got_new_message(self, connection: 'Connection', message: 'wl.Message') -> None:
            '''Called when a new message has been processed'''
            raise NotImplementedError()

        @abstractmethod
        def connection_closed(self, connection: 'Connection') -> None:
            '''Called only once when the connection is closed'''
            raise NotImplementedError()

    @abstractmethod
    def name(self) -> str:
        '''Returns the name the connection was created with'''
        raise NotImplementedError()

    @abstractmethod
    def is_server(self) -> Optional[bool]:
        '''Returns if this connection is a server or client, or None if unknown'''
        raise NotImplementedError()

    @abstractmethod
    def messages(self) -> Tuple['wl.Message', ...]:
        '''Returns a tuple of all messages in order they were processed'''
        raise NotImplementedError()

    @abstractmethod
    def is_open(self) -> bool:
        '''Returns if this connection is currently open'''
        raise NotImplementedError()

    @abstractmethod
    def app_id(self) -> Optional[str]:
        '''Returns the app's app_id if detected or None'''
        raise NotImplementedError()

    @abstractmethod
    def create_object(self, time: float, parent: 'wl.ObjectBase', obj_id: int, type_name: str) -> 'wl.ObjectBase':
        '''Create a new objects and add it to the database
        time: the time to create the object with
        parent: the object that created this object
        obj_id: the ID for the new object
        type_name: the Wayland type (such as 'wl_pointer')
        '''
        raise NotImplementedError()

    @abstractmethod
    def retrieve_object(self, id: int, generation: int, type_name: Optional[str]) -> 'wl.ObjectBase':
        '''Get an object
        id: the objects's Wayland ID (database can contain multiple objects with the same ID)
        generation: 0 for first object with the given ID, 1 for 2nd, -1 for the last, etc.
        type_name: str or None, if set, is used to make sure the object is correct, wildcards allowed
        Raises: RuntimeError if id or generation is invalid, or type_name is not None and doesn't match object's type
        '''
        raise NotImplementedError()

    @abstractmethod
    def wl_display(self) -> 'wl.ObjectBase':
        '''Get the wl_display object every connection has'''
        raise NotImplementedError()

    @abstractmethod
    def __str__(self) -> str:
        '''Describes connection'''
        raise NotImplementedError()

    @abstractmethod
    def add_connection_listener(self, listener: Listener) -> None:
        '''Get notified of connection changes and messages'''
        raise NotImplementedError()

    @abstractmethod
    def remove_connection_listener(self, listener: Listener) -> None:
        '''Stop the given connection listener being notified'''
        raise NotImplementedError()
