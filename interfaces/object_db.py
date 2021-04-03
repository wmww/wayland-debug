from abc import abstractmethod
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core import wl

class ObjectDB:
    '''A queryable database of wl.Objects'''

    @abstractmethod
    def create_object(self, time: float, parent: 'wl.Object', obj_id: int, type_name: str) -> 'wl.Object':
        '''Create a new objects and add it to the database
        time: the time to create the object with
        parent: the object that created this object
        obj_id: the ID for the new object
        type_name: the Wayland type (such as 'wl_pointer')
        '''
        raise NotImplementedError()

    @abstractmethod
    def retrieve_object(self, id: int, generation: int, type_name: Optional[str]) -> 'wl.Object':
        '''Get an object
        id: the objects's Wayland ID (database can contain multiple objects with the same ID)
        generation: 0 for first object with the given ID, 1 for 2nd, -1 for the last, etc.
        type_name: str or None, if set, is used to make sure the object is correct, wildcards allowed
        Raises: RuntimeError if id or generation is invalid, or type_name is not None and doesn't match object's type
        '''
        raise NotImplementedError()

    @abstractmethod
    def wl_display(self) -> 'wl.Object':
        '''Get the wl_display object every connection has'''
        raise NotImplementedError()
