#!/usr/bin/python3

import sys
import re

from util import *
import matcher as wl_matcher
import session as wl_session
import parse_wl_debug as parse
import gdb_runner

example_usage = 'WAYLAND_DEBUG=1 program 2>&1 1>/dev/null | ' + sys.argv[0]

def piped_input_main(matcher, show_unparsable_output):
    session = wl_session.Session(matcher)
    parse.file(sys.stdin, session, show_unparsable_output)

def file_input_main(file_path, matcher, show_unparsable_output):
    log('Opening ' + file_path)
    input_file = open(file_path)
    session = wl_session.Session(wl_matcher.Collection.match_none_matcher())
    log('Parsing messages')
    parse.file(input_file, session, show_unparsable_output)
    input_file.close()
    session.print_messages(matcher)
    log('Done')

def main():
    import argparse
    parser = argparse.ArgumentParser(description=
        'Debug Wayland protocol messages. ' +
        'To use, pipe in the stderr of a Wayland server or client run with WAYLAND_DEBUG=1. ' +
        'full usage looks like: ' +
        ' $ ' + color('1;37', example_usage))
    parser.add_argument('--matcher-help', action='store_true', help='show how to write matchers used by filter and quit')
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose output, mostly used for debugging this program')
    parser.add_argument('-l', '--load', type=str, help='Load Wayland events from a file instead of stdin')
    parser.add_argument('-a', '--all', action='store_true', help='show output that can\'t be parsed as Wayland events')
    parser.add_argument('-f', '--filter', type=str, help='only show these objects/messages (see --matcher-help for syntax)')
    parser.add_argument('-F', '--filter-out', type=str, help='don\'t show these objects/messages (see --matcher-help for syntax)')
    parser.add_argument('-b', '--break', dest='_break', type=str, help='break on these objects/messages (see --matcher-help for syntax)')
    parser.add_argument('-d', '--gdb', type=str, help='run inside gdb, all subsequent arguments are sent to gdb')
    # NOTE: -d/--gdb is here only for the help text, it is processed without argparse in gdb_runner.main()
    
    args = parser.parse_args()

    if args.verbose:
        set_verbose(True)
        log('Verbose output enabled')

    if args.matcher_help:
        wl_matcher.print_help()
        exit(1)

    show_unparsable_output = False
    if args.all:
        show_unparsable_output = True
        log('Showing unparsable output')

    use_whitelist = False
    matcher_list = ''
    if args.filter:
        matcher_list = args.filter

    break_matcher = None
    if args._break:
        break_matcher = wl_matcher.Collection(args._break, True)

    matcher = wl_matcher.parse_matcher(matcher_list)
    file_path = args.load

    if check_gdb():
        import gdb_interface
        gdb_interface.main(matcher, break_matcher)
    elif file_path:
        file_input_main(file_path, matcher, show_unparsable_output)
    else:
        piped_input_main(matcher, show_unparsable_output)

if __name__ == '__main__':
    # First, we check if we're supposed to run inside GDB, and do that if so
    if gdb_runner.main():
        pass
    else:
        main()

