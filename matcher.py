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
        matcher = ListMatcher(matcher)
    if inversed:
        matcher = InverseMatcher(matcher)
    return matcher

# Matches a Wayland object
class ObjectMatcher:
    def __init__(self, type_matcher, obj_id, obj_generation):
        if obj_id:
            assert isinstance(obj_id, int)
        if obj_generation:
            assert isinstance(obj_generation, int)
        self.type = type_matcher
        self.id = obj_id
        self.generation = obj_generation
    def matches(self, obj):
        if self.id and self.id != obj.id:
            return False
        elif self.generation and self.generation != obj.generation:
            return False
        elif not self.type.matches(obj.type):
            return False
        else:
            return True
    def simplify(self):
        self.type = self.type.simplify()
        if self.type == never:
            return never
        if not self.id and not self.generation:
            if isinstance(self.type, ConstMatcher):
                return self.type
        return self
    def __str__(self):
        out = ''
        if self.type != always:
            out += str(self.type)
            if self.id:
                out += '@'
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
    def simplify(self):
        self.pattern = re.sub('\*+', '*', self.pattern)
        if self.pattern == '*':
            return always
        return self
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
    def simplify(self):
        for i in range(len(self.matchers)):
            self.matchers[i] = self.matchers[i].simplify()
            if self.matchers[i] == always:
                return always
        if len(self.matchers) == 0:
            return always
        elif len(self.matchers) == 1:
            return self.matchers[0]
        else:
            return self
    def __str__(self):
        return ', '.join(str(matcher) for matcher in self.matchers)

# Reverses another matcher
class InverseMatcher:
    def __init__(self, matcher):
        self.matcher = matcher
    def matches(self, thing):
        return not self.matcher.matches(thing)
    def simplify(self):
        self.matcher = self.matcher.simplify()
        if self.matcher == always:
            return never
        elif self.matcher == never:
            return always
        elif isinstance(self.matcher, InverseMatcher):
            return matcher.matcher
        else:
            return self
    def __str__(self):
        return color('1;31', '(^ ') + str(self.matcher) + color('1;31', ')')

# Always matches or does not match
class ConstMatcher:
    def __init__(self, val):
        self.val = val
    def matches(self, thing):
        return self.val
    def simplify(self):
        if self.val and self != always:
            return always
        elif not self.val and self != never:
            return never
        else:
            return self
    def __str__(self):
        if self.val:
            return color('1;32', '*')
        else:
            return color('1;31', '(^)')

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
    def simplify(self):
        self.message_name_matcher = self.message_name_matcher.simplify()
        self.object_matcher = self.object_matcher.simplify()
        if self.message_name_matcher == never:
            return never
        if self.object_matcher == never:
            return never
        if self.message_name_matcher == always and self.object_matcher == always:
            return always
        return self
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
    def simplify(self):
        self.message_name_matcher = self.message_name_matcher.simplify()
        self.object_matcher = self.object_matcher.simplify()
        if self.message_name_matcher == never:
            return never
        if self.object_matcher == never:
            return never
        if self.message_name_matcher == always and self.object_matcher == always:
            return always
        return self
    def __str__(self):
        return '<' + str(self.object_matcher) + '> [' + str(self.message_name_matcher) + ']'

always = ConstMatcher(True)
never = ConstMatcher(False)
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
    if raw.startswith('^'):
        inversed, seq = _parse_sequence(raw[1:])
        return (not inversed, seq)
    elems = []
    for elem in _parse_comma_list(raw):
        elem = elem.strip()
        if elem.startswith('^'):
            warning('\'^\' can only be at the start of a sequence, not before \'' + elem[1:] + '\'')
            elem = elem[1:]
        elems.append(elem)
    return (False, elems)

def _parse_message_list(raw):
    assert raw.startswith('[') and raw.endswith(']')
    raw = raw[1:-1]
    if not raw:
        return always
    is_inversed, sequence = _parse_sequence(raw)
    elems = []
    for elem in sequence:
        elem = elem.strip()
        if elem:
            if re.findall('^[\*]+$', elem):
                elems.append(always)
            elif re.findall('^[\w\*]+$', elem):
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
    if type_pattern:
        type_matcher = StrMatcher(type_pattern)
    else:
        type_matcher = always
    return ObjectMatcher(type_matcher, obj_id, obj_generation)

def _parse_obj_list(raw):
    raw = raw.strip()
    if not raw:
        return always
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
        return parse(raw[1:-1])
    else:
        not_bracs_regex = '([^\[\]]*)'
        message_list_regex = '(\[' + not_bracs_regex + '\])?'
        groups = re.findall('^' + message_list_regex + not_bracs_regex + message_list_regex + '$', raw)
        if groups:
            message_list_a = groups[0][0]
            object_list = groups[0][2]
            message_list_b = groups[0][3]
            # Check for special case where there is only one message list and no object matchers
            if message_list_a and not object_list and not message_list_b:
                return MessageOnObjMatcher(
                    always,
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
                    always))
            return make_matcher(matchers, False)
        else:
            warning('\'' + raw + '\' has invalid syntax')
            return never

# Either returns a valid matcher or throws a RuntimeError with a description of why it could not be parsed
# Other behavior (such as throwing an AssertionError) is possible, but should be considered a bug in this file
def parse(raw):
    raw = no_color(raw)
    is_inversed, sequence = _parse_sequence(raw)
    matchers = [_parse_single_matcher(i) for i in sequence]
    return make_matcher(matchers, is_inversed)

# Order matters
def join(new, old):
    if isinstance(old, ConstMatcher):
        return new
    elif isinstance(new, InverseMatcher):
        # When you don't feel like writing an 'AndMatcher', and know too much about boolean logic
        return InverseMatcher(join(InverseMatcher(new), InverseMatcher(old)))
    else:
        if isinstance(old, ListMatcher):
            old.matchers.append(new)
            return old
        else:
            return ListMatcher([old, new])

if __name__ == '__main__':
    print('File meant to be imported, not run')
    exit(1)
