from util import *
import wl
from .connection import Connection

class ConnectionImpl(Connection.Sink, Connection):
    def __init__(self, time, name, is_server):
        '''Create a new connection
        time: float, when the connection was created
        name: unique name of the connection, often A, B, C etc
        is_server: bool or None, if we are on the server or client side of the connection (None if unknown)
        '''
        assert isinstance(time, float)
        assert isinstance(name, str)
        assert isinstance(is_server, bool) or is_server is None
        self._name = name
        self.is_server = is_server
        self.title = None
        self.open_time = time
        self.open = True
        # keys are ids, values are arrays of objects in the order they are created
        self.db = {}
        self.message_list = []
        self.display = wl.Object(self, 1, 'wl_display', None, 0)

    def message(self, message):
        '''Overrides method in Connection.Sink'''
        assert isinstance(message, wl.Message)
        if not self.open:
            warning(
                'Connection ' + self._name + ' (' + self.description() + ')' +
                ' got message ' + str(message) + ' after it had been closed')
        self.message_list.append(message)
        message.resolve(self)
        try:
            if message.name == 'set_app_id':
                self._set_title(message.args[0].value.rsplit(',', 1)[-1])
            elif message.name == 'set_title' and not self.title: # this isn't as good as set_app_id, so don't overwrite
                self._set_title(message.args[0].value)
            elif message.name == 'get_layer_surface':
                self._set_title(message.args[4].value)
        except Exception as e: # Connection name is a non-critical feature, so don't be mean if something goes wrong
            warning('Could not set connection name: ' + str(e))

    def close(self, time):
        '''Overrides method in Connection.Sink'''
        self.open = False
        self.close_time = time

    def messages(self):
        '''Overrides method in Connection'''
        return tuple(self.message_list)

    def is_open(self):
        '''Overrides method in Connection'''
        return self.open

    def name(self):
        '''Overrides method in Connection'''
        return self._name

    def __str__(self):
        '''Overrides method in Connection'''
        if self.is_server == True:
            txt = 'server'
        elif self.is_server == False:
            txt = 'client'
        else:
            txt = color('1;31', 'unknown type')
        if self.title:
            if self.is_server:
                txt += ' to'
            txt += ' ' + self.title
        return txt

    def add_connection_listener(self, listener):
        '''Overrides method in Connection'''
        raise NotImplementedError()

    def remove_connection_list_listener(self, listener):
        '''Overrides method in Connection'''
        raise NotImplementedError()

    def _set_title(self, title):
        assert isinstance(title, str)
        self.title = title

    def look_up_specific(self, obj_id, obj_generation, type_name = None):
        if not obj_id in self.db:
            msg = 'Id ' + str(obj_id) + ' of type ' + str(type_name) + ' not in object database'
            if obj_id > 100000:
                msg += ' (see https://github.com/wmww/wayland-debug/issues/6)'
            raise RuntimeError(msg)
        if obj_generation < 0 or len(self.db[obj_id]) <= obj_generation:
            raise RuntimeError('Invalid generation ' + str(obj_generation) + ' for id ' + str(obj_id))
        obj = self.db[obj_id][obj_generation]
        if type_name and obj.type and not str_matches(type_name, obj.type):
            raise RuntimeError(str(obj) + ' expected to be of type ' + type_name)
        return obj

    def look_up_most_recent(self, obj_id, type_name = None):
        obj_generation = 0
        if obj_id in self.db:
            obj_generation = len(self.db[obj_id]) - 1
        obj = self.look_up_specific(obj_id, obj_generation, type_name)
        # This *would* be a useful warning, except somehow callback.done, delete(callback) (though sent in the right
        # order), arrive to the client in the wrong order. I don't know a better workaround then just turning off the check
        # if not obj.alive:
        #    warning(str(obj) + ' used after destroyed')
        return obj

class Mock(Connection):
    def __init__(self):
        self.display = wl.object.Mock()
    def close(self, time):
        pass
    def set_title(self, title):
        pass
    def description(self):
        return 'mock connection'
    def look_up_specific(self, obj_id, obj_generation, type_name = None):
        return wl.object.Mock()
    def look_up_most_recent(self, obj_id, type_name = None):
        return wl.object.Mock()
    def message(self, message):
        pass
