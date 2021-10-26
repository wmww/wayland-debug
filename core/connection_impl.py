import logging
from typing import Optional, List, Tuple

from interfaces import Connection, ObjectDB
from .util import *
from . import wl

logger = logging.getLogger(__name__)

class ConnectionImpl(Connection.Sink, Connection, ObjectDB):
    def __init__(self, time: float, name: str, is_server: Optional[bool]) -> None:
        '''Create a new connection
        time: when the connection was created
        name: unique name of the connection, often A, B, C etc
        is_server: if we are on the server or client side of the connection (None if unknown)
        '''
        self._name = name
        self._is_server = is_server
        self.title: Optional[str] = None
        self._app_id: Optional[str] = None
        self.open_time = time
        self.open = True
        # keys are ids, values are arrays of objects in the order they are created
        self.message_list: List[wl.Message] = []
        self.display = wl.ResolvedObject(0.0, None, 1, 0, 'wl_display')
        self.db = {1: [self.display]}
        self.listener = new_disseminator_of_type(Connection.Listener)

    def message(self, message: wl.Message) -> None:
        '''Overrides method in Connection.Sink'''
        if not self.open:
            logger.warning(
                'Connection ' + self._name + ' (' + str(self) + ')' +
                ' got message ' + str(message) + ' after it had been closed')
        self.message_list.append(message)
        message.resolve(self)
        self.listener.connection_got_new_message(self, message)
        try:
            if message.name == 'set_app_id':
                assert isinstance(message.args[0], wl.Arg.String)
                app_id = message.args[0].value
                self._set_app_id(app_id)
                self._set_title(app_id.rsplit('.', 1)[-1])
            elif message.name == 'set_title' and not self.title: # this isn't as good as set_app_id, so don't overwrite
                assert isinstance(message.args[0], wl.Arg.String)
                self._set_title(message.args[0].value)
            elif message.name == 'get_layer_surface':
                assert isinstance(message.args[4], wl.Arg.String)
                self._set_title(message.args[4].value)
        except Exception as e: # Connection name is a non-critical feature, so don't be mean if something goes wrong
            logger.error('Could not set connection name: ' + str(e))

    def close(self, time: float) -> None:
        '''Overrides method in Connection.Sink'''
        self.open = False
        self.close_time = time
        self.listener.connection_closed(self)
        self.listener.connection_str_changed(self)

    def name(self) -> str:
        '''Overrides method in Connection'''
        return self._name

    def is_server(self) -> Optional[bool]:
        '''Overrides method in Connection'''
        return self._is_server

    def messages(self) -> Tuple[wl.Message, ...]:
        '''Overrides method in Connection'''
        return tuple(self.message_list)

    def is_open(self) -> bool:
        '''Overrides method in Connection'''
        return self.open

    def app_id(self) -> Optional[str]:
        '''Overrides method in Connection'''
        return self._app_id

    def __str__(self) -> str:
        '''Overrides method in Connection'''
        txt = ''
        txt += color('1;37', self._name) + ' ('
        if self._is_server == True:
            txt += 'server'
        elif self._is_server == False:
            txt += 'client'
        else:
            txt += color('1;31', 'unknown type')
        if self.title:
            if self._is_server:
                txt += ' to'
            txt += ' ' + self.title
        if not self.open:
            txt += ', ' + color('1;31', 'closed')
        txt += ')'
        return txt

    def add_connection_listener(self, listener: Connection.Listener) -> None:
        '''Overrides method in Connection'''
        self.listener.add_listener(listener)

    def remove_connection_listener(self, listener: Connection.Listener) -> None:
        '''Overrides method in Connection'''
        self.listener.remove_listener(listener)

    def create_object(self, time: float, parent: wl.ObjectBase, obj_id: int, type_name: str) -> wl.ObjectBase:
        '''Overrides method in ObjectDB'''
        if obj_id <= 1:
            raise RuntimeError('Invalid object ID ' + str(obj_id))
        if obj_id in self.db:
            last_obj = self.db[obj_id][-1]
            if last_obj.alive:
                if type_name == 'wl_registry' and obj_id == 2:
                    msg = ('It looks like multiple Wayland connections were made, without a way to distinguish between them. '
                        + 'Please see https://github.com/wmww/wayland-debug/issues/5 for further details')
                    logger.error(msg)
                    raise RuntimeError(msg)
                elif last_obj.owned_by_server():
                    # We don't get .delete_id events for server-owned objects, so we have to delete them implicitly
                    last_obj.destroy(time)
                else:
                    raise RuntimeError(
                        'Tried to create object of type '
                        + str(type_name) + ' with the same id as ' + str(last_obj))
        else:
            self.db[obj_id] = []
        generation = len(self.db[obj_id])
        obj = wl.ResolvedObject(time, parent, obj_id, generation, type_name)
        self.db[obj_id].append(obj)
        return obj

    def retrieve_object(self, id: int, generation: int, type_name: Optional[str]) -> wl.ObjectBase:
        '''Overrides method in ObjectDB'''
        try:
            obj_list = self.db[id]
        except KeyError as e:
            raise RuntimeError('Id ' + str(id) + ' not in object database') from e
        try:
            obj = obj_list[generation]
        except IndexError as e:
            raise RuntimeError('Invalid generation ' + str(generation) + ' for id ' + str(id)) from e
        if ((type_name is not None) and
            (obj.type is not None) and
            (not str_matches(type_name, obj.type))
        ):
            raise RuntimeError(str(obj) + ' expected to be of type ' + type_name)
        return obj

    def wl_display(self) -> wl.ObjectBase:
        '''Overrides method in ObjectDB'''
        return self.display

    def _set_title(self, title: str) -> None:
        assert isinstance(title, str) and title
        self.title = title
        self.listener.connection_str_changed(self)

    def _set_app_id(self, app_id: str) -> None:
        assert isinstance(app_id, str) and app_id
        self._app_id = app_id
        self.listener.connection_app_id_set(self, app_id)
