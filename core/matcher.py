import re
from typing import List, Set, Tuple, Generic, TypeVar, Any, Callable, cast

from core.util import *
from core.output import Output
from core.letter_id_generator import letter_id_to_number
from core import wl

T = TypeVar('T')
U = TypeVar('U')

def show_help(out: Output) -> None:
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
    out.show(result)

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
        if isinstance(self.a, AlwaysMatcher) and self.a.always() is self.b.always():
            return self.a
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

class ObjectIdMatcher(Matcher[wl.ObjectBase]):
    def __init__(self, pair_matcher: Matcher[Tuple[int, int]]) -> None:
        self.pair_matcher = pair_matcher

    def matches(self, obj: wl.ObjectBase) -> bool:
        generation = obj.generation if obj.generation is not None else 0
        return self.pair_matcher.matches((obj.id, generation))

    def simplify(self) -> Matcher[wl.ObjectBase]:
        self.pair_matcher = self.pair_matcher.simplify()
        if isinstance(self.pair_matcher, AlwaysMatcher):
            return self.pair_matcher
        else:
            return self

    def __str__(self) -> str:
        return str(self.pair_matcher)

    def __repr__(self) -> str:
        return 'Object(' + repr(self.pair_matcher) + ')'

class ObjectNameMatcher(Matcher[wl.ObjectBase]):
    def __init__(self, str_matcher: Matcher[str]) -> None:
        self.str_matcher = str_matcher

    def matches(self, obj: wl.ObjectBase) -> bool:
        return obj.type is not None and self.str_matcher.matches(obj.type)

    def simplify(self) -> Matcher[wl.ObjectBase]:
        self.str_matcher = self.str_matcher.simplify()
        if isinstance(self.str_matcher, AlwaysMatcher):
            return self.str_matcher
        else:
            return self

    def __str__(self) -> str:
        return str(self.str_matcher)

    def __repr__(self) -> str:
        return 'ObjectName(' + repr(self.str_matcher) + ')'

class MessagePattern(Matcher[wl.Message]):
    def __init__(
        self,
        obj_matcher: Matcher[wl.ObjectBase],
        name_matcher: Matcher[str],
        args_matcher: Matcher[Tuple[wl.Arg.Base, ...]]
    ) -> None:
        self.obj_matcher = obj_matcher
        self.name_matcher = name_matcher
        self.args_matcher = args_matcher
        self.match_destroyed = self.name_matcher.matches('destroyed')

    def matches(self, message: wl.Message) -> bool:
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
        self.obj_matcher = self.obj_matcher.simplify()
        self.name_matcher = self.name_matcher.simplify()
        self.args_matcher = self.args_matcher.simplify()
        if (self.obj_matcher.always() is False or
            self.name_matcher.always() is False or
            self.args_matcher.always() is False
        ):
            return AlwaysMatcher(False)
        if (self.obj_matcher.always() is True and
            self.name_matcher.always() is True and
            self.args_matcher.always() is True
        ):
            return AlwaysMatcher(True)
        return self

    def __str__(self) -> str:
        return (
            str(self.obj_matcher) +
            '.' + str(self.name_matcher) +
            '(' + str(self.args_matcher) + ')'
        )

    def __repr__(self) -> str:
        return ('Message(' +
            repr(self.obj_matcher) + ', ' +
            repr(self.name_matcher) + ', ' +
            repr(self.args_matcher) + ')'
        )

always: Matcher[Any] = AlwaysMatcher(True)
never: Matcher[Any] = AlwaysMatcher(False)

def str_matcher(pattern: str) -> Matcher[str]:
    if pattern == '*':
        return AlwaysMatcher(True)
    elif '*' in pattern:
        return WildcardMatcher(pattern)
    else:
        return EqMatcher(pattern)

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

def _split_on(text: str, delimiter: str) -> Tuple[str, ...]:
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

def _parse_text_matcher(text: str) -> Matcher[str]:
    if text.startswith('[') and text.endswith(']'):
        text = text[1:-1]
        return _parse_matcher_list(text, _parse_text_matcher)
    elif text == '':
        return AlwaysMatcher(True)
    else:
        return str_matcher(text)

def _parse_int_matcher(text: str) -> Matcher[int]:
    if text == '*' or text == '':
        return AlwaysMatcher(True)
    else:
        try:
            return EqMatcher(int(text))
        except ValueError:
            raise RuntimeError(text + ' is not a valid int')

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
    type_m: Matcher[str] = AlwaysMatcher(True)
    id_m: Matcher[Tuple[int, int]] = AlwaysMatcher(True)
    name_m: Matcher[str] = AlwaysMatcher(True)
    args_m: Matcher[Tuple[wl.Arg.Base, ...]] = AlwaysMatcher(True)
    dot_split = _split_pair(text, '.')
    if dot_split is not None:
        obj_text, name_and_arg_text = dot_split
        peren_split = _split_peren_at_end(text)
        if peren_split is not None:
            name_text, arg_text = peren_split
        else:
            name_text = name_and_arg_text
            arg_text = ''
    else:
        peren_split = _split_peren_at_end(text)
        if peren_split is not None:
            obj_text, arg_text = peren_split
        else:
            obj_text = text
            arg_text = ''
        name_text = ''
    if arg_text:
        raise RuntimeError(text + ' has argument matcher component, this is not yet implemented')
    return MessagePattern(
        _parse_obj_matcher(obj_text),
        _parse_text_matcher(name_text),
        AlwaysMatcher(True)
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
    print('File meant to be imported, not run')
    exit(1)
