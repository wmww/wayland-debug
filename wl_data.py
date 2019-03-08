from util import *

class Connection:
    def __init__(self, name, is_server, title, time, output):
        self.name = name
        self.is_server = is_server
        self.title = title
        self.open_time = time
        self.open = True
        self.out = output
        # keys are ids, values are arrays of objects in the order they are created
        self.db = {}
        self.messages = []
        self.display = Object(self, 1, 'wl_display', None, 0)

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
        assert obj_id in self.db, 'Id ' + str(obj_id) + ' of type ' + str(type_name) + ' not in object database'
        assert obj_generation >= 0 and len(self.db[obj_id]) > obj_generation, (
            'Invalid generation ' + str(obj_generation) + ' for id ' + str(obj_id))
        obj = self.db[obj_id][obj_generation]
        if type_name:
            if obj.type:
                assert str_matches(type_name, obj.type), str(obj) + ' expected to be of type ' + type_name
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

    def message(self, message):
        if not self.open:
            self.out.warn('Connection ' + self.name + ' (' + self.description() + ') got message ' + str(message) + ' after it had been closed')
            self.open = True
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

class ObjBase:
    def type_str(self):
        if self.type:
            return self.type
        else:
            return '???'
    def id_str(self):
        ret = str(self.id)
        if self.generation == None:
            ret += '.?'
        else:
            ret += '.' + str(self.generation)
        return ret
    def to_str(self):
        return color('1;36' if self.type else '1;31', self.type_str()) + color('37', '@') + color('1;37', self.id_str())

class Object(ObjBase):
    def __init__(self, connection, obj_id, type_name, parent_obj, create_time):
        assert isinstance(obj_id, int)
        assert obj_id > 0
        assert isinstance(type_name, str)
        assert isinstance(parent_obj, Object) or (parent_obj == None and obj_id == 1)
        assert isinstance(create_time, float) or isinstance(create_time, int)
        if obj_id in connection.db:
            last_obj = connection.db[obj_id][-1]
            assert not last_obj.alive, 'Tried to create object of type ' + type_name + ' with the same id as ' + str(last_obj)
        else:
            connection.db[obj_id] = []
        self.generation = len(connection.db[obj_id])
        connection.db[obj_id].append(self)
        self.connection = connection
        self.type = type_name
        self.id = obj_id
        self.parent = parent_obj
        self.create_time = create_time
        self.destroy_time = None
        self.alive = True

    def destroy(self, time):
        self.destroy_time = time
        self.alive = False

    def __str__(self):
        assert self.connection.db[self.id][self.generation] == self, 'Database corrupted'
        return self.to_str()

    class Unresolved(ObjBase):
        def __init__(self, obj_id, type_name):
            assert isinstance(obj_id, int)
            assert obj_id > 0
            assert isinstance(type_name, str) or type_name == None
            self.id = obj_id
            self.generation = None
            self.type = type_name
        def resolve(self, connection):
            if self.id > 100000:
                warning('Ignoreing unreasonably large ID ' + str(self.id) + ' as it is likely to cause an error')
                return self
            return connection.look_up_most_recent(self.id, self.type)
        def __str__(self):
            return color('1;31', 'unresolved<') + self.to_str() + color('1;31', '>')

class ArgBase:
    pass

class Arg:
    error_color = '2;33'

    # ints, floats, strings and nulls
    class Primitive(ArgBase):
        def __init__(self, value):
            self.value = value
        def __str__(self):
            if isinstance(self.value, int):
                return color('1;34', str(self.value))
            elif isinstance(self.value, float):
                return color('1;35', str(self.value))
            elif isinstance(self.value, str):
                return color('1;33', repr(self.value))
            elif self.value == None:
                return color('37', 'null')
            else:
                return color(Arg.error_color, type(self.value).__name__ + ': ' + repr(self.value))

    class Object(ArgBase):
        def __init__(self, obj, is_new):
            assert isinstance(obj, ObjBase)
            assert isinstance(is_new, bool)
            self.obj = obj
            self.is_new = is_new
        def set_type(self, new_type):
            if isinstance(self.obj, Object.Unresolved) and self.obj.type == None:
                self.obj.type = new_type
            assert new_type == self.obj.type, 'Object arg already has type ' + self.obj.type + ', so can not be set to ' + new_type
        def resolve(self, connection, parent_obj, time):
            if isinstance(self.obj, Object.Unresolved):
                if self.is_new:
                    Object(connection, self.obj.id, self.obj.type, parent_obj, time)
                self.obj = self.obj.resolve(connection)
        def __str__(self):
            return (color('1;32', 'new ') if self.is_new else '') + str(self.obj)

    class Fd(ArgBase):
        def __init__(self, value):
            self.value = value
        def __str__(self):
            return color('36', 'fd ' + str(self.value))

    class Unknown(ArgBase):
        def __init__(self, string):
            assert isinstance(string, str)
            self.string = string
        def __str__(self):
            return color(Arg.error_color, 'Unknown: ' + repr(self.string))

class Message:
    base_time = None

    def __init__(self, abs_time, obj, sent, name, args):
        assert isinstance(abs_time, float) or isinstance(abs_time, int)
        assert isinstance(obj, ObjBase)
        assert isinstance(sent, bool)
        assert isinstance(name, str)
        for arg in args:
            assert isinstance(arg, ArgBase)
        if Message.base_time == None:
            Message.base_time = abs_time
        self.timestamp = abs_time - Message.base_time
        self.obj = obj
        self.sent = sent
        self.name = name
        self.args = args
        self.destroyed_obj = None

    def resolve(self, connection):
        if isinstance(self.obj, Object.Unresolved):
            self.obj = self.obj.resolve(connection)
        if self.obj.type == 'wl_registry' and self.name == 'bind':
            assert isinstance(self.args[3], Arg.Object)
            self.args[3].set_type(self.args[1].value)
        if self.obj == connection.display and self.name == 'delete_id' and len(self.args) > 0:
            self.destroyed_obj = connection.look_up_most_recent(self.args[0].value, None)
            self.destroyed_obj.destroy(self.timestamp)
        for i in self.args:
            if isinstance(i, Arg.Object):
                i.resolve(connection, self.obj, self.timestamp)

    def used_objects(self):
        result = []
        for i in self.args:
            if isinstance(i, Arg.Object):
                result.append(i.obj)
        if self.destroyed_obj:
            result.append(self.destroyed_obj)
        return result

    def __str__(self):
        destroyed = ''
        if self.destroyed_obj:
            destroyed = (
                color(timestamp_color, ' [') +
                color('1;31', 'destroyed ') +
                str(self.destroyed_obj) +
                color(timestamp_color, ']'))
        return (
            (' ' + color('37', '→  ') if self.sent else '') +
            str(self.obj) + ' ' +
            color(message_color, self.name + '(') +
            color(message_color, ', ').join([str(i) for i in self.args]) + color(message_color, ')') +
            destroyed +
            (color(timestamp_color, ' ↲') if not self.sent else ''))

    def show(self, out):
        out.show(color('37', '{:8.4f}'.format(self.timestamp)) + ' ' + str(self))

if __name__ == '__main__':
    print('File meant to be imported, not run')
    exit(1)
