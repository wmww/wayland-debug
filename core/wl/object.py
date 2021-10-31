import logging
from typing import Optional

from interfaces import ObjectDB
from core.util import *

logger = logging.getLogger(__name__)

class ObjectBase:
    def __init__(self, obj_id: int) -> None:
        assert obj_id > 0
        self.id = obj_id
        self.generation: Optional[int] = None
        self.type: Optional[str] = None
        self.create_time: Optional[float] = None
        self.destroy_time: Optional[float] = None
        self.alive = True

    def resolve(self, db: ObjectDB) -> 'ObjectBase':
        return self

    def type_str(self) -> str:
        if self.type:
            return self.type
        else:
            return color(bad_color, '???')

    def id_str(self) -> str:
        ret = color(object_id_symbol_color, '@') + color(object_id_color, str(self.id))
        if self.generation == None:
            ret += color(object_id_symbol_color, '#') + color(bad_color, '?')
        else:
            ret += color(object_id_symbol_color, '#') + color(object_id_color, str(self.generation))
        return ret

    def to_str(self) -> str:
        return color(object_type_color if self.type else bad_color, self.type_str()) + self.id_str()

    def __str__(self) -> str:
        return self.to_str()

    def owned_by_server(self) -> bool:
        # See https://wayland.freedesktop.org/docs/html/ch04.html#sect-Protocol-Creating-Objects
        return self.id >= 0xff000000

    def destroy(self, time: float) -> None:
        self.destroy_time = time
        self.alive = False

    def lifespan(self) -> Optional[float]:
        if self.create_time is not None and self.destroy_time is not None:
            return self.destroy_time - self.create_time
        else:
            return None

    def resolved(self) -> bool:
        raise NotImplementedError()

class ResolvedObject(ObjectBase):
    def __init__(self, create_time: float, parent_obj: Optional[ObjectBase], obj_id: int, generation: int, type_name: Optional[str]) -> None:
        assert generation >= 0
        super().__init__(obj_id)
        self.create_time = create_time
        self.parent = parent_obj
        self.generation = generation
        self.type = type_name

    def resolved(self) -> bool:
        return True

class UnresolvedObject(ObjectBase):
    def __init__(self, obj_id: int, type_name: Optional[str]) -> None:
        super().__init__(obj_id)
        self.type = type_name

    def resolve(self, db: ObjectDB) -> ObjectBase:
        try:
            resolved = db.retrieve_object(self.id, -1, self.type)
            assert isinstance(resolved, ObjectBase)
            return resolved
        except RuntimeError as e:
            logger.error('Unable to resolve object ' + str(self) + ': ' + str(e))
            return self

    def __str__(self) -> str:
        return color(bad_color, 'unresolved ') + self.to_str()

    def resolved(self) -> bool:
        return False

class MockObject(ObjectBase):
    def __init__(
        self,
        create_time: float = 0.0,
        id: int = 1,
        generation: int = 0,
        type: Optional[str] = 'mock_type'
    ) -> None:
        super().__init__(id)
        self.create_time = create_time
        self.generation = generation
        self.type = type

    def resolved(self) -> bool:
        return True
