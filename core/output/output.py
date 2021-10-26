from core.util import color
from . import stream

class Output:
    '''An object that manages text output to the user'''
    def __init__(self, verbose: bool, show_unprocessed: bool, show_stream: stream.Base, err_stream: stream.Base) -> None:
        self.verbose = verbose
        self.show_unprocessed = show_unprocessed
        self.out = show_stream
        self.err = err_stream

    def show(self, *msg) -> None:
        self.out.write(' '.join(map(lambda m: str(m), msg)))

    # Used when parsing WAYLAND_DEBUG lines and we come across output we can't parse
    def unprocessed(self, *msg) -> None:
        if self.show_unprocessed:
            self.show(color('37', ' ' * 6 + ' |  ' + ' '.join(map(lambda m: str(m), msg))))

    def warn(self, *msg) -> None:
        self.err.write(color('1;33', 'Warning: ') + ' '.join(map(lambda m: str(m), msg)))

    def error(self, *msg) -> None:
        self.err.write(color('1;31', 'Error: ') + ' '.join(map(lambda m: str(m), msg)))

class Null(Output):
    '''Null output that does nothging'''
    def __init__(self) -> None:
        null_stream = stream.Null()
        super().__init__(False, False, null_stream, null_stream)

class Strict(Output):
    '''Like Null, except raises on errors or warnings (useful for tests)'''
    def __init__(self) -> None:
        super().__init__(False, False, stream.Null(), stream.ErrorRaising())
