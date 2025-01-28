import re
from typing import List, Set, Optional, Tuple, Generic, TypeVar, Any, Callable, cast

from core.util import *
from core.letter_id_generator import letter_id_to_number
from core import wl
from interfaces import Connection

T = TypeVar('T')
U = TypeVar('U')

def help_text() -> str:
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'matchers.md')
    text = open(path, 'r').read()
    text = re.sub(r'# Matchers\n\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'\| Matcher\s*\| Description \|\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'\| ---\s*\| --- \|\n', '', text, flags=re.MULTILINE)
    matches = re.findall(r'^\|\s*`(.*)`\s*\|(.*)\|$', text, flags=re.MULTILINE)
    parts = re.split(r'^\|.*\|$', text, flags=re.MULTILINE)
    assert len(matches) + 1 == len(parts)
    result = parts[0]
    for i, match in enumerate(matches):
        result += color(object_type_color, match[0])
        result += ' ' * (32 - len(match[0]))
        result += color(object_id_color, match[1])
        result += parts[i + 1]
    return result

class Matcher(Generic[T]):
    def matches(self, message: T) -> bool:
        raise NotImplementedError()

    def simplify(self) -> 'Matcher[T]':
        return self

    def always(self) -> Optional[bool]:
        return None

    def __str__(self) -> str:
        raise NotImplementedError()

    def __repr__(self) -> str:
        raise NotImplementedError()

MessageMatcher = Matcher[wl.Message]

class AlwaysMatcher(Matcher[Any]):
    def __init__(self, result: bool) -> None:
        self.result = result

    def matches(self, message: T) -> bool:
        return self.result

    def always(self) -> Optional[bool]:
        return self.result

    def __str__(self) -> str:
        if self.result:
            return color(good_color, '*')
        else:
            return color(bad_color, '!')

    def __repr__(self) -> str:
        if self.result:
            return '<always>'
        else:
            return '<never>'

class WildcardMatcher(Matcher[str]):
    def __init__(self, pattern: str) -> None:
        self.pattern = pattern
        re_pattern = r'^' + re.escape(pattern).replace(r'\*', '.*') + r'$'
        self.regex = re.compile(re_pattern)

    def matches(self, text: str) -> bool:
        return len(self.regex.findall(text)) > 0

    def __str__(self) -> str:
        return self.pattern

    def __repr__(self) -> str:
        return 'Wildcard(' + self.pattern + ')'

class EqMatcher(Matcher[T]):
    def __init__(self, expected: T, text: Optional[str] = None) -> None:
        self.expected = expected
        if text is None:
            self.text = str(self.expected)
        else:
            self.text = text

    def matches(self, value: T) -> bool:
        return self.expected == value

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return 'Eq(' + self.text + ', ' + repr(self.expected) + ')'

class WrapMatcher(Generic[T, U], Matcher[T]):
    def __init__(self, wrapped: Matcher[U]) -> None:
        self.wrapped = wrapped

    def simplify(self) -> Matcher[T]:
        self.wrapped = self.wrapped.simplify()
        always = self.wrapped.always()
        if always is not None:
            return AlwaysMatcher(always)
        else:
            return self

    def __str__(self) -> str:
        return str(self.wrapped)

    def __repr__(self) -> str:
        return type(self).__name__ + '(' + repr(self.wrapped) + ')'

class PairMatcher(Matcher[Tuple[T, U]]):
    def __init__(self, a: Matcher[T], delimiter: str, b: Matcher[U]) -> None:
        self.a = a
        self.b = b
        self.delimiter = delimiter # Used only for display

    def matches(self, pair: Tuple[T, U]) -> bool:
        return self.a.matches(pair[0]) and self.b.matches(pair[1])

    def simplify(self) -> Matcher[Tuple[T, U]]:
        self.a = self.a.simplify()
        self.b = self.b.simplify()
        a_always = self.a.always()
        b_always = self.b.always()
        if a_always is not None and a_always is b_always:
            return AlwaysMatcher(a_always)
        else:
            return self

    def __str__(self) -> str:
        return str(self.a) + self.delimiter + str(self.b)

    def __repr__(self) -> str:
        return 'Pair(' + repr(self.a) + ', ' + self.delimiter.strip() + ', ' + repr(self.b) + ')'

