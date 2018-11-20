import re

from util import *
import argparse # only used for line wrapping in the help

def print_help():
#                                                                          |
    print('''
Matchers are used through out the program to show and hide messages. A matcher
consists of a comma seporated list of objects. An object is a type name,
and/or an object ID (in which case a generation can also be specified). An
@ goes inbetween the name and ID, and is optional if both are not specified.
A * can be used as a wildcard in type names.''')
    print()
    print('Examples of objects:')
    for i in [
            ('wl_surface  ', 'any wl_surface'),
            ('5           ', 'the object with ID 5'),
            ('4.12        ', 'the 12th object with ID 4'),
            ('wl_surface@6', 'the object with ID 7, which is asserted to be a wl_surface'),
            ('xdg_*@3.2   ', 'the 2nd object with ID 3, which is some sort of XDG type')]:
        print('  ' + color('1;37', i[0]) + ' - Matches ' + i[1])
#                                                                          |
    print('''
Matchers can optionally be accompanied by a brace enclosed, comma seporated
list of messages. Messages can have wildcards too. Messages before the
object require the object to be on argument, and messages after require the
message to be called on the object''')
    print()
    print('Examples of messages:')
    for i in [
            ('wl_surface[commit]  ', 'commit messages on wl_surfaces'),
            ('6.2[motion,button]  ', 'motion or button messages on the 2nd object with ID 6'),
            ('[delete_id]*_surface', 'delete_id messages on any sort of surface (this works\n' +
             '                         even though the messages themselves are called on the wl_display)')]:
        print('  ' + color('1;37', i[0]) + ' - Matches ' + i[1])
    print('''
If the matcher list (or a message list) starts with \'^\', it matches everything but what\'s
given. A complete example of a matcher could look something like:''')
    print(color('1;37', '  \'[delete_id]wl_surface[commit], *[destroy], @3.2\''))

def make_matcher(matcher, inversed):
    if isinstance(matcher, list):
        if len(matcher) == 0:
            matcher = ConstMatcher.always
        elif len(matcher) == 1:
            matcher = matcher[0]
        else:
            matcher = ListMatcher(matcher)
    if inversed:
        matcher = _inverse_matcher(matcher)
    return matcher

# Matches a Wayland object
class ObjectMatcher:
    def __init__(self, type_pattern, obj_id, obj_generation):
        if type_pattern:
            assert isinstance(type_pattern, str)
        if obj_id:
            assert isinstance(obj_id, int)
        if obj_generation:
            assert isinstance(obj_generation, int)
        self.type = type_pattern
        self.id = obj_id
        self.generation = obj_generation

    def matches(self, obj):
        if self.id and self.id != obj.id:
            return False
        elif self.generation and self.generation != obj.generation:
            return False
        elif self.type and not str_matches(self.type, obj.type):
            return False
        else:
            return True

    def __str__(self):
        out = ''
        if self.type:
            out += self.type
            if self.id:
                out += ' @ '
        if self.id:
            out += str(self.id)
            if self.generation:
                out += '.' + str(self.generation)
        return color('1;35', out)

# Matches a string (uses wildcards)
class StrMatcher:
    def __init__(self, pattern):
        assert isinstance(pattern, str)
        self.pattern = pattern
    def matches(self, name):
        assert isinstance(name, str)
        return str_matches(self.pattern, name)
    def __str__(self):
        return color('1;34', self.pattern)

# Matches any in a list of matchers
class ListMatcher:
    def __init__(self, matchers):
        self.matchers = matchers
    def matches(self, thing):
        for matcher in self.matchers:
            if matcher.matches(thing):
                return True
        return False
    def __str__(self):
        return ', '.join(str(matcher) for matcher in self.matchers)

# Reverses another matcher
class InverseMatcher:
    def __init__(self, matcher):
        self.matcher = matcher
    def matches(self, thing):
        return not self.matcher.matches(thing)
    def __str__(self):
        return color('1;31', '(^ ') + str(self.matcher) + color('1;31', ')')

