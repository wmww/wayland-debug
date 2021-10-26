from typing import Optional, List

class NameGenerator:
    def __init__(self) -> None:
        self.name: List[str] = []

    def next(self) -> str:
        self._increment(len(self.name) - 1)
        return ''.join(self.name)

    def _increment(self, current: int) -> None:
        '''Increments a list in place'''
        if current < 0:
            # We have run left past the end of the list without finding a letter to increment
            # We need to add a new letter to the left
            # All other letters have already been set to 'A'
            self.name.insert(0, 'A')
        elif self.name[current] == 'Z':
            # We can't increment this letter any more
            # Set it to 'A' and increment the letter to the left
            self.name[current] = 'A'
            self._increment(current - 1)
        else:
            # Increment the current letter by 1
            self.name[current] = chr(ord(self.name[current]) + 1)