class MatcherList(Generic[T], Matcher[T]):
    def __init__(self, positive: List[Matcher], negative: List[Matcher]) -> None:
        self.positive = positive
        self.negative = negative

    def matches(self, message: T) -> bool:
        result = False
        for matcher in self.positive:
            if matcher.matches(message):
                result = True
                break
        if result:
            for matcher in self.negative:
                if matcher.matches(message):
                    result = False
                    break
        return result

    def simplify(self) -> Matcher[T]:
        if len(self.positive) == 0:
            return AlwaysMatcher(False)
        self.positive = [pattern.simplify() for pattern in self.positive]
        self.negative = [pattern.simplify() for pattern in self.negative]
        for pattern in self.negative:
            if pattern.always() is True:
                return AlwaysMatcher(False)
        for pattern in self.positive:
            if pattern.always() is True:
                self.positive = [pattern]
        # Filter out AlwaysMatcher(False) from both
        self.positive = [pattern for pattern in self.positive if not pattern.always() is False]
        self.negative = [pattern for pattern in self.negative if not pattern.always() is False]
        if len(self.positive) == 0:
            return AlwaysMatcher(False)
        elif len(self.positive) == 1 and len(self.negative) == 0:
            return self.positive[0]
        else:
            return self

    def __str__(self) -> str:
        if len(self.negative) == 0:
            return '[' + ', '.join(str(i) for i in self.positive) + ']'
        elif len(self.positive) == 1 and self.positive[0].always() is True:
            return '[' + color(bad_color, ' ! ') + ', '.join(str(i) for i in self.negative) + ']'
        else:
            return '[' + (
                ', '.join(str(i) for i in self.positive) +
                color(bad_color, ' ! ') +
                ', '.join(str(i) for i in self.negative)
            ) + ']'

    def __repr__(self) -> str:
        return 'List(positive=' + repr(self.positive) + ', negative=' + repr(self.negative) + ')'

class ArgsMatcherList(Matcher[Tuple[wl.Arg.Base, ...]]):
    def __init__(self, positive: List[Matcher[wl.Arg.Base]], negative: List[Matcher[wl.Arg.Base]]) -> None:
        self.positive = positive
        self.negative = negative

    def matches(self, message: Tuple[wl.Arg.Base, ...]) -> bool:
        result = True
        for matcher in self.positive:
            found_match = False
            for arg in message:
                if matcher.matches(arg):
                    found_match = True
                    break
            if not found_match:
                result = False
                break
        if result:
            for matcher in self.negative:
                for arg in message:
                    if matcher.matches(arg):
                        result = False
                        break
        return result

    def simplify(self) -> Matcher[Tuple[wl.Arg.Base, ...]]:
        self.positive = [pattern.simplify() for pattern in self.positive]
        self.negative = [pattern.simplify() for pattern in self.negative]
        for pattern in self.negative:
            if pattern.always() is True:
                return AlwaysMatcher(False)
        positive_all_always_true = True
        for pattern in self.positive:
            if pattern.always() is False:
                return AlwaysMatcher(False)
            if pattern.always() is not True:
                positive_all_always_true = False
        self.negative = [pattern for pattern in self.negative if not pattern.always() is False]
        if positive_all_always_true and len(self.negative) == 0:
            return AlwaysMatcher(True)
        return self

    def __str__(self) -> str:
        if len(self.negative) == 0:
            return ', '.join(str(i) for i in self.positive)
        elif len(self.positive) == 1 and self.positive[0].always() is True:
            return color(bad_color, ' ! ') + ', '.join(str(i) for i in self.negative)
        else:
            return (
                ', '.join(str(i) for i in self.positive) +
                color(bad_color, ' ! ') +
                ', '.join(str(i) for i in self.negative)
            )

    def __repr__(self) -> str:
        return 'ArgsList(positive=' + repr(self.positive) + ', negative=' + repr(self.negative) + ')'

class IntArgValueMatcher(WrapMatcher[wl.Arg.Base, int]):
    def matches(self, arg: wl.Arg.Base) -> bool:
        if isinstance(arg, wl.Arg.Int) or isinstance(arg, wl.Arg.Float) or isinstance(arg, wl.Arg.Fd):
            return arg.value == int(arg.value) and self.wrapped.matches(int(arg.value))
        elif isinstance(arg, wl.Arg.Object):
            return self.wrapped.matches(arg.obj.id)
        else:
            return False

class FloatArgValueMatcher(WrapMatcher[wl.Arg.Base, float]):
    def matches(self, arg: wl.Arg.Base) -> bool:
        if isinstance(arg, wl.Arg.Float):
            return self.wrapped.matches(arg.value)
        else:
            return False

class StringArgValueMatcher(WrapMatcher[wl.Arg.Base, str]):
    def matches(self, arg: wl.Arg.Base) -> bool:
        return isinstance(arg, wl.Arg.String) and self.wrapped.matches(arg.value)

