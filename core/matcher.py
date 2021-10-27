import re
from typing import List, Tuple, Generic, TypeVar, Any

from core.util import *
from core import wl

T = TypeVar('T')
U = TypeVar('U')

class Matcher(Generic[T]):
    def matches(self, message: T) -> bool:
        raise NotImplementedError()

    def simplify(self) -> 'Matcher[T]':
        return self

    def __str__(self) -> str:
        raise NotImplementedError()

MessageMatcher = Matcher[wl.Message]

class AlwaysMatcher(Matcher[Any]):
    def __init__(self, result: bool) -> None:
        self.result = result

    def matches(self, message: T) -> bool:
        return self.result

    def __str__(self) -> str:
        if self.result:
            return color(good_color, '*')
        else:
            return color(bad_color, '!')

class WildcardMatcher(Matcher[str]):
    def __init__(self, pattern: str) -> None:
        self.pattern = pattern
        re_pattern = r'^' + re.escape(pattern).replace(r'\*', '.*') + r'$'
        self.regex = re.compile(re_pattern)

    def matches(self, text: str) -> bool:
        return len(self.regex.findall(text)) > 0

    def __str__(self) -> str:
        return self.pattern

class EqMatcher(Matcher[T]):
    def __init__(self, expected: T) -> None:
        self.expected = expected

    def matches(self, value: T) -> bool:
        return self.expected == value

    def __str__(self) -> str:
        return str(self.expected)

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
        return self

    def __str__(self) -> str:
        return str(self.a) + self.delimiter + str(self.b)

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
            if isinstance(pattern, AlwaysMatcher) and pattern.result:
                return AlwaysMatcher(False)
        for pattern in self.positive:
            if isinstance(pattern, AlwaysMatcher):
                if pattern.result:
                    self.positive = [pattern]
        # Filter out AlwaysMatcher(False) from both
        self.positive = [
            pattern for pattern in self.positive if
                not isinstance(pattern, AlwaysMatcher) or pattern.result]
        self.negative = [
            pattern for pattern in self.negative if
                not isinstance(pattern, AlwaysMatcher) or pattern.result]
        if len(self.positive) == 0:
            return AlwaysMatcher(False)
        elif len(self.positive) == 1 and len(self.negative) == 0:
            return self.positive[0]
        else:
            return self

    def __str__(self) -> str:
        return (
            ', '.join(str(i) for i in self.positive) +
            color(bad_color, ' ! ') +
            ', '.join(str(i) for i in self.negative)
        )

class MessagePattern(Matcher[wl.Message]):
    def __init__(
        self,
        type_matcher: Matcher[str],
        id_matcher: Matcher[Tuple[int, int]],
        name_matcher: Matcher[str],
        args_matcher: Matcher[Tuple[wl.Arg.Base, ...]]
    ) -> None:
        self.type_matcher = type_matcher
        self.id_matcher = id_matcher
        self.name_matcher = name_matcher
        self.args_matcher = args_matcher

    def matches(self, message: wl.Message) -> bool:
        type_name = message.obj.type
        if type_name is None or not self.type_matcher.matches(type_name):
            return False
        id = message.obj.id
        generation = message.obj.generation if message.obj.generation is not None else 0
        if not self.id_matcher.matches((id, generation)):
            return False
        if not self.name_matcher.matches(message.name):
            return False
        if not self.args_matcher.matches(message.args):
            return False
        return True

    def simplify(self) -> Matcher[wl.Message]:
        self.type_matcher = self.type_matcher.simplify()
        self.id_matcher = self.id_matcher.simplify()
        self.name_matcher = self.name_matcher.simplify()
        self.args_matcher = self.args_matcher.simplify()
        return self

    def __str__(self) -> str:
        return (
            str(self.type_matcher) +
            '@' + str(self.id_matcher) +
            '.' + str(self.name_matcher) +
            '(' + str(self.args_matcher) + ')'
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

def print_help():
    pass

closing_chars = {
    '(' : ')',
    '[' : ']',
}
def find_matching(text: str, start: int) -> int:
    opening = text[start]
    closing = closing_chars[opening]
    i = start
    level = 0
    for i in range(start, len(text)):
        if text[i] == opening:
            level += 1
        elif text[i] == closing:
            level -= 1
        if level == 0:
            return i
    raise RuntimeError('Unmatched "' + opening + '" at position ' + str(start))

# Raises a RuntimeError if text is an invalid matcher
def parse(text: str) -> MessageMatcher:
    text = no_color(text).strip()
    if text == '':
        raise RuntimeError('No matcher given')
    return AlwaysMatcher(True)

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
    return new_list

if __name__ == '__main__':
    print('File meant to be imported, not run')
    exit(1)
