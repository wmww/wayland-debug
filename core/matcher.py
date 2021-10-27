import re

from core.util import *
import argparse # only used for line wrapping in the help

def print_help():
#                                                                          |
    print('''
Matchers are used throughout the program to show and hide messages. A matcher
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
    print(color('1;37', '  \'[delete_id]wl_surface[^commit], *[destroy], @3.2\''))

# Matches a string (uses wildcards)
class StrMatcher:
    def __init__(self, pattern):
        assert isinstance(pattern, str)
        self.pattern = pattern
    def matches(self, name):
        assert isinstance(name, str)
        return str_matches(self.pattern, name)
    def simplify(self):
        self.pattern = re.sub(r'\*+', '*', self.pattern)
        if self.pattern == '*':
            return always
        return self
    def __str__(self):
        return color('1;34', self.pattern)

# Matches any in a list of matchers
class ListMatcher:
    def __init__(self, matchers, match_any, joiner_str):
        self.matchers = matchers
        self.match_any = bool(match_any)
        self.joiner_str = joiner_str
    def matches(self, thing):
        for matcher in self.matchers:
            if bool(matcher.matches(thing)) == self.match_any:
                return self.match_any 
        return not self.match_any
    def simplify(self):
        matchers = []
        for i in self.matchers:
            matcher = i.simplify()
            if isinstance(matcher, ListMatcher) and self.match_any == matcher.match_any:
                for j in matcher.matchers:
                    matchers.append(j)
                matcher = None
            if isinstance(matcher, ConstMatcher):
                if matcher.val == self.match_any:
                    return matcher
                else:
                    matcher = None
            if matcher:
                matchers.append(matcher)
        self.matchers = matchers
        if len(self.matchers) == 0:
            return ConstMatcher(not self.match_any).simplify()
        elif len(self.matchers) == 1:
            return self.matchers[0]
        else:
            return self
    def __str__(self):
        return '(' + self.joiner_str.join(str(matcher) for matcher in self.matchers) + ')'

class AndMatcher(ListMatcher):
    def __init__(self, matchers):
        super().__init__(matchers, False, ' & ')
    def __str__(self):
        return '(' + ' & '.join([str(i) for i in self.matchers]) + ')'
        """
        # Special case the parts of an object matcher
        msg_obj = ''
        msg_obj_arg = ''
        msg_name = ''
        obj_type = ''
        obj_id = ''
        obj_gen = ''
        matchers = []
        for matcher in self.matchers:
            if not msg_obj and isinstance(matcher, ObjectOfMessageMatcher):
                msg_obj = str(matcher.matcher)
            elif not msg_name and isinstance(matcher, MessageNameMatcher):
                msg_name = str(matcher.matcher)
            elif not msg_obj_arg and isinstance(matcher, ObjectMessageArgMatcher):
                msg_obj_arg = str(matcher.matcher)
            elif not obj_type and isinstance(matcher, ObjectTypeMatcher):
                obj_type = str(matcher)
            elif not obj_id and isinstance(matcher, ObjectIdMatcher):
                obj_id = str(matcher)
            elif not obj_gen and isinstance(matcher, ObjectGenMatcher):
                obj_gen = str(matcher)
            else:
                matchers.append(str(matcher))
        if obj_type or obj_id or obj_gen:
            matchers = [obj_type + obj_id + obj_gen] + matchers
        if msg_obj or (msg_name and not msg_obj_arg):
            matchers = [msg_obj + '[' + msg_name + ']'] + matchers
        if msg_obj_arg:
            matchers = ['[' + msg_name + ']' + msg_obj_arg] + matchers
        return '(' + ' & '.join(matchers) + ')'
        """

class OrMatcher(ListMatcher):
    def __init__(self, matchers):
        super().__init__(matchers, True, ', ')

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

MessageMatcher = ConstMatcher

class TransformMatcher:
    def __init__(self, matcher):
        self.matcher = matcher
    def matches(self, thing):
        return self.matcher.matches(self.transform(thing))
    def simplify(self):
        self.matcher = self.matcher.simplify()
        if isinstance(self.matcher, ConstMatcher):
            return self.matcher
        return self

class ObjectOfMessageMatcher(TransformMatcher):
    def transform(self, message):
        assert message.obj is not None, 'Message objects must be resolved before matching'
        return message.obj
    def __str__(self):
        return str(self.matcher) + ' []'

class MessageNameMatcher(TransformMatcher):
    def transform(self, message):
        return message.name
    def __str__(self):
        return '[' + str(self.matcher) + ']'

class ObjectTypeMatcher(TransformMatcher):
    def transform(self, obj):
        return obj.type_str()
    def __str__(self):
        return str(self.matcher)

class ObjectIdMatcher(TransformMatcher):
    def transform(self, obj):
        return obj.id
    def __str__(self):
        return '@' + str(self.matcher)

class ObjectGenMatcher(TransformMatcher):
    def transform(self, obj):
        return obj.generation
    def __str__(self):
        return '.' + str(self.matcher)

class EqMatcher:
    def __init__(self, value):
        self.value = value
    def matches(self, thing):
        return self.value == thing
    def simplify(self):
        return self
    def __str__(self):
        return color('1;37', str(self.value))

class ObjectMessageArgMatcher:
    def __init__(self, matcher):
        self.matcher = matcher
    def matches(self, message):
        for obj in message.used_objects():
            if self.matcher.matches(obj):
                return True
        return False
    def simplify(self):
        self.matcher = self.matcher.simplify()
        if isinstance(self.matcher, ConstMatcher):
            return self.matcher
        return self
    def __str__(self):
        return '[] ' + str(self.matcher)

always = ConstMatcher(True)
never = ConstMatcher(False)
_op_braces = {'(': ')', '[': ']', '<': '>', "'": "'", '"': '"'}
_cl_braces = {a: b for b, a in _op_braces.items()}
_ignore = {' ': True, '\t': True, '\n': True}

def _split_raw_list(delimiter, raw, list_start, end):
    chunks = []
    start = list_start
    i = start
    while True:
        if i == end or raw[i] == delimiter:
            if delimiter or i > start:
                chunks.append((start, i))
            start = i + 1
            if i == end:
                return chunks
        elif raw[i] in _cl_braces:
            raise RuntimeError('"' + raw[:i] + color('1;31', raw[i]) + raw[i+1:] + '" has extra \'' + raw[i] + '\'')
        elif raw[i] in _op_braces:
            if not delimiter and i > start:
                chunks.append((start, i))
                start = i
            j = i
            op = raw[i]
            cl = _op_braces[op]
            count = 1
            while count > 0:
                j += 1
                if j >= end:
                    raise RuntimeError('"' + raw[:i] + color('1;31', raw[i]) + raw[i+1:] + '" has unclosed \'' + raw[i] + '\'')
                elif raw[j] == '\\' and op == cl and j + 1 < end and raw[j+1] == cl:
                    j += 1
                elif raw[j] == cl:
                    count -= 1
                elif raw[j] == op:
                    count += 1
            i = j
            if not delimiter and i + 1 > start:
                chunks.append((start, i + 1))
                start = i + 1
        i += 1
    assert False

def _parse_expr(raw, start, end, allow_inverse, sub_parser_func):
    while start < end and raw[start] in _ignore:
        start += 1
    while end > start and raw[end - 1] in _ignore:
        end -= 1
    if start >= end:
        raise RuntimeError('"' + raw[:start] + color('1;31', '__') + raw[end:] + '" has empty expression')
    if raw[start] == '^':
        if allow_inverse:
            if start + 1 < end:
                return InverseMatcher(_parse_expr(raw, start + 1, end, True, sub_parser_func))
            else:
                return never
        else:
            raise RuntimeError('"' + raw[:start] + color('1;31', '^') + raw[start+1:] + '" has incorrectly placed \'^\' (you must use parentheses)')
    elems = _split_raw_list(',', raw, start, end)
    if len(elems) > 1:
        matchers = [_parse_expr(raw, i[0], i[1], False, sub_parser_func) for i in elems]
        return OrMatcher(matchers)
    elems = _split_raw_list('&', raw, start, end)
    if len(elems) > 1:
        matchers = [_parse_expr(raw, i[0], i[1], False, sub_parser_func) for i in elems]
        return AndMatcher(matchers)
    if raw[start] == '(' and raw[end - 1] == ')':
        return _parse_expr(raw, start + 1, end - 1, True, sub_parser_func)
    return sub_parser_func(raw, start, end)

def _parse_str(raw, start, end):
    text = raw[start:end]
    if not re.findall(r'^[^\(\)\[\]~,@&\.]*$', text):
        raise RuntimeError('"' + text + '" is not a valid string')
    return StrMatcher(text)

def _parse_int(raw, start, end):
    s = raw[start:end]
    if not re.findall(r'^[\-]?\d+$', s):
        raise RuntimeError('In "' + raw[:start] + color('1;31', raw[start:end]) + raw[end:] + '", "' + raw[start:end] + raw[end:] + '" should have been an int')
    return EqMatcher(int(raw[start:end]))

def _parse_message_list(raw, start, end):
    assert raw[start] == '[' and raw[end - 1] == ']'
    start += 1
    end -= 1
    if start >= end:
        return always
    else:
        m = _parse_expr(raw, start, end, True, _parse_str)
        return MessageNameMatcher(m)

def _parse_object_id_matcher(raw, start, end):
    elems = _split_raw_list('.', raw, start, end)
    assert len(elems) > 0
    if len(elems) > 2:
        raise RuntimeError('"' + raw[:start] + color('1;31', raw[start:end]) + raw[end:] + '" has too many \'.\'s')
    id_matcher = always
    if elems[0][0] < elems[0][1]:
        id_matcher = _parse_expr(raw, elems[0][0], elems[0][1], False, _parse_int)
    gen_matcher = always
    if len(elems) > 1:
        gen_matcher = _parse_expr(raw, elems[1][0], elems[1][1], False, _parse_int)
    return AndMatcher([
        ObjectIdMatcher(id_matcher),
        ObjectGenMatcher(gen_matcher)])

_digit_chars = {i: True for i in [str(j) for j in range(10)] + ['.']}

def _parse_object_matcher(raw, start, end):
    elems = _split_raw_list('@', raw, start, end)
    assert len(elems) > 0
    if len(elems) > 2:
        raise RuntimeError('"' + raw[:start] + color('1;31', raw[start:end]) + raw[end:] + '" has too many \'@\'s')
    name_matcher = always
    if elems[0][0] < elems[0][1]:
        if not raw[elems[0][0]] in _digit_chars:
            name_matcher = _parse_expr(raw, elems[0][0], elems[0][1], False, _parse_str)
            elems = elems[1:]
    else:
        elems = elems[1:]
    id_matcher = always
    if len(elems) > 0:
        id_matcher = _parse_expr(raw, elems[0][0], elems[0][1], True, _parse_object_id_matcher)
        elems = elems[1:]
    return AndMatcher([
        ObjectTypeMatcher(name_matcher),
        id_matcher])

def _parse_message_matcher(raw, start, end):
    elems = _split_raw_list(None, raw, start, end)
    a = never
    b = never
    obj = None
    # [a] obj [b]
    if len(elems) > 0 and raw[elems[-1][0]] == '[':
        b = _parse_message_list(raw, elems[-1][0], elems[-1][1])
        elems = elems[:-1]
        obj = always
    if len(elems) > 0 and raw[elems[0][0]] == '[':
        a = _parse_message_list(raw, elems[0][0], elems[0][1])
        elems = elems[1:]
        obj = always
    if not obj:
        a = always
        b = always
    if len(elems) > 0:
        obj = _parse_expr(raw, elems[0][0], elems[-1][1], False, _parse_object_matcher)
    if not obj:
        raise RuntimeError('"' + raw[:start] + color('1;31', raw[start:end]) + raw[end:] + '" has invalid syntax')
    return OrMatcher([
        AndMatcher([
            a,
            ObjectMessageArgMatcher(obj)]),
        AndMatcher([
            ObjectOfMessageMatcher(obj),
            b])])

# Either returns a valid matcher or throws a RuntimeError with a description of why it could not be parsed
# Other behavior (such as throwing an AssertionError) is possible, but should be considered a bug in this file
def parse(raw):
    raw = no_color(raw)
    if not raw.strip():
        return always
    return _parse_expr(raw, 0, len(raw), True, _parse_message_matcher)

# Order matters
def join(new, old):
    if isinstance(old, ConstMatcher):
        return new
    elif isinstance(new, InverseMatcher) or new == never:
        return AndMatcher([old, new])
    else:
        return OrMatcher([old, new])

if __name__ == '__main__':
    print('File meant to be imported, not run')
    exit(1)