class ObjectArgValueMatcher(WrapMatcher[wl.Arg.Base, wl.ObjectBase]):
    def matches(self, arg: wl.Arg.Base) -> bool:
        if isinstance(arg, wl.Arg.Object):
            return self.wrapped.matches(arg.obj)
        elif isinstance(arg, wl.Arg.Null):
            mock = wl.object.MockObject(id=0, type=arg.type)
            return self.wrapped.matches(mock)
        else:
            return False

class ArgMatcher(WrapMatcher[wl.Arg.Base, Tuple[str, wl.Arg.Base]]):
    def __init__(self, name_matcher: Matcher[str], val_matcher: Matcher[wl.Arg.Base]):
        super().__init__(PairMatcher(name_matcher, '=', val_matcher))

    def matches(self, arg: wl.Arg.Base) -> bool:
        name = arg.name if arg.name is not None else ''
        return self.wrapped.matches((name, arg))

class ObjectIdMatcher(WrapMatcher[wl.ObjectBase, Tuple[int, int]]):
    def matches(self, obj: wl.ObjectBase) -> bool:
        generation = obj.generation if obj.generation is not None else 0
        return self.wrapped.matches((obj.id, generation))

class ObjectNameMatcher(WrapMatcher[wl.ObjectBase, str]):
    def matches(self, obj: wl.ObjectBase) -> bool:
        return obj.type is not None and self.wrapped.matches(obj.type)

class MessagePattern(Matcher[wl.Message]):
    def __init__(
        self,
        conn_matcher: Matcher[Optional[Connection]],
        obj_matcher: Matcher[wl.ObjectBase],
        name_matcher: Matcher[str],
        args_matcher: Matcher[Tuple[wl.Arg.Base, ...]]
    ) -> None:
        self.conn_matcher = conn_matcher
        self.obj_matcher = obj_matcher
        self.name_matcher = name_matcher
        self.args_matcher = args_matcher
        self.match_destroyed = self.name_matcher.matches('destroyed')

    def matches(self, message: wl.Message) -> bool:
        if not self.conn_matcher.matches(message.obj.connection):
            return False
        if (self.match_destroyed and
            message.destroyed_obj is not None and
            self.obj_matcher.matches(message.destroyed_obj)
        ):
            return True
        if not self.obj_matcher.matches(message.obj):
            return False
        if not self.name_matcher.matches(message.name):
            return False
        if not self.args_matcher.matches(message.args):
            return False
        return True

    def simplify(self) -> Matcher[wl.Message]:
        self.conn_matcher = self.conn_matcher.simplify()
        self.obj_matcher = self.obj_matcher.simplify()
        self.name_matcher = self.name_matcher.simplify()
        self.args_matcher = self.args_matcher.simplify()
        if (self.conn_matcher.always() is False or
            self.obj_matcher.always() is False or
            self.name_matcher.always() is False or
            self.args_matcher.always() is False
        ):
            return AlwaysMatcher(False)
        if (self.conn_matcher.always() is True and
            self.obj_matcher.always() is True and
            self.name_matcher.always() is True and
            self.args_matcher.always() is True
        ):
            return AlwaysMatcher(True)
        return self

    def __str__(self) -> str:
        result = ''
        if self.conn_matcher.always() is not True:
            result += str(self.conn_matcher)
        result += str(self.obj_matcher)
        result += '.' + str(self.name_matcher)
        result += '(' + str(self.args_matcher) + ')'
        return result

    def __repr__(self) -> str:
        return ('Message(' +
            repr(self.conn_matcher) + ', ' +
            repr(self.obj_matcher) + ', ' +
            repr(self.name_matcher) + ', ' +
            repr(self.args_matcher) + ')'
        )

class ConnectionMatcher(WrapMatcher[Optional[Connection], str]):
    def matches(self, conn: Optional[Connection]) -> bool:
        name = conn.name() if conn is not None else 'unknown'
        return self.wrapped.matches(name)

always: Matcher[Any] = AlwaysMatcher(True)
never: Matcher[Any] = AlwaysMatcher(False)

def str_matcher(pattern: str) -> Matcher[str]:
    if pattern == '*':
        return AlwaysMatcher(True)
    elif '*' in pattern:
        return WildcardMatcher(pattern)
    else:
        return EqMatcher(pattern)

identifier_re = re.compile(r'^[\*\-_A-Za-z0-9]*$')

def identifier_matcher(pattern: str) -> Matcher[str]:
    if not identifier_re.match(pattern):
        raise RuntimeError(pattern + ' is not a valid identifier')
    return str_matcher(pattern)

