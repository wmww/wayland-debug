from unittest import TestCase
from unittest.mock import Mock
from wl import *
import connection

class TestUnresolvedObject(TestCase):
    def test_resolves_to_object_returned_by_db(self):
        o = Object.Unresolved(7, None)
        db = Mock(spec=connection.ObjectDB)
        expected_obj = object.Mock()
        db.retrieve_object = Mock(return_value=expected_obj)
        r = o.resolve(db)
        self.assertEqual(r, expected_obj)

    def test_requests_right_object_with_null_type_from_db(self):
        o = Object.Unresolved(7, None)
        db = Mock(spec=connection.ObjectDB)
        expected_obj = object.Mock()
        db.retrieve_object = Mock(return_value=expected_obj)
        o.resolve(db)
        db.retrieve_object.assert_called_once_with(7, -1, None)

    def test_requests_right_object_with_non_null_type_from_db(self):
        o = Object.Unresolved(7, 'some_type')
        db = Mock(spec=connection.ObjectDB)
        expected_obj = object.Mock()
        db.retrieve_object = Mock(return_value=expected_obj)
        o.resolve(db)
        db.retrieve_object.assert_called_once_with(7, -1, 'some_type')

class TestMockObject(TestCase):
    def test_is_object(self):
        o = object.Mock()
        self.assertIsInstance(o, object.Base)

    def test_convert_to_str(self):
        o = object.Mock()
        self.assertTrue(str(o))

    def test_try_to_resolve(self):
        o = object.Mock()
        self.assertFalse(o.resolved())
        db = Mock(spec=connection.ObjectDB)
        o.resolve(db)
        self.assertFalse(o.resolved())

