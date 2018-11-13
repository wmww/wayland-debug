#!/usr/bin/python3

import sys
import re

from util import *
import matcher as wl_matcher
import session as wl_session
import parse_wl_debug as parse

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
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose output, mostly used for debugging this program')
    parser.add_argument('-l', '--load', type=str, help='Load Wayland events from a file instead of stdin')
    parser.add_argument('-a', '--all', action='store_true', help='show output that can\'t be parsed as Wayland events')
    parser.add_argument('-f', '--filter', type=str, help='only show these objects/messages (see --matcher-help for syntax)')
    parser.add_argument('-F', '--filter-out', type=str, help='don\'t show these objects/messages (see --matcher-help for syntax)')
    parser.add_argument('--matcher-help', action='store_true', help='show how to write matchers used by filter and quit')
    
    args = parser.parse_args()

    if args.verbose:
        verbose = True
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
    if args.filter_out:
        matcher_list = args.filter_out
    if args.filter:
        if matcher_list:
            warning('filter-out is ignored when a filter is provided')
        matcher_list = args.filter
        use_whitelist = True

    matcher = wl_matcher.Collection(matcher_list, use_whitelist)
    file_path = args.load

    if file_path:
        file_input_main(file_path, matcher, show_unparsable_output)
    else:
        piped_input_main(matcher, show_unparsable_output)

def is_in_gdb():
    import importlib
    loader = importlib.find_loader('gdb')
    return loader is not None

if __name__ == '__main__':
    main()

