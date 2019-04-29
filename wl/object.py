from util import *

class Base:
    def type_str(self):
        if self.type:
            return self.type
        else:
            return color('1;31', '???')
    def id_str(self):
        ret = str(self.id)
        if self.generation == None:
            ret += '.' + color('1;31', '?')
        else:
            ret += '.' + str(self.generation)
        return ret
    def to_str(self):
        return color('1;36' if self.type else '1;31', self.type_str()) + color('37', '@') + color('1;37', self.id_str())
    def lifespan(self):
        if not hasattr(self, 'create_time') or not hasattr(self, 'destroy_time') or self.destroy_time == None:
            return None
        else:
            return self.destroy_time - self.create_time
    def resolved(self):
        raise NotImplementedError()

class Object(Base):
    def __init__(self, connection, obj_id, type_name, parent_obj, create_time):
        assert isinstance(obj_id, int)
        assert obj_id > 0
        assert isinstance(type_name, str)
        assert isinstance(parent_obj, Object) or (parent_obj == None and obj_id == 1)
        assert isinstance(create_time, float) or isinstance(create_time, int)
        if obj_id > 100000:
            connection.out.warn(
                (type_name if type_name else 'Object') +
                ' ID ' + str(obj_id) + ' is probably bigger than it should be (see https://github.com/wmww/wayland-debug/issues/6)')
        if obj_id in connection.db:
            last_obj = connection.db[obj_id][-1]
            if last_obj.alive:
                if type_name == 'wl_registry' and obj_id == 2:
                    msg = ('It looks like multiple Wayland connections were made, without a way to distinguish between them. '
                        + 'Please see https://github.com/wmww/wayland-debug/issues/5 for further details')
                    connection.out.error(msg)
                    raise RuntimeError(msg)
                else:
                    raise RuntimeError('Tried to create object of type '
                        + type_name + ' with the same id as ' + str(last_obj))
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

    def resolved(self):
        return True

    class Unresolved(Base):
        def __init__(self, obj_id, type_name):
            assert isinstance(obj_id, int)
            assert obj_id > 0
            assert isinstance(type_name, str) or type_name == None
            self.id = obj_id
            self.generation = None
            self.type = type_name
            self.create_time = 0
        def resolve(self, connection):
            try:
                return connection.look_up_most_recent(self.id, self.type)
            except RuntimeError as e:
                connection.out.warn(str(e))
                return self
        def __str__(self):
            return color('1;31', 'unresolved ') + self.to_str()
        def resolved(self):
            return False