_brace_pairs = {
    '(' : ')',
    '[' : ']',
    '"' : '"',
}
def _find_closing_brace(text: str, start: int) -> int:
    opening = text[start]
    closing = _brace_pairs[opening]
    i = start
    level = 1
    for i in range(start + 1, len(text)):
        if text[i] == closing:
            level -= 1
        elif text[i] == opening:
            level += 1
        if level == 0:
            return i
    raise RuntimeError(
        text[:start] + color(bad_color, opening) + text[start + 1:] +
        ' contains unmatched "' + opening + '"'
    )

def _split_on(text: str, delimiter: str, allow_empty_list: bool = False) -> Tuple[str, ...]:
    if text.strip() == '' and allow_empty_list:
        return ()
    section_start = 0
    result = []
    i = 0
    while i <= len(text):
        c = text[i] if i < len(text) else ''
        if c == '' or c == delimiter:
            result.append(text[section_start:i].strip())
            section_start = i + 1
        if c in _brace_pairs:
            i = _find_closing_brace(text, i)
        i += 1
    return tuple(result)

def _split_pair(text: str, delimiter: str) -> Optional[Tuple[str, str]]:
    results = _split_on(text, delimiter)
    if len(results) == 2:
        return cast(Tuple[str, str], results)
    elif len(results) <= 1:
        return None
    else:
        raise RuntimeError(
            color(bad_color, delimiter).join(results) +
            ' contains too many "' + delimiter + '"s'
        )

def _split_peren_at_end(text: str) -> Optional[Tuple[str, str]]:
    pair = _split_pair(text, '(')
    if pair is not None:
        if not pair[1].endswith(')'):
            raise RuntimeError(text + ' has trailing characters after ")"')
        return (pair[0], pair[1][:-1])
    else:
        return pair

def _parse_matcher_list(text: str, sub_parser: Callable[[str], Matcher[T]]) -> Matcher[T]:
    bang_split = _split_pair(text, '!')
    if bang_split is not None:
        return MatcherList(
            [sub_parser(i) for i in _split_on(bang_split[0], ',')],
            [sub_parser(i) for i in _split_on(bang_split[1], ',')],
        )
    else:
        positive = [sub_parser(i) for i in _split_on(text, ',')]
        if len(positive) > 1:
            return MatcherList(positive, [])
        else:
            return positive[0]

def _parse_args_list(text: str) -> Matcher[Tuple[wl.Arg.Base, ...]]:
    if text == '':
        return AlwaysMatcher(True)
    bang_split = _split_pair(text, '!')
    if bang_split is None:
        positive_text = _split_on(text, ',', allow_empty_list=True)
        negative_text: Tuple[str, ...] = ()
    else:
        positive_text = _split_on(bang_split[0], ',', allow_empty_list=True)
        negative_text = _split_on(bang_split[1], ',', allow_empty_list=True)
    positive = [_parse_arg_matcher(i) for i in positive_text]
    negative = [_parse_arg_matcher(i) for i in negative_text]
    return ArgsMatcherList(positive, negative)

def _parse_arg_matcher(text: str) -> Matcher[wl.Arg.Base]:
    if text.startswith('[') and text.endswith(']'):
        text = text[1:-1]
        return _parse_matcher_list(text, _parse_arg_matcher)
    eq_split = _split_pair(text, '=')
    if eq_split is not None:
        name_matcher = _parse_text_matcher(eq_split[0])
        value_text = eq_split[1]
    else:
        name_matcher = AlwaysMatcher(True)
        value_text = text
    value_matcher = _parse_arg_value_matcher(value_text)
    return ArgMatcher(name_matcher, value_matcher)

def _parse_arg_value_matcher(text: str) -> Matcher[wl.Arg.Base]:
    if text.startswith('[') and text.endswith(']'):
        text = text[1:-1]
        return _parse_matcher_list(text, _parse_arg_value_matcher)
    try:
        int_matcher = _parse_int_matcher(text)
        return IntArgValueMatcher(int_matcher)
    except RuntimeError:
        pass
    try:
        float_matcher = _parse_float_matcher(text)
        return FloatArgValueMatcher(float_matcher)
    except RuntimeError:
        pass
    try:
        obj_matcher = _parse_obj_matcher(text)
        return ObjectArgValueMatcher(obj_matcher)
    except RuntimeError:
        pass
    raise RuntimeError(text + ' is not a valid argument matcher')

def _parse_text_matcher(text: str) -> Matcher[str]:
    if text.startswith('[') and text.endswith(']'):
        text = text[1:-1]
        return _parse_matcher_list(text, _parse_text_matcher)
    elif text == '':
        return AlwaysMatcher(True)
    else:
        return identifier_matcher(text)

