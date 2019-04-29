from util import *
from . import object
from . import protocol

class Arg:
    error_color = '1;31'

    class Base:
        def resolve(self, connection, message, index):
            try:
                name = protocol.get_arg_name(message.obj.type, message.name, index)
                if name:
                    self.name = name
            except RuntimeError as e:
                connection.out.warn(e)
        def __str__(self):
            if hasattr(self, 'name'):
                return color('37', self.name + '=') + self.value_to_str()
            else:
                return self.value_to_str()

    # ints, floats, strings and nulls
    class Primitive(Base):
        def __init__(self, value):
            self.value = value

    class Int(Primitive):
        def resolve(self, connection, message, index):
            super().resolve(connection, message, index)
            try:
                labels = protocol.look_up_enum(message.obj.type, message.name, index, self.value)
                if labels:
                    self.labels = labels
            except RuntimeError as e:
                connection.out.warn(e)
        def value_to_str(self):
            assert isinstance(self.value, int)
            if hasattr(self, 'labels'):
                return color('1;34', str(self.value)) + color('34', ':') + color('34', '&').join([color('1;34', i) for i in self.labels])
            else:
                return color('1;34', str(self.value))

    class Float(Primitive):
        def value_to_str(self):
            assert isinstance(self.value, float)
            return color('1;35', str(self.value))

    class String(Primitive):
        def value_to_str(self):
            assert isinstance(self.value, str)
            return color('1;33', repr(self.value))

    class Null(Base):
        def __init__(self, type_=None):
            assert isinstance(type_, str) or type_ == None
            self.type = type_
        def resolve(self, connection, message, index):
            super().resolve(connection, message, index)
            if not self.type:
                try:
                    self.type = protocol.look_up_interface(message.obj.type, message.name, index)
                except RuntimeError as e:
                    connection.out.warn(e)

        def value_to_str(self):
            return color('1;37', 'null ' + (self.type if self.type else '??'))

    class Object(Base):
        def __init__(self, obj, is_new):
            assert isinstance(obj, object.Base)
            assert isinstance(is_new, bool)
            self.obj = obj
            self.is_new = is_new
        def set_type(self, new_type):
            if not self.obj.resolved() and self.obj.type == None:
                self.obj.type = new_type
            assert new_type == self.obj.type, 'Object arg already has type ' + self.obj.type + ', so can not be set to ' + new_type
        def resolve(self, connection, message, index):
            super().resolve(connection, message, index)
            if not self.obj.resolved():
                if self.is_new:
                    try:
                        object.Object(connection, self.obj.id, self.obj.type, message.obj, message.timestamp)
                    except RuntimeError as e:
                        connection.out.error(e)
                self.obj = self.obj.resolve(connection)
        def value_to_str(self):
            return (color('1;32', 'new ') if self.is_new else '') + str(self.obj)

    class Fd(Base):
        def __init__(self, value):
            assert isinstance(value, int)
            self.value = value
        def value_to_str(self):
            return color('36', 'fd ' + str(self.value))

    class Array(Base):
        def __init__(self, values=None):
            if isinstance(values, list):
                for i in values:
                    assert isinstance(i, Arg.Base)
            else:
                assert values == None
            self.values = values
        def resolve(self, connection, message, index):
            super().resolve(connection, message, index)
            if self.values != None:
                for v in self.values:
                    v.resolve(connection, message, index)
                    if hasattr(v, 'name'):
                        del v.name # hack to stop names appearing in every array element
        def value_to_str(self):
            if self.values != None:
                return color('1;37', '[') + color('1;37', ', ').join([str(v) for v in self.values]) + color('1;37', ']')
            else:
                return color('1;37', '[...]')

    class Unknown(Base):
        def __init__(self, string=None):
            assert isinstance(string, str) or string == None
            self.string = string
        def value_to_str(self):
            if self.string == None:
                return color(Arg.error_color, '?')
            else:
                return color(Arg.error_color, 'Unknown: ' + repr(self.string))

