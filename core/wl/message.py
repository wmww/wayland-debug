from typing import Optional, Tuple

from core.util import *
from interfaces import ObjectDB
from .object import ObjectBase, MockObject
from .arg import Arg
from core.output import Output

class Message:
    # TODO: figure out a way to remove global time offset
    base_time = None

    def __init__(self, abs_time: float, obj: ObjectBase, sent: bool, name: str, args: Tuple[Arg.Base, ...]) -> None:
        if Message.base_time is None:
            Message.base_time = abs_time
        self.timestamp = abs_time - Message.base_time
        self.obj = obj
        self.sent = sent
        self.name = name
        self.args = args
        self.destroyed_obj: Optional[ObjectBase] = None

    def resolve(self, db: ObjectDB) -> None:
        if not self.obj.resolved():
            self.obj = self.obj.resolve(db)
        if self.obj.type == 'wl_registry' and self.name == 'bind':
            assert len(self.args) == 4
            assert isinstance(self.args[1], Arg.String)
            assert isinstance(self.args[3], Arg.Object)
            self.args[3].set_type(self.args[1].value)
        if self.obj == db.wl_display() and self.name == 'delete_id' and len(self.args) > 0:
            first_arg = self.args[0]
            assert isinstance(first_arg, Arg.Int)
            self.destroyed_obj = db.retrieve_object(first_arg.value, -1, None)
            self.destroyed_obj.destroy(self.timestamp)
        for i, arg in enumerate(self.args):
            arg.resolve(db, self, i)

    def used_objects(self) -> Tuple[ObjectBase, ...]:
        result = []
        for i in self.args:
            if isinstance(i, Arg.Object):
                result.append(i.obj)
        if self.destroyed_obj:
            result.append(self.destroyed_obj)
        return tuple(result)

    def __str__(self) -> str:
        destroyed = ''
        if self.destroyed_obj:
            destroyed = (
                color(timestamp_color, ' -- ') +
                color('1;31', 'destroyed ') +
                str(self.destroyed_obj))
            lifespan = self.destroyed_obj.lifespan()
            if lifespan is not None:
                destroyed += color(timestamp_color, ' after {:0.4f}s'.format(lifespan))
        return (
            (color('37', '→ ') if self.sent else '') +
            str(self.obj) + ' ' +
            color(message_color, self.name) + color(timestamp_color, '(') +
            color(timestamp_color, ', ').join([str(i) for i in self.args]) + color(timestamp_color, ')') +
            destroyed +
            (color(timestamp_color, ' ↲') if not self.sent else ''))

    def show(self, out: Output) -> None:
        out.show(color('37', '{:7.4f}'.format(self.timestamp)) + ' ' + str(self))

class MockMessage(Message):
    def __init__(
        self,
        timestamp: float = 0.0,
        obj: ObjectBase = MockObject(),
        sent: bool = False,
        name: str = 'mock_message',
        args: Tuple[Arg.Base, ...] = ()
    ) -> None:
        super().__init__(timestamp, obj, sent, name, args)
