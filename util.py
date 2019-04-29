import sys
import re

def check_gdb():
    '''Check if the gdb module is available, and thus if we are inside a running instance of GDB'''
    import importlib.util
    return importlib.util.find_spec("gdb") is not None

verbose = False

# if we print with colors and such
color_output = False
timestamp_color = '37'
object_color = '1;37'
message_color = None

def set_color_output(val):
    global color_output
    color_output = val

# if string is not None, resets to normal at end
def color(color, string):
    result = ''
    if string == '':
        return ''
    if color_output:
        if color:
            result += '\x1b[' + color + 'm'
        else:
            result += '\x1b[0m'
    if string:
        result += string
        if color_output and color:
            result += '\x1b[0m'
    return result

def no_color(string):
    return re.sub('\x1b\[[\d;]*m', '', string)

def log(msg):
    if verbose:
        if check_gdb():
            print(color('1;34', 'wl log: '), end='')
        print(color('37', msg))

def set_verbose(val):
    global verbose
    verbose = val

def warning(msg):
    print(color('1;33', 'Warning: ') + msg)

def str_matches(pattern, txt):
    pattern = re.escape(pattern)
    pattern = pattern.replace('\*', '.*')
    pattern = '^' + pattern + '$'
    return len(re.findall(pattern, txt)) == 1

class Output:
    def __init__(self, verbose, show_unprocessed, show_file, err_file):
        self.verbose = verbose
        self.show_unprocessed = show_unprocessed
        self.out = show_file
        self.err = err_file

    def show(self, *msg):
        print(' '.join(map(lambda m: str(m), msg)), file=self.out)

    # Used when parsing WAYLAND_DEBUG lines and we come across output we can't parse
    def unprocessed(self, *msg):
        if self.show_unprocessed:
            self.show(color('37', ' ' * 6 + ' |  ' + ' '.join(map(lambda m: str(m), msg))))

    def log(self, *msg):
        if self.verbose:
            print(color('37', 'wl log: ') + ' '.join(map(lambda m: str(m), msg)), file=self.out)

    def warn(self, *msg):
        print(color('1;33', 'Warning: ') + ' '.join(map(lambda m: str(m), msg)), file=self.err)

    def error(self, *msg):
        print(color('1;31', 'Error: ') + ' '.join(map(lambda m: str(m), msg)), file=self.err)

if __name__ == '__main__':
    print('File meant to be imported, not run')
    exit(1)
