from unittest import TestCase
from unittest.mock import Mock

import interfaces
from core.wl import *
from core.wl.object import MockObject

class TestUnresolvedObject(TestCase):
    def test_resolves_to_object_returned_by_db(self):
        o = UnresolvedObject(7, None)
        db = Mock(spec=interfaces.ObjectDB)
        expected_obj = MockObject()
        db.retrieve_object = Mock(return_value=expected_obj)
        r = o.resolve(db)
        self.assertEqual(r, expected_obj)

    def test_requests_right_object_with_null_type_from_db(self):
        o = UnresolvedObject(7, None)
        db = Mock(spec=interfaces.ObjectDB)
        expected_obj = MockObject()
        db.retrieve_object = Mock(return_value=expected_obj)
        o.resolve(db)
        db.retrieve_object.assert_called_once_with(7, -1, None)

    def test_requests_right_object_with_non_null_type_from_db(self):
        o = UnresolvedObject(7, 'some_type')
        db = Mock(spec=interfaces.ObjectDB)
        expected_obj = MockObject()
        db.retrieve_object = Mock(return_value=expected_obj)
        o.resolve(db)
        db.retrieve_object.assert_called_once_with(7, -1, 'some_type')

class TestMockObject(TestCase):
    def test_is_object(self):
        o = MockObject()
        self.assertIsInstance(o, ObjectBase)

    def test_convert_to_str(self):
        o = MockObject()
        self.assertTrue(str(o))