def _parse_int_matcher(text: str) -> Matcher[int]:
    if text == '*' or text == '':
        return AlwaysMatcher(True)
    else:
        try:
            return EqMatcher(int(text))
        except ValueError:
            raise RuntimeError(text + ' is not a valid int')

def _parse_float_matcher(text: str) -> Matcher[float]:
    try:
        return EqMatcher(float(text))
    except ValueError:
        raise RuntimeError(text + ' is not a valid float')

def _parse_generation_matcher(text: str) -> Matcher[int]:
    return EqMatcher(letter_id_to_number(text), text)

def _is_letter(a: str) -> bool:
    val = ord(a)
    return (
        (val >= ord('a') and val <= ord('z')) or
        (val >= ord('A') and val <= ord('Z'))
    )

def _parse_obj_id_matcher(text: str) -> Matcher[Tuple[int, int]]:
    i = len(text)
    while i > 0 and _is_letter(text[i - 1]):
        i -= 1
    if i < len(text):
        return PairMatcher(
            _parse_int_matcher(text[:i]),
            '',
            _parse_generation_matcher(text[i:]),
        )
    else:
        return PairMatcher(
            _parse_int_matcher(text),
            '',
            AlwaysMatcher(True)
        )

def _parse_obj_matcher(text: str) -> Matcher[wl.ObjectBase]:
    if text.startswith('[') and text.endswith(']'):
        text = text[1:-1]
        return _parse_matcher_list(text, _parse_obj_matcher)
    at_split = _split_pair(text, '#')
    if at_split is None:
        at_split = _split_pair(text, '@')
    if at_split is not None:
        obj_name_text, obj_id_text = at_split
    elif text and ord(text[0]) >= ord('0') and ord(text[0]) <= ord('9'):
        obj_name_text = ''
        obj_id_text = text
    else:
        obj_name_text = text
        obj_id_text = ''
    if obj_name_text and obj_id_text:
        raise RuntimeError(text + ' specifies both object type and ID, should only have one')
    if obj_name_text:
        return ObjectNameMatcher(_parse_text_matcher(obj_name_text))
    elif obj_id_text:
        return ObjectIdMatcher(_parse_obj_id_matcher(obj_id_text))
    else:
        return AlwaysMatcher(True)

def _parse_message_pattern(text: str) -> Matcher[wl.Message]:
    if not text:
        return AlwaysMatcher(True)
    colon_split = _split_pair(text, ':')
    if colon_split is not None:
        conn_text, message_text = colon_split
    else:
        message_text = text
        conn_text = '*'
    dot_split = _split_pair(message_text, '.')
    if dot_split is not None:
        obj_text, name_and_arg_text = dot_split
        peren_split = _split_peren_at_end(message_text)
        if peren_split is not None:
            name_text, arg_text = peren_split
        else:
            name_text = name_and_arg_text
            arg_text = ''
    else:
        peren_split = _split_peren_at_end(message_text)
        if peren_split is not None:
            obj_text, arg_text = peren_split
        else:
            obj_text = message_text
            arg_text = ''
        name_text = ''
    return MessagePattern(
        ConnectionMatcher(_parse_text_matcher(conn_text)),
        _parse_obj_matcher(obj_text),
        _parse_text_matcher(name_text),
        _parse_args_list(arg_text)
    )

# Raises a RuntimeError if text is an invalid matcher
def parse(text: str) -> MessageMatcher:
    text = no_color(text).strip()
    if text == '':
        raise RuntimeError('No matcher given')
    return _parse_matcher_list(text, _parse_message_pattern)

def _as_list(matcher: Matcher[T]) -> MatcherList[T]:
    if isinstance(matcher, MatcherList):
        return matcher
    else:
        return MatcherList([matcher], [])

def join(new: Matcher[T], old: Matcher[T]) -> Matcher[T]:
    if isinstance(old, AlwaysMatcher) or isinstance(new, AlwaysMatcher):
        return new
    old_list = _as_list(old)
    new_list = _as_list(new)
    new_list.positive += old_list.positive
    new_list.negative += old_list.negative
    new_list.positive = [i for i in new_list.positive if i.always() is not True]
    if len(new_list.positive) == 0:
        new_list.positive.append(AlwaysMatcher(True))
    return new_list

if __name__ == '__main__':
    # You may have to run like PYTHONPATH=. python ./core/matcher.py
    set_color_output(True)
    text = sys.argv[1]
    print('input: "' + text + '"')
    m = parse(text)
    print('parsed: ' + str(m))
    print('        ' + repr(m))
    m = m.simplify()
    print('simplified: ' + str(m))
    print('            ' + repr(m))
