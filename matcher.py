import re

import wl_data as wl
from util import *
import argparse # only used for line wrapping in the help

def print_help():
#                                                                          |
    print('''
Matchers are used throught the program to show and hide messages. A matcher
consists of a comma seporated list of objects. An object is a type name,
and/or an object ID (in which case a generation can also be specified). An
@ goes inbetween the name and ID, and is optional if both are not specified.
A * can be used as a wildcard in type names.''')
    print()
    print('Examples of objects:')
    for i in [
            ('wl_surface  ', 'any wl_surface'),
            ('@5          ', 'the object with ID 5 (@ is optional)'),
            ('@4.12       ', 'the 12th object with ID 4 (@ is optional)'),
            ('wl_surface@6', 'the object with ID 7, which is asserted to be a wl_surface'),
            ('xdg_*@3.2   ', 'the 2nd object with ID 3, which is some sort of XDG type')]:
        print('  ' + color('1;37', i[0]) + ' - Matches ' + i[1])
#                                                                          |
    print('''
Matchers can optionally be followed by a brace enclosed, comma seporated
list of messages. If the object is referenced by a message, it will match
even if the message is not called on that object. Messages can have
wildcards too.''')
    print()
    print('Examples of messages:')
    for i in [
            ('wl_surface[commit]  ', 'commit messages on wl_surfaces'),
            ('@6.2[motion,button] ', 'motion or button messages on the 2nd object with ID 6'),
            ('*_surface[delete_id]', 'delete_id messages on any sort of surface (this works\n' +
             '                         even though the messages themselves are called on the wl_display)')]:
        print('  ' + color('1;37', i[0]) + ' - Matches ' + i[1])
    print()
    print('A complete example of a matcher could look something like:')
    print(color('1;37', '  wl_surface[delete_id,commit],*[destroy],@3.2'))

def make_matcher(matcher, inversed):
    assert matcher
    if isinstance(matcher, list):
        elif len(matchers) == 1:
            matcher = matchers[0]
        else:
            matcher = ListMatcher(matchers)
    if inversed:
        matcher = InverseMatcher(matcher)
    return matcher

# Matches a Wayland object
class ObjectMatcher:
    def __init__(self, type_pattern, obj_id, obj_generation):
        try:
            assert obj_id is not None
            if obj_generation:
                self.obj = wl.Object.look_up_specific(obj_id, obj_generation, type_pattern)
            else:
                self.obj = wl.Object.look_up_most_recent(obj_id, type_pattern)
        except AssertionError:
            self.type = type_pattern
            self.id = obj_id
            self.generation = obj_generation

    def matches(self, obj):
        assert isinstance(obj, wl.Object)
        if self.obj:
            return obj == self.obj
        else:
            if self.id and self.id != obj.id:
                return False
            elif self.generation and self.generation != obj.generation:
                return False
            elif self.type and not str_matches(self.type, obj.type):
                return False
            else:
                return True

    def __str__(self):
        if self.obj:
            return str(self.obj)
        else:
            out = ''
            if self.type:
                out += self.type
                if self.obj_id:
                    out += ' @ '
            if self.obj_id:
                out += int(self.obj_id)
                if self.obj_generation:
                    out += '.' + int(self.obj_generation)
            return color('1;35', out)

# Matches a string (uses wildcards)
class StrMatcher:
    def __init__(self, pattern):
        assert isinstance(pattern, str)
        self.pattern = pattern
    def matches(self, name):
        assert isinstance(name, str)
        return str_matches(self.pattern, name):
    def __str__(self):
        return color('1;35', self.pattern)

# Matches any in a list of matchers
class ListMatcher:
    def __init__(self, matchers):
        self.matchers = matchers
    def matches(self, thing):
        for matcher in matchers:
            if matcher.matches(thing):
                return True
        return False
    def __str__(self):
        return ', '.join(str(matcher) for matcher in matchers)

# Reverses another matcher
def InverseMatcher:
    def __init__(self, matcher):
        self.matcher = matcher
    def matches(self, thing):
        return not self.matcher.matches(thing)
    def __str__(self):
        return color('1;32', '^') + str(self.matcher)

# Always matches or does not match
def ConstMatcher:
    def __init__(self, val):
        self.val = val
    def matches(self, thing):
        return self.val
    def __str__(self):
        if self.val:
            return color('32', 'any')
        else:
            return color('31', 'none')
ConstMatcher.always = ConstMatcher(True)
ConstMatcher.never = ConstMatcher(False)

# Matches a method if an argument is a specific object
class MessageWithArgMatcher:
    def __init__(self, message_name_matcher, object_matcher):
        self.message_name_matcher = message_name_matcher
        self.object_matcher = object_matcher
    def matches(self, message):
        if not self.message_name_matcher.matches(message.name):
            return False
        for obj in message.used_objects():
            if self.object_matcher.matches(obj):
                return True
        return False
    def __str__(self):
        return '[' + str(self.message_name_matcher) + '] {' + str(self.object_matcher) + '}'

