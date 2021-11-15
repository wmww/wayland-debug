from typing import Optional, List

def number_to_letter_id(value: int, caps: bool) -> str:
    value += 1
    result = ''
    base = ord('A') if caps else ord('a')
    while value > 0:
        value -= 1
        result = chr(value % 26 + base) + result
        value //= 26
    return result

class LetterIdGenerator:
    def __init__(self) -> None:
        self.index = 0

    def next(self) -> str:
        value = self.index
        self.index += 1
        return number_to_letter_id(value, True)
