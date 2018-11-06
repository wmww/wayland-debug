#!/usr/bin/python3

import sys
import re

verbose = False

# if we print with colors and such
color_output = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

program_name = 'wayland-debug'
example_usage = 'WAYLAND_DEBUG=1 server-or-client-program 2>&1 1>/dev/null | ' + program_name

# if string is not None, resets to normal at end
def color(color, string):
    result = ''
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

def log(msg):
    if verbose:
        print(color('37', msg))

class WaylandMessage:
    def __init__(self, raw):
        regex = re.findall('\[(\d+)\.(\d+)\]', raw)
        if len(regex) != 1:
            raise RuntimeError(
                'Could not parse "' + raw + '" as Wayland debug message' +
                (' (' + str(len(regex)) + ' regex matches)' if len(regex) > 1 else ''))

    def __str__(self):
        return 'Wayland message'

def main():
    while True:
        line = sys.stdin.readline().strip()
        if line == '':
            break
        try:
            message = WaylandMessage(line)
            print(message)
        except RuntimeError as e:
            log('Parse error: ' + str(e))

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=
        'Debug Wayland protocol messages\n' +
        'To use, pipe in the stderr of a Wayland server or client run with WAYLAND_DEBUG=1.\n' +
        'full usage looks like this:\n' +
        ' $ ' + color('1;37', example_usage))
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose output')
    args = parser.parse_args()

    if args.verbose:
        verbose = True
        log('Verbose output enabled')

    main()