# Matches a method called on a specific object
class MessageOnObjMatcher:
    def __init__(self, object_matcher, message_name_matcher):
        self.object_matcher = object_matcher
        self.message_name_matcher = message_name_matcher
    def matches(self, message):
        assert message.obj is not None, 'Message objects must be resolved before matching'
        if not self.message_name_matcher.matches(message.name):
            return False
        if not self.object_matcher.matches(message.obj):
            return False
        return True
    def __str__(self):
        return '{' + str(self.object_matcher) + '} [' + str(self.message_name_matcher) + ']'

# returns (is_inversed, ['comma', 'seporated', 'stripped', 'strings'])
def _parse_sequence(raw):
    raw = raw.strip()
    is_inversed = False
    if raw.startswith('^'):
        is_inversed = True
        raw = raw[1:]
    elems = []
    for elem in raw.split(','):
        elem = elem.strip()
        if elem.startswith('^'):
            warning('\'^\' can only be at the start of a sequence, not before \'' + i[1:] + '\'')
            elem = elem[1:]
        elems.append(elem)
    return (is_inversed, elems)

def _parse_message_list(raw):
    if not raw:
        return ConstMatcher.always
    is_inversed, sequence = _parse_sequence(raw)
    elems = []
    for elem in sequence:
        elem = elem.strip()
        if elem:
            if re.findall('^[\w\*]+$', elem):
                elems.append(StrMatcher(elem))
            else:
                warning('Failed to parse message matcher \'' + elem + '\'')
    if len(elems) == 0:
        return ConstMatcher.always
    else:
        return make_matcher(elems, is_inversed)

def _parse_obj_matcher(raw):
    id_matches = re.findall('(^|[^\w\.-])(\d+)(\.(\d+))?', raw)
    obj_id = None
    obj_generation = None
    if id_matches:
        if len(id_matches) > 1:
            raise RuntimeError(
                'Found multiple object IDs (' +
                ', '.join(i[1] + ('.' + i[3] if i[3] else '') for i in id_matches) +
                ')')
        obj_id = int(id_matches[0][1])
        if id_matches[0][3]:
            obj_generation = int(id_matches[0][3])
    obj_name_matches = re.findall('([a-zA-Z\*][\w\*-]*)', raw)
    type_pattern = None
    if obj_name_matches:
        if len(obj_name_matches) > 1:
            raise RuntimeError(
                'Found multiple object type names (' +
                ', '.join(i for i in obj_name_matches) +
                ')')
        type_pattern = obj_name_matches[0]
    if not type_pattern and not obj_id:
        raise RuntimeError('Failed to parse object matcher \'' + raw + '\'')
    return ObjectMatcher(type_pattern, obj_id, obj_generation)

def _parse_obj_list(raw):
    raw = raw.strip()
    if not raw:
        return ConstMatcher.always
    if raw.startswith('{') and raw.endswith('}'):
        return _parse_obj_list(raw[1:-1]
    is_inversed, sequence = _parse_sequence(raw)
    elems = []
    for elem in sequence:
        elem = elem.strip()
        if elem:
            try:
                elems.append(_parse_obj_matcher(elem))
            except RuntimeError as e:
                warning(e)
    if len(elems) == 0:
        return ConstMatcher.always
    else:
        return make_matcher(elems, is_inversed)

def _parse_single_matcher(raw):
    assert not raw.startswith('^')
    if raw.startswith('{') and raw.endswith('}'):
        return parse_matcher(raw[1:-1])
    else:
        not_bracs_regex = '([^\[\]]*)'
        message_list_regex = '(\[' + not_bracs_regex + '\])?'
        groups = re.findall('^' + message_list_regex + not_bracs_regex + message_list_regex + '$', raw)
        if groups:
            message_list_a = _parse_message_list(groups[1])
            object_list = _parse_obj_list(groups[2])
            message_list_b = _parse_message_list(groups[4])
            # Check for special case where there is only one message list and no object matchers
            if message_list_a and not object_list and not message_list_b:
                return MessageOnObjMatcher(
                    ConstMatcher.always,
                    _parse_message_list(message_list_a))
            matchers = []
            if message_list_a:
                matchers.append(MessageWithArgMatcher(
                    _parse_message_list(message_list_a),
                    _parse_obj_list(object_list)))
            if message_list_b:
                matchers.append(MessageOnObjMatcher(
                    _parse_obj_list(object_list),
                    _parse_message_list(message_list_b)))
            if len(matchers) == 0:
                matchers.append(MessageOnObjMatcher(
                    _parse_obj_list(object_list),
                    ConstMatcher.always))
            make_matcher(matchers, False)
        else:
            warning('\'' + raw + '\' has invalid syntax')
            return ConstMatcher.never

def parse_matcher(raw):
    is_inversed, sequence = _parse_sequence(raw)
    matchers = (_parse_single_matcher(i) for i in sequence)
    if len(matchers) == 0:
        return ConstMatcher.never
    else:
        return make_matcher(matchers, is_inversed)

if __name__ == '__main__':
    print('File meant to be imported, not run')
    exit(1)
