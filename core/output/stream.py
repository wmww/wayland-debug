import sys

class Base:
    '''An output stream that supports tokens.'''
    def write(self, thing):
        '''Show anything that can be converted to a string.'''
        self.override_write(str(thing))

    def override_write(self, string):
        '''Print a string to the stream.

        Input is always a string.
        Should print the string to the stream followed by a newline.
        Only for overriding by child classes (not to be called externally).
        '''
        raise NotImplementedError()

class Std(Base):
    def __init__(self, file=sys.stdout):
        self.file = file
    def override_write(self, string):
        print(string, file=self.file)

class String(Base):
    def __init__(self):
        self.buffer = ''
    def override_write(self, string):
        self.buffer += string + '\n'

class Null(Base):
    def override_write(self, string):
        pass

class ErrorRaising(Base):
    def override_write(self, string):
        raise RuntimeError(string)
