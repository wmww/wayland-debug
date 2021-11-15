from typing import Optional, List

def number_to_letter_id(value: int, caps: bool) -> str:
    assert value >= 0, 'negative input to number_to_letter_id(): ' + str(value)
    value += 1
    result = ''
    base = ord('A') if caps else ord('a')
    while value > 0:
        value -= 1
        result = chr(value % 26 + base) + result
        value //= 26
    return result

def letter_id_to_number(text: str) -> int:
    text = text.lower()
    assert text, 'empty string given to letter_id_to_number()'
    result = -1
    for c in text:
        result = (result + 1) * 26
        v = ord(c) - ord('a')
        assert v >= 0 and v < 26, 'non-letter character in input to letter_id_to_number(): "' + text + '"'
        result += v
    return result

class LetterIdGenerator:
    def __init__(self) -> None:
        self.index = 0

    def next(self) -> str:
        value = self.index
        self.index += 1
        return number_to_letter_id(value, True)
