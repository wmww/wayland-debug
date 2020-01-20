import logging

import interfaces
from core.util import *

logger = logging.getLogger(__name__)

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
    def __init__(self, create_time, parent_obj, obj_id, generation, type_name):
        assert isinstance(create_time, float)
        assert isinstance(parent_obj, Object) or parent_obj is None
        assert isinstance(obj_id, int)
        assert obj_id > 0
        assert isinstance(generation, int)
        assert generation >= 0
        assert isinstance(type_name, str)
        self.create_time = create_time
        self.parent = parent_obj
        self.id = obj_id
        self.generation = generation
        self.type = type_name
        self.destroy_time = None
        self.alive = True

    def destroy(self, time):
        self.destroy_time = time
        self.alive = False

    def __str__(self):
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
        def resolve(self, db):
            assert isinstance(db, interfaces.ObjectDB)
            try:
                resolved = db.retrieve_object(self.id, -1, self.type)
                assert isinstance(resolved, Base)
                return resolved
            except RuntimeError as e:
                logger.error('Unable to resolve object ' + str(self) + ': ' + str(e))
                return self
        def __str__(self):
            return color('1;31', 'unresolved ') + self.to_str()
        def resolved(self):
            return False

class Mock(Base):
    def __init__(self):
        self.id = 1
        self.generation = None
        self.type = 'mock'
        self.create_time = 0.0
    def resolve(self, db):
        return self
    def __str__(self):
        return 'mock object'
    def resolved(self):
        return False
