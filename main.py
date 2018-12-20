#!/usr/bin/python3

import sys
import re

from util import *
import matcher
import session as wl_session
import parse_wl_debug as parse
import gdb_runner

example_usage = 'WAYLAND_DEBUG=1 program 2>&1 1>/dev/null | ' + sys.argv[0]

def piped_input_main(session):
    session.out.log('Getting input piped from stdin')
    for msg in parse.file(sys.stdin, session.out):
        session.message(msg)
    session.out.log('Done')

def file_input_main(session, file_path):
    session.out.log('Opening ' + file_path)
    input_file = open(file_path)
    session.out.log('Parsing messages')
    for msg in parse.file(input_file, session.out):
        session.message(msg)
        while session.stopped():
            if session.quit():
                break
            cmd = input('wl debug $ ')
            session.command(cmd)
        if session.quit():
                break
    input_file.close()
    session.out.log('Done')

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Debug Wayland protocol messages, see https://github.com/wmww/wayland-debug for additional info')
    parser.add_argument('--matcher-help', action='store_true', help='show how to write matchers used by filter and quit')
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose output, mostly used for debugging this program')
    parser.add_argument('-l', '--load', dest='path', type=str, help='load Wayland events from a file instead of stdin')
    parser.add_argument('-s', '--supress', action='store_true', help='supress non-wayland output of the program')
    parser.add_argument('-c', '--color', action='store_true', help='force color output (default for interactive sessions)')
    parser.add_argument('-C', '--no-color', action='store_true', help='disable color output (default for non-interactive sessions)')
    parser.add_argument('-f', '--filter', dest='f', type=str, help='only show these objects/messages (see --matcher-help for syntax)')
    parser.add_argument('-b', '--break', dest='b', type=str, help='stop on these objects/messages (see --matcher-help for syntax)')
    parser.add_argument('-g', '--gdb', action='store_true', help='run inside gdb, all subsequent arguments are sent to gdb, when inside gdb start commands with \'wl\'')
    # NOTE: -d/--gdb is here only for the help text, it is processed without argparse in gdb_runner.main()

    args = parser.parse_args()

    out_file = sys.stdout
    err_file = sys.stderr
    if check_gdb():
        # Stops the annoying continue prompts in GDB
        out_file = sys.stderr

    if args.no_color:
        set_color_output(False)
    elif args.color:
        set_color_output(True)

    verbose = bool(args.verbose)
    unprocessed_output = not bool(args.supress)
    output = Output(verbose, unprocessed_output, out_file, err_file)

    if verbose:
        set_verbose(True)
        output.log('Verbose output enabled')

    if args.no_color:
        if args.color:
            output.warn('Ignoring --color, since --no-color was also specified')
        output.log('Color output disabled')
    elif args.color:
        s = ''
        i = 0
        for i, c in enumerate('Color output enabled'):
            s += color('1;' + str(i % 6 + 31), c)
        output.log(s)

    if unprocessed_output:
        output.log('Showing unparsable output')

    if args.matcher_help:
        matcher.print_help()
        exit(1)

    filter_matcher = matcher.always
    if args.f:
        try:
            filter_matcher = matcher.parse(args.f).simplify()
            output.log('Filter matcher: ' + str(filter_matcher))
        except RuntimeError as e:
            output.error(e)

    stop_matcher = matcher.never
    if args.b:
        try:
            stop_matcher = matcher.parse(args.b).simplify()
            output.log('Break matcher: ' + str(stop_matcher))
        except RuntimeError as e:
            output.error(e)

    session = wl_session.Session(filter_matcher, stop_matcher, output)

    file_path = args.path

    if check_gdb():
        if file_path:
            output.warn('Ignoring load file because we\'re inside GDB')
        import gdb_interface
        gdb_interface.main(session)
    elif file_path:
        file_input_main(session, file_path)
    else:
        if args.b:
            output.warn('Ignoring stop matcher when stdin is used for messages')
        piped_input_main(session)

if __name__ == '__main__':
    if check_gdb() or (hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()):
        set_color_output(True)
    # First, we check if we're supposed to run inside GDB, and do that if so
    if gdb_runner.main():
        pass
    else:
        main()

