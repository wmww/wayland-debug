from util import *

class Object:
    # keys are ids, values are arrays of objects in the order they are created
    db = {}
    display = None

    def look_up_specific(obj_id, obj_generation, type_name = None):
        assert obj_id in Object.db, 'Id ' + str(obj_id) + ' of type ' + str(type_name) + ' not in object database'
        assert obj_generation >= 0 and len(Object.db[obj_id]) > obj_generation, (
            'Invalid generation ' + str(obj_generation) + ' for id ' + str(obj_id))
        obj = Object.db[obj_id][obj_generation]
        if type_name:
            if obj.type:
                assert str_matches(type_name, obj.type), str(obj) + ' expected to be of type ' + type_name
        return obj

    def look_up_most_recent(obj_id, type_name = None):
        obj_generation = 0
        if obj_id in Object.db:
            obj_generation = len(Object.db[obj_id]) - 1
        obj = Object.look_up_specific(obj_id, obj_generation, type_name)
        # This *would* be a useful warning, except somehow callback.done, delete(callback) (though sent in the right
        # order), arrive to the client in the wrong order. I don't know a better workaround then just turning off the check
        # if not obj.alive:
        #    warning(str(obj) + ' used after destroyed')
        return obj

    def __init__(self, obj_id, type_name, parent_obj, create_time):
        assert(isinstance(obj_id, int))
        if obj_id in self.db:
            last_obj = self.db[obj_id][-1]
            assert not last_obj.alive, 'Tried to create object of type ' + type_name + ' with the same id as ' + str(last_obj)
        else:
            self.db[obj_id] = []
        self.generation = len(self.db[obj_id])
        self.db[obj_id].append(self)
        self.type = type_name
        self.id = obj_id
        self.parent = parent_obj
        self.create_time = create_time
        self.destroy_time = None
        self.alive = True

    def destroy(self, time):
        self.destroy_time = None
        self.alive = False

    def type_str(self):
        if self.type:
            return self.type
        else:
            return color('1;31', '[unknown]')

    def __str__(self):
        assert self.db[self.id][self.generation] == self, 'Database corrupted'
        return color('1;37', self.type_str() + '@' + str(self.id) + '.' + str(self.generation))

Object.display = Object(1, 'wl_display', None, 0)

class Arg:
    error_color = '2;33'

    # ints, floats, strings and nulls
    class Primitive:
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

    class Object:
        def __init__(self, obj_id, type_name, is_new):
            self.id = obj_id
            self.type = type_name
            self.is_new = is_new
            self.resolved = False
        def resolve(self, parent_obj, time):
            if self.resolved:
                return True
            if self.is_new:
                self.obj = Object(self.id, self.type, parent_obj, time)
            else:
                self.obj = Object.look_up_most_recent(self.id, self.type)
            del self.id
            del self.type
            self.resolved = True
        def __str__(self):
            if self.resolved:
                return (color('1;32', 'new ') if self.is_new else '') + str(self.obj)
            else:
                return color(Arg.error_color, ('New u' if self.is_new else 'U') + 'nresolved object: ' + self.type + '@' + str(self.id))

    class Fd:
        def __init__(self, value):
            self.value = value
        def __str__(self):
            return color('36', 'fd ' + str(self.value))

    class Unknown:
        def __init__(self, string):
            assert isinstance(string, str)
            self.string = string
        def __str__(self):
            return color(Arg.error_color, 'Unknown: ' + repr(self.string))

class Message:
    base_time = None

    def __init__(self, abs_time, obj, sent, name, args):
        if Message.base_time == None:
            Message.base_time = abs_time
        self.timestamp = abs_time - Message.base_time
        self.obj = obj
        self.sent = sent
        self.name = name
        self.args = args
        self.destroyed_obj = None

    def resolve_objects(self, session):
        if self.obj.type == 'wl_registry' and self.name == 'bind':
            self.args[3].type = self.args[1].value
        if self.obj == Object.display and self.name == 'delete_id':
            self.destroyed_obj = Object.look_up_most_recent(self.args[0].value, None)
            self.destroyed_obj.destroy(self.timestamp)
        for i in self.args:
            if isinstance(i, Arg.Object):
                i.resolve(self.obj, self.timestamp)

    def used_objects(self):
        result = []
        for i in self.args:
            if isinstance(i, Arg.Object):
                if i.resolved:
                    result.append(i.obj)
                else:
                    warning('used_objects() called on message with unresolved object')
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
            color('37', '{:10.4f}'.format(self.timestamp) + (' →  ' if self.sent else ' ') +
            str(self.obj) + ' ' +
            color(message_color, self.name + '(') +
            color(message_color, ', ').join([str(i) for i in self.args]) + color(message_color, ')')) +
            destroyed +
            color(timestamp_color, ' ↲' if not self.sent else ''))

if __name__ == '__main__':
    print('File meant to be imported, not run')
    exit(1)