# Always matches or does not match
class ConstMatcher:
    def __init__(self, val):
        self.val = val
    def matches(self, thing):
        return self.val
    def __str__(self):
        if self.val:
            return color('32', '*')
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
        return '[' + str(self.message_name_matcher) + '] <' + str(self.object_matcher) + '>'

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
        return '<' + str(self.object_matcher) + '> [' + str(self.message_name_matcher) + ']'

def _inverse_matcher(matcher):
    if matcher == ConstMatcher.always:
        return ConstMatcher.never
    elif matcher == ConstMatcher.never:
        return ConstMatcher.always
    elif isinstance(matcher, InverseMatcher):
        while isinstance(matcher, InverseMatcher) and isinstance(matcher.matcher, InverseMatcher):
            matcher = matcher.matcher.matcher
        return matcher.matcher
    else:
        return InverseMatcher(matcher)

_op_braces = {'(': ')', '[': ']', '<': '>'}
_cl_braces = {a: b for b, a in _op_braces.items()}

def _parse_comma_list(raw):
    chunks = []
    start = 0
    i = 0
    while i <= len(raw):
        if i == len(raw) or raw[i] == ',':
            if i > start:
                chunks.append(raw[start:i])
            start = i + 1
        elif raw[i] in _cl_braces:
            raise RuntimeError('\'' + raw + '\' has mismatched braces')
        elif raw[i] in _op_braces:
            j = i
            op = raw[i]
            cl = _op_braces[op]
            count = 1
            while count > 0:
                j += 1
                if j >= len(raw):
                    raise RuntimeError('\'' + raw + '\' has mismatched braces')
                if raw[j] == op:
                    count += 1
                if raw[j] == cl:
                    count -= 1
            i = j
        i += 1
    return chunks

# returns (is_inversed, ['comma', 'seporated', 'stripped', 'strings'])
def _parse_sequence(raw):
    raw = raw.strip()
    if raw.startswith('(') and raw.endswith(')'):
        return _parse_sequence(raw[1:-1])
    is_inversed = False
    if raw.startswith('^'):
        is_inversed = True
        raw = raw[1:]
    elems = []
    for elem in _parse_comma_list(raw):
        elem = elem.strip()
        if elem.startswith('^'):
            warning('\'^\' can only be at the start of a sequence, not before \'' + elem[1:] + '\'')
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
    if raw.startswith('<') and raw.endswith('>'):
        return _parse_obj_list(raw[1:-1])
    is_inversed, sequence = _parse_sequence(raw)
    elems = []
    for elem in sequence:
        elem = elem.strip()
        if elem:
            try:
                elems.append(_parse_obj_matcher(elem))
            except RuntimeError as e:
                warning(str(e))
    return make_matcher(elems, is_inversed)

def _parse_single_matcher(raw):
    assert not raw.startswith('^')
    if raw.startswith('(') and raw.endswith(')'):
        return parse_matcher(raw[1:-1])
    else:
        not_bracs_regex = '([^\[\]]*)'
        message_list_regex = '(\[' + not_bracs_regex + '\])?'
        groups = re.findall('^' + message_list_regex + not_bracs_regex + message_list_regex + '$', raw)
        if groups:
            message_list_a = groups[0][1]
            object_list = groups[0][2]
            message_list_b = groups[0][4]
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
            return make_matcher(matchers, False)
        else:
            warning('\'' + raw + '\' has invalid syntax')
            return ConstMatcher.never

# Either returns a valid matcher or throws a RuntimeError with a description of why it could not be parsed
# Other behavior (such as throwing an AssertionError) is possible, but should be considered a bug in this file
def parse(raw):
    is_inversed, sequence = _parse_sequence(raw)
    matchers = [_parse_single_matcher(i) for i in sequence]
    return make_matcher(matchers, is_inversed)

# Order matters
def join(new, old):
    if isinstance(new, InverseMatcher):
        # When you don't feel like writing an 'AndMatcher', and know too much about boolean logic
        return _inverse_matcher(join(_inverse_matcher(new), _inverse_matcher(old)))
    else:
        if isinstance(old, ListMatcher):
            old.matchers.append(new)
            return old
        else:
            return ListMatcher([old, new])

if __name__ == '__main__':
    print('File meant to be imported, not run')
    exit(1)
