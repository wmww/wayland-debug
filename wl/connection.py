from util import *
from . import object
from output import Output

class Connection:
    class NameGenerator:
        def __init__(self):
            self.name = []

        def next(self):
            self.increment()
            return ''.join(self.name)

        def increment(self, current=None):
            '''Increments a list in place'''
            # If no current letter is specified, start at the right
            if current is None:
                current = len(self.name) - 1
            if current < 0:
                # We have run left past the end of the list without finding a letter to increment
                # We need to add a new letter to the left
                # All other letters have already been set to 'A'
                self.name.insert(0, 'A')
            elif self.name[current] == 'Z':
                # We can't increment this letter any more
                # Set it to 'A' and increment the letter to the left
                self.name[current] = 'A'
                self.increment(current - 1)
            else:
                # Increment the current letter by 1
                self.name[current] = chr(ord(self.name[current]) + 1)

    def __init__(self, name, is_server, title, time, thread, output):
        '''
        Create a new connection
        name: unique name of the connection, often A, B, C etc
        is_server: if we are on the server or client side of the connection
        title: human-readable descriptive title (can be None, and can be changed latar)
        time: the timestamp (in seconds) of the first message on the connection
        thread: Either None if unknown, or an int thread ID that all messages should be on
        output: the Output object the connection will use
        '''
        assert isinstance(name, str)
        assert isinstance(is_server, bool)
        assert isinstance(title, str) or title == None
        assert isinstance(time, float) or isinstance(time, int)
        assert isinstance(thread, int) or thread == None
        assert isinstance(output, Output)
        self.name = name
        self.is_server = is_server
        self.title = title
        self.open_time = time
        self.open = True
        self.thread = thread
        self.out = output
        # keys are ids, values are arrays of objects in the order they are created
        self.db = {}
        self.messages = []
        self.display = object.Object(self, 1, 'wl_display', None, 0)

    def close(self, time):
        self.open = False
        self.close_time = time

    def set_title(self, title):
        assert isinstance(title, str)
        self.title = title

    def description(self):
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

    def message(self, thread, message):
        if not self.open:
            self.out.warn(
                'Connection ' + self.name + ' (' + self.description() + ')' +
                ' got message ' + str(message) + ' after it had been closed')
            self.open = True
        if thread != self.thread:
            self.out.warn(
                'Got message ' + str(message) +
                ' on thread ' + str(thread) +
                ' instead of connection\'s main thread ' + str(self.thread))
        self.messages.append(message)
        message.resolve(self)
        try:
            if message.name == 'set_app_id':
                self.set_title(message.args[0].value.rsplit(',', 1)[-1])
            elif message.name == 'set_title' and not self.title: # this isn't as good as set_app_id, so don't overwrite
                self.set_title(message.args[0].value)
            elif message.name == 'get_layer_surface':
                self.set_title(message.args[4].value)
        except Exception as e: # Connection name is a non-critical feature, so don't be mean if something goes wrong
            self.out.warning('Could not set connection name: ' + str(e))

