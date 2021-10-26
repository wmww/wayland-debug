import logging
from typing import TYPE_CHECKING

from core.util import *
from . import protocol

if TYPE_CHECKING:
    from interfaces import ObjectDB
    from . import Message, ObjectBase

class Arg:
    error_color = '1;31'

    class Base:
        def __init__(self) -> None:
            self.name: Optional[str] = None

        def resolve(self, db: 'ObjectDB', message: 'Message', index: int) -> None:
            if self.name is None and message.obj.type is not None:
                self.name = protocol.get_arg_name(message.obj.type, message.name, index)

        def value_to_str(self) -> str:
            raise NotImplementedError()

        def __str__(self) -> str:
            if self.name is not None:
                return color('37', self.name + '=') + self.value_to_str()
            else:
                return self.value_to_str()

    # ints, floats, strings and nulls
    class Primitive(Base):
        pass

    class Int(Primitive):
        def __init__(self, value: int) -> None:
            super().__init__()
            self.value = value
        def resolve(self, db, message, index):
            super().resolve(db, message, index)
            try:
                labels = protocol.look_up_enum(message.obj.type, message.name, index, self.value)
                if labels:
                    self.labels = labels
            except RuntimeError as e:
                logging.warning('Unable to resolve int argument ' + str(self) + ': ' + str(e))
        def value_to_str(self) -> str:
            if hasattr(self, 'labels'):
                return color('1;34', str(self.value)) + color('34', ':') + color('34', '&').join([color('1;34', i) for i in self.labels])
            else:
                return color('1;34', str(self.value))

    class Float(Primitive):
        def __init__(self, value: float) -> None:
            super().__init__()
            self.value = value
        def value_to_str(self) -> str:
            return color('1;35', str(self.value))

    class String(Primitive):
        def __init__(self, value: str) -> None:
            super().__init__()
            self.value = value
        def value_to_str(self) -> str:
            return color('1;33', repr(self.value))

    class Null(Base):
        def __init__(self, type_: Optional[str] = None) -> None:
            super().__init__()
            self.type = type_
        def resolve(self, db: 'ObjectDB', message: 'Message', index: int) -> None:
            super().resolve(db, message, index)
            if self.type is None and message.obj.type is not None:
                self.type = protocol.look_up_interface(message.obj.type, message.name, index)

        def value_to_str(self) -> str:
            return color('1;37', 'null ' + (self.type if self.type else '??'))

    class Object(Base):
        def __init__(self, obj: 'ObjectBase', is_new: bool) -> None:
            super().__init__()
            self.obj = obj
            self.is_new = is_new

        def set_type(self, new_type: str) -> None:
            if not self.obj.resolved() and self.obj.type is None:
                self.obj.type = new_type
            assert new_type == self.obj.type, 'Object arg already has type ' + str(self.obj.type) + ', so can not be set to ' + new_type

        def resolve(self, db: 'ObjectDB', message: 'Message', index: int) -> None:
            super().resolve(db, message, index)
            if not self.obj.resolved():
                if self.is_new:
                    try:
                        if self.obj.type is None:
                            raise RuntimeError('has no type')
                        db.create_object(message.timestamp, message.obj, self.obj.id, self.obj.type)
                    except RuntimeError as e:
                        logging.warning('Unable to resolve object argument ' + str(self) + ': ' + str(e))
                self.obj = self.obj.resolve(db)

        def value_to_str(self) -> str:
            return (color('1;32', 'new ') if self.is_new else '') + str(self.obj)

    class Fd(Base):
        def __init__(self, value: int) -> None:
            super().__init__()
            self.value = value
        def value_to_str(self) -> str:
            return color('36', 'fd ' + str(self.value))

    class Array(Base):
        def __init__(self, values: Optional[list['Arg.Base']] = None) -> None:
            super().__init__()
            self.values = values
        def resolve(self, db: 'ObjectDB', message: 'Message', index: int) -> None:
            super().resolve(db, message, index)
            if self.values is not None:
                for v in self.values:
                    v.resolve(db, message, index)
                    if hasattr(v, 'name'):
                        del v.name # hack to stop names appearing in every array element
        def value_to_str(self) -> str:
            if self.values is not None:
                return color('1;37', '[') + color('1;37', ', ').join([str(v) for v in self.values]) + color('1;37', ']')
            else:
                return color('1;37', '[...]')

    class Unknown(Base):
        def __init__(self, string: Optional[str] = None) -> None:
            super().__init__()
            self.string = string
        def value_to_str(self) -> str:
            if self.string is None:
                return color(Arg.error_color, '?')
            else:
                return color(Arg.error_color, 'Unknown: ' + repr(self.string))

