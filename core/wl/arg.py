import logging
from typing import TYPE_CHECKING, List

from core.util import *
from . import protocol

if TYPE_CHECKING:
    from interfaces import Connection
    from . import Message, ObjectBase

class Arg:
    class Base:
        def __init__(self) -> None:
            self.name: Optional[str] = None

        def resolve(self, conn: 'Connection', message: 'Message', index: int) -> None:
            if self.name is None and message.obj.type is not None:
                self.name = protocol.get_arg_name(message.obj.type, message.name, index)

        def value_to_str(self) -> str:
            raise NotImplementedError()

        def __str__(self) -> str:
            if self.name is not None:
                return color(symbol_color, self.name + '=') + self.value_to_str()
            else:
                return self.value_to_str()

    # ints, floats, strings and nulls
    class Primitive(Base):
        pass

    class Int(Primitive):
        def __init__(self, value: int) -> None:
            super().__init__()
            self.value = value
        def resolve(self, conn: 'Connection', message: 'Message', index: int) -> None:
            super().resolve(conn, message, index)
            if message.obj.type is not None:
                labels = protocol.look_up_enum(message.obj.type, message.name, index, self.value)
                if labels:
                    self.labels = labels
        def value_to_str(self) -> str:
            if hasattr(self, 'labels'):
                return (color(int_color, str(self.value)) +
                        color(int_symbol_color, ':') +
                        color(int_symbol_color, '&').join([color(int_color, i) for i in self.labels])
                )
            else:
                return color(int_color, str(self.value))

    class Float(Primitive):
        def __init__(self, value: float) -> None:
            super().__init__()
            self.value = value
        def value_to_str(self) -> str:
            return color(float_color, str(self.value))

    class String(Primitive):
        def __init__(self, value: str) -> None:
            super().__init__()
            self.value = value
        def value_to_str(self) -> str:
            return color(string_color, repr(self.value))

    class Null(Base):
        def __init__(self, type_: Optional[str] = None) -> None:
            super().__init__()
            self.type = type_
        def resolve(self, conn: 'Connection', message: 'Message', index: int) -> None:
            super().resolve(conn, message, index)
            if self.type is None and message.obj.type is not None:
                self.type = protocol.look_up_interface(message.obj.type, message.name, index)

        def value_to_str(self) -> str:
            return color(null_color, 'null ' + (self.type if self.type else '??'))

    class Object(Base):
        def __init__(self, obj: 'ObjectBase', is_new: bool) -> None:
            super().__init__()
            self.obj = obj
            self.is_new = is_new

        def set_type(self, new_type: str) -> None:
            if not self.obj.resolved() and self.obj.type is None:
                self.obj.type = new_type
            assert new_type == self.obj.type, 'Object arg already has type ' + str(self.obj.type) + ', so can not be set to ' + new_type

        def resolve(self, conn: 'Connection', message: 'Message', index: int) -> None:
            super().resolve(conn, message, index)
            if not self.obj.resolved():
                if self.is_new:
                    try:
                        if self.obj.type is None:
                            raise RuntimeError('has no type')
                        conn.create_object(message.timestamp, message.obj, self.obj.id, self.obj.type)
                    except RuntimeError as e:
                        logging.warning('Unable to resolve object argument ' + str(self) + ': ' + str(e))
                self.obj = self.obj.resolve(conn)

        def value_to_str(self) -> str:
            return (color(good_color, 'new ') if self.is_new else '') + str(self.obj)

    class Fd(Base):
        def __init__(self, value: int) -> None:
            super().__init__()
            self.value = value
        def value_to_str(self) -> str:
            return color(fd_color, 'fd ' + str(self.value))

    class Array(Base):
        def __init__(self, values: Optional[List['Arg.Base']] = None) -> None:
            super().__init__()
            self.values = values
        def resolve(self, conn: 'Connection', message: 'Message', index: int) -> None:
            super().resolve(conn, message, index)
            if self.values is not None:
                for v in self.values:
                    v.resolve(conn, message, index)
                    v.name = None # hack to stop names appearing in every array element
        def value_to_str(self) -> str:
            if self.values is not None:
                return (color(array_color, '[') +
                        color(array_color, ', ').join([str(v) for v in self.values]) +
                        color(array_color, ']')
                )
            else:
                return color(array_color, '[...]')

    class Unknown(Base):
        def __init__(self, string: Optional[str] = None) -> None:
            super().__init__()
            self.string = string
        def value_to_str(self) -> str:
            if self.string is None:
                return color(bad_color, '?')
            else:
                return color(bad_color, 'Unknown: ' + repr(self.string))

