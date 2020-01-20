import unittest
from core.util import *
import os

class TestDisseminator(unittest.TestCase):
    @generate_disseminator
    class Listener:
        def __init__(self):
            self.a = 0
        def method_a(self):
            self.a += 1
        def method_b(self, foo, **kwargs):
            self.foo = foo
            self.bar = kwargs['bar']
        def _priv(self):
            self.priv = True

    def setUp(self):
        self.diss = type(self).Listener.Disseminator()

    def add_listener(self):
        self.l = type(self).Listener()
        self.diss.add_listener(self.l)

    def test_disseminator_class_name(self):
        self.assertEqual(type(self).Listener.Disseminator.__name__, 'ListenerDisseminator')

    def test_can_not_make_disseminator_twice_for_one_class(self):
        with self.assertRaises(AssertionError):
            generate_disseminator(type(self).Listener)

    def test_init_not_overidden(self):
        assert hasattr(self.diss, 'a')

    def test_init_with_args_not_overidden(self):
        @generate_disseminator
        class Listener:
            def __init__(self, foo, **kwargs):
                self.foo = foo
                self.bar = kwargs['bar']
        diss = Listener.Disseminator('abc', bar=4)
        self.assertEqual(diss.foo, 'abc')
        self.assertEqual(diss.bar, 4)

    def test_underscore_methods_not_overidden(self):
        assert hasattr(self.diss, 'a')

    def test_create_disseminator(self):
        self.diss.method_a()

    def test_can_not_add_listener_to_disseminator_twice(self):
        self.add_listener()
        with self.assertRaises(AssertionError):
            self.diss.add_listener(self.l)

    def test_add_listener_to_disseminator(self):
        self.add_listener()
        self.assertEqual(self.l.a, 0)
        self.diss.method_a()
        self.assertEqual(self.l.a, 1)

    def test_remove_listener_from_disseminator(self):
        self.add_listener()
        self.diss.remove_listener(self.l)
        self.diss.method_a()
        self.assertEqual(self.l.a, 0)

    def test_can_not_remove_nonexistant_disseminator(self):
        self.l = type(self).Listener()
        with self.assertRaises(ValueError):
            self.diss.remove_listener(self.l)

    def test_disseminator_calls_method_with_arguments(self):
        self.add_listener()
        self.diss.method_b('abc', bar=67)
        self.assertEqual(self.l.foo, 'abc')
        self.assertEqual(self.l.bar, 67)

    def test_disseminator_does_not_run_methods_on_itself(self):
        self.diss.method_a()
        self.diss.method_b('abc', bar=67)
        self.assertEqual(self.diss.a, 0)
        self.assertFalse(hasattr(self.diss, 'foo'))
        self.assertFalse(hasattr(self.diss, 'bar'))

    def test_can_add_multiple_listeners(self):
        ll = [type(self).Listener() for _ in range(3)]
        for l in ll:
            self.diss.add_listener(l)
        self.diss.method_a()
        self.diss.method_b('abc', bar=67)
        for l in ll:
            self.assertEqual(l.a, 1)
            self.assertEqual(l.foo, 'abc')
            self.assertEqual(l.bar, 67)

    def test_can_remove_one_of_multiple_listeners(self):
        ll = [type(self).Listener() for _ in range(3)]
        for l in ll:
            self.diss.add_listener(l)
        self.diss.method_a()
        self.diss.remove_listener(ll[1])
        self.diss.method_a()
        self.assertEqual(ll[0].a, 2)
        self.assertEqual(ll[1].a, 1)
        self.assertEqual(ll[2].a, 2)

    def test_new_disseminator_of_type_only_generates_once(self):
        class Listener:
            def __init__(self):
                pass
        diss0 = new_disseminator_of_type(Listener)
        diss1 = new_disseminator_of_type(Listener)
        self.assertEqual(type(diss0), type(diss1))

    def test_new_disseminator_of_type_takes_args(self):
        class Listener:
            def __init__(self, foo, **kwargs):
                self.foo = foo
                self.bar = kwargs['bar']
        diss = new_disseminator_of_type(Listener, 'abc', bar=4)
        self.assertEqual(diss.foo, 'abc')
        self.assertEqual(diss.bar, 4)
