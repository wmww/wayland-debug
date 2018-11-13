#!/usr/bin/python3

import sys
import re

from util import *
import matcher as wl_matcher
import wl_data as wl
import session as wl_session
import parse_wl_debug as parse

unparsable_output = False

base_time = None

program_name = 'wayland-debug'
example_usage = 'WAYLAND_DEBUG=1 server-or-client-program 2>&1 1>/dev/null | ' + program_name

def interactive(session, matcher):
    for i in session.messages:
        if matcher.matches(i):
            print(i)

def main(file_path, matcher):
    if file_path:
        input_file = open(file_path)
        session = wl_session.Session(wl_matcher.Collection.match_none_matcher())
        parse.file(input_file, session, unparsable_output)
        input_file.close()
        interactive(session, matcher)
    else:
        session = wl_session.Session(matcher)
        parse.file(sys.stdin, session, unparsable_output)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=
        'Debug Wayland protocol messages. ' +
        'To use, pipe in the stderr of a Wayland server or client run with WAYLAND_DEBUG=1. ' +
        'full usage looks like: ' +
        ' $ ' + color('1;37', example_usage))
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose output, mostly used for debugging this program')
    parser.add_argument('-f', '--file', type=str, help='Read Wayland events from the specified file instead of stdin')
    parser.add_argument('-t', '--show-trash', action='store_true', help='show output as-is if it can not be parsed, default is to filter it')
    parser.add_argument('-b', '--blacklist', type=str, help=
        'colon seporated list (no spaces) of wayland types to hide.' +
        'you can also put a comma seporated list of messages to hide in brackets after the type. ' +
        'example: type_a:type_b[message_a,message_b]')
    parser.add_argument('-w', '--whitelist', type=str, help=
        'only show these objects (all objects are shown if not specified). ' +
        'messages that reference these objects will also be shown, and the optional message list is used to filter those as well.' +
        'same syntax as blacklist')

    args = parser.parse_args()

    if args.verbose:
        verbose = True
        log('Verbose output enabled')

    if args.show_trash:
        unparsable_output = True
        log('Showing unparsable output')

    use_whitelist = False
    matcher_list = ''
    if args.blacklist:
        matcher_list = args.blacklist
    if args.whitelist:
        if matcher_list:
            warning('blacklist is ignored when a whitelist is provided')
        matcher_list = args.whitelist
        use_whitelist = True

    matcher = wl_matcher.Collection(matcher_list, use_whitelist)
    main(args.file, matcher)

