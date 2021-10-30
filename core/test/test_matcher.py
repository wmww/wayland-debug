from unittest import TestCase
from core.matcher import *
from core.wl.object import MockObject
from core.wl.message import MockMessage
from core.wl import Arg

class TestStrMatcher(TestCase):
    def test_plain_string(self):
        m = str_matcher('foo')
        self.assertTrue(m.matches('foo'))
        self.assertFalse(m.matches('bar'))
        self.assertFalse(m.matches(''))
        self.assertFalse(m.matches('foobar'))
        self.assertFalse(m.matches('barfoo'))
        self.assertFalse(m.matches('foo '))

    def test_with_wildcard(self):
        m = str_matcher('foo*')
        self.assertTrue(m.matches('foo'))
        self.assertTrue(m.matches('foobar'))
        self.assertTrue(m.matches('foo '))
        self.assertFalse(m.matches('bar'))
        self.assertFalse(m.matches(''))
        self.assertFalse(m.matches('barfoo'))

    def test_with_only_wildcard(self):
        m = str_matcher('*')
        self.assertTrue(m.matches('foo'))
        self.assertTrue(m.matches('foobar'))
        self.assertTrue(m.matches('foo '))
        self.assertTrue(m.matches('bar'))
        self.assertTrue(m.matches(''))
        self.assertTrue(m.matches('barfoo'))

