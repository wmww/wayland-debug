from typing import Optional, List

class NameGenerator:
    def __init__(self) -> None:
        self.index = 0

    def next(self) -> str:
        self.index += 1
        value = self.index
        result = ''
        while value > 0:
            value -= 1
            result = chr(value % 26 + ord('A')) + result
            value //= 26
        return result
