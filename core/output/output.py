from core.util import color
from . import stream

class Output:
    '''An object that manages text output to the user'''
    def __init__(self, verbose, show_unprocessed, show_stream, err_stream):
        assert isinstance(verbose, bool)
        assert isinstance(show_unprocessed, bool)
        assert isinstance(show_stream, stream.Base)
        assert isinstance(err_stream, stream.Base)
        self.verbose = verbose
        self.show_unprocessed = show_unprocessed
        self.out = show_stream
        self.err = err_stream

    def show(self, *msg):
        self.out.write(' '.join(map(lambda m: str(m), msg)))

    # Used when parsing WAYLAND_DEBUG lines and we come across output we can't parse
    def unprocessed(self, *msg):
        if self.show_unprocessed:
            self.show(color('37', ' ' * 6 + ' |  ' + ' '.join(map(lambda m: str(m), msg))))

    def warn(self, *msg):
        self.err.write(color('1;33', 'Warning: ') + ' '.join(map(lambda m: str(m), msg)))

    def error(self, *msg):
        self.err.write(color('1;31', 'Error: ') + ' '.join(map(lambda m: str(m), msg)))

class Null(Output):
    '''Null output that does nothging'''
    def __init__(self):
        null_stream = stream.Null()
        super().__init__(False, False, null_stream, null_stream)

class Strict(Output):
    '''Like Null, except raises on errors or warnings (useful for tests)'''
    def __init__(self):
        super().__init__(False, False, stream.Null(), stream.ErrorRaising())