class TestParsedMessageMatcher(TestCase):
    def test_obj_type(self):
        m = parse('wl_pointer')
        self.assertTrue(m.matches(MockMessage(obj=MockObject(type='wl_pointer'))))
        self.assertFalse(m.matches(MockMessage()))
        self.assertFalse(m.matches(MockMessage(obj=MockObject(type='wl_touch'))))
        self.assertFalse(m.matches(MockMessage(name='wl_pointer')))
        self.assertFalse(m.matches(MockMessage(args=[Arg.Object(MockObject(type='wl_pointer'), False)])))

    def test_obj_type_with_at(self):
        m = parse('wl_pointer@')
        self.assertTrue(m.matches(MockMessage(obj=MockObject(type='wl_pointer'))))
        self.assertFalse(m.matches(MockMessage(name='wl_pointer')))

    def test_obj_type_with_wildcard(self):
        m = parse('wl_*')
        self.assertTrue(m.matches(MockMessage(obj=MockObject(type='wl_pointer'))))
        self.assertTrue(m.matches(MockMessage(obj=MockObject(type='wl_touch'))))
        self.assertFalse(m.matches(MockMessage(obj=MockObject(type='xdg_shell'))))

    def test_obj_type_matches_for_new_obj(self):
        m = parse('wl_pointer')
        self.assertFalse(m.matches(MockMessage(args=[Arg.Object(MockObject(type='wl_pointer'), True)])))

    def test_obj_id(self):
        m = parse('7')
        self.assertTrue(m.matches(MockMessage(obj=MockObject(id=7))))
        self.assertTrue(m.matches(MockMessage(obj=MockObject(id=7, generation=3))))
        self.assertFalse(m.matches(MockMessage(obj=MockObject(id=8))))
        self.assertFalse(m.matches(MockMessage(obj=MockObject(type='7'))))

    def test_obj_id_with_at(self):
        m = parse('@7')
        self.assertTrue(m.matches(MockMessage(obj=MockObject(id=7))))
        self.assertTrue(m.matches(MockMessage(obj=MockObject(id=7, generation=3))))
        self.assertFalse(m.matches(MockMessage(obj=MockObject(id=8))))
        self.assertFalse(m.matches(MockMessage(obj=MockObject(type='7'))))

    def test_obj_id_and_generation(self):
        m = parse('5#3')
        self.assertTrue(m.matches(MockMessage(obj=MockObject(id=5, generation=3))))
        self.assertFalse(m.matches(MockMessage(obj=MockObject(id=5, generation=None))))
        self.assertFalse(m.matches(MockMessage(obj=MockObject(id=5, generation=12))))
        self.assertFalse(m.matches(MockMessage(obj=MockObject(id=12, generation=3))))
        self.assertFalse(m.matches(MockMessage(obj=MockObject(type='5'))))

    def test_obj_id_and_generation_with_at(self):
        m = parse('@5#3')
        self.assertTrue(m.matches(MockMessage(obj=MockObject(id=5, generation=3))))
        self.assertFalse(m.matches(MockMessage(obj=MockObject(id=5, generation=None))))
        self.assertFalse(m.matches(MockMessage(obj=MockObject(id=5, generation=12))))
        self.assertFalse(m.matches(MockMessage(obj=MockObject(id=12, generation=3))))
        self.assertFalse(m.matches(MockMessage(obj=MockObject(type='5'))))

    def test_message_name(self):
        m = parse('.axis')
        self.assertTrue(m.matches(MockMessage(name='axis')))
        self.assertFalse(m.matches(MockMessage()))
        self.assertFalse(m.matches(MockMessage(obj=MockObject(type='axis'))))

    def test_message_name_with_wildcard(self):
        m = parse('.set_*')
        self.assertTrue(m.matches(MockMessage(name='set_foo')))
        self.assertTrue(m.matches(MockMessage(name='set_bar')))
        self.assertFalse(m.matches(MockMessage(name='foobar')))

    def test_obj_type_and_message_name(self):
        m = parse('wl_pointer.motion')
        self.assertTrue(m.matches(MockMessage(obj=MockObject(type='wl_pointer'), name='motion')))
        self.assertFalse(m.matches(MockMessage(obj=MockObject(type='wl_touch'), name='motion')))
        self.assertFalse(m.matches(MockMessage(obj=MockObject(type='wl_pointer'), name='axis')))

    def test_obj_type_and_id(self):
        m = parse('wl_pointer@5')
        self.assertTrue(m.matches(MockMessage(obj=MockObject(type='wl_pointer', id=5))))
        self.assertFalse(m.matches(MockMessage(obj=MockObject(type='wl_touch', id=5))))
        self.assertFalse(m.matches(MockMessage(obj=MockObject(type='wl_pointer', id=8))))

    def test_obj_id_generation_and_message_name(self):
        m = parse('wl_pointer@5#3.motion')
        self.assertTrue(m.matches(MockMessage(obj=MockObject(type='wl_pointer', id=5, generation=3), name='motion')))
        self.assertFalse(m.matches(MockMessage(obj=MockObject(type='wl_touch', id=5, generation=3), name='motion')))
        self.assertFalse(m.matches(MockMessage(obj=MockObject(type='wl_pointer', id=12, generation=3), name='motion')))
        self.assertFalse(m.matches(MockMessage(obj=MockObject(type='wl_pointer', id=5, generation=12), name='motion')))
        self.assertFalse(m.matches(MockMessage(obj=MockObject(type='wl_pointer', id=5, generation=3), name='axis')))
        self.assertFalse(m.matches(MockMessage(name='3.motion')))

    def test_multiple_obj_types(self):
        m = parse('wl_pointer, wl_keyboard')
        self.assertTrue(m.matches(MockMessage(obj=MockObject(type='wl_pointer'))))
        self.assertTrue(m.matches(MockMessage(obj=MockObject(type='wl_keyboard'))))
        self.assertFalse(m.matches(MockMessage(obj=MockObject(type='wl_touch'))))

    def test_exclude_obje_types(self):
        m = parse('wl_* ! wl_keyboard')
        self.assertTrue(m.matches(MockMessage(obj=MockObject(type='wl_pointer'))))
        self.assertFalse(m.matches(MockMessage(obj=MockObject(type='wl_keyboard'))))
        self.assertFalse(m.matches(MockMessage(obj=MockObject(type='xdg_shell'))))

    def test_obj_type_with_multiple_message_names(self):
        m = parse('wl_pointer.[motion, axis]')
        self.assertTrue(m.matches(MockMessage(obj=MockObject(type='wl_pointer'), name='motion')))
        self.assertTrue(m.matches(MockMessage(obj=MockObject(type='wl_pointer'), name='axis')))
        self.assertFalse(m.matches(MockMessage(obj=MockObject(type='wl_pointer'), name='frame')))
        self.assertFalse(m.matches(MockMessage(obj=MockObject(type='wl_touch'), name='motion')))
