#!/usr/bin/python3

import sys
import re
import logging
from typing import Callable, List

from interfaces import UIState, ConnectionIDSink, CommandSink
from core import matcher, ConnectionManager
from core.util import check_gdb, set_color_output, set_verbose, color
from core.wl import protocol
from frontends.tui import Controller, TerminalUI
from backends.libwayland_debug_output import parse
from backends import gdb_plugin
from core.output import stream, Output

logging.basicConfig()

logger = logging.getLogger(__name__)
if sys.version_info[0] < 3 or sys.version_info[1] < 8:
    logger.error('Needs at least Python 3.8!')

example_usage = 'WAYLAND_DEBUG=1 program 2>&1 1>/dev/null | ' + sys.argv[0]

def piped_input_main(output: Output, connection_id_sink: ConnectionIDSink) -> None:
    logger.info('Getting input piped from stdin')
    parse.into_sink(sys.stdin, output, connection_id_sink)
    logger.info('Done with input')

def file_input_main(
    file_path: str,
    output: Output,
    connection_id_sink: ConnectionIDSink,
    command_sink: CommandSink,
    ui_state: UIState,
    input_func: Callable[[str], str]
) -> None:
    ui = TerminalUI(command_sink, ui_state, input_func)
    logger.info('Opening ' + file_path)
    try:
        input_file = open(file_path)
        parse.into_sink(input_file, output, connection_id_sink)
        input_file.close()
    except FileNotFoundError:
        output.error(file_path + ' not found')
    ui.run_until_stopped()
    logger.info('Done with file')

def main(out_stream: stream.Base, err_stream: stream.Base, argv: List[str], input_func: Callable[[str], str]) -> None:
    '''
    Parse arguments and run wayland-debug
    out_stream: An instance of stream.Base to use for output
    err_stream: An instance of stream.Base to use for logging and errors
    argv: A list of str arguments (should include the program name like sys.argv)
    input_func: the input builtin, or a mock function that behaves the same
    '''

    # If we want to run inside GDB, the rest of main does not get called in this instance of the script
    # Instead GDB is run, an instance of wayland-debug is run inside it and main() is run in that
    # gdb_plugin.runner.parse_args() will check if this needs to happen, and gdb_plugin.run_gdb() will do it
    gdb_runner_args = gdb_plugin.runner.parse_args(argv)
    if gdb_runner_args:
        gdb_plugin.run_gdb(gdb_runner_args, False)
        return

    import argparse
    parser = argparse.ArgumentParser(description='Debug Wayland protocol messages, see https://github.com/wmww/wayland-debug for additional info')
    parser.add_argument('--matcher-help', action='store_true', help='show how to write matchers and exit')
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose output, mostly used for debugging this program')
    parser.add_argument('-l', '--load', dest='path', type=str, help='load Wayland events from a file instead of stdin')
    parser.add_argument('-s', '--supress', action='store_true', help='supress non-wayland output of the program')
    parser.add_argument('-c', '--color', action='store_true', help='force color output (default for interactive sessions)')
    parser.add_argument('-C', '--no-color', action='store_true', help='disable color output (default for non-interactive sessions)')
    parser.add_argument('-f', '--filter', dest='f', type=str, help='only show these objects/messages (see --matcher-help for syntax)')
    parser.add_argument('-b', '--break', dest='b', type=str, help='stop on these objects/messages (see --matcher-help for syntax)')
    parser.add_argument('-g', '--gdb', action='store_true', help='run inside gdb, all subsequent arguments are sent to gdb, when inside gdb start commands with \'wl\'')
    # NOTE: -g/--gdb is here only for the help text, it is processed without argparse in gdb_runner.main()

    args = parser.parse_args(args=argv[1:]) # chop off the first argument (program name)

    assert not args.gdb, 'GDB argument should have been intercepted by gdb_plugin.runner.parse_args()'

    if args.no_color:
        set_color_output(False)
    elif args.color:
        set_color_output(True)

    verbose = bool(args.verbose)
    unprocessed_output = not bool(args.supress)
    output = Output(verbose, unprocessed_output, out_stream, err_stream)

    if verbose:
        set_verbose(True)
        logger.info('Verbose output enabled')

    if args.no_color:
        if args.color:
            output.warn('Ignoring --color, since --no-color was also specified')
        logger.info('Color output disabled')
    elif args.color:
        # Print message in rainbow colors
        s = ''
        for i, c in enumerate('Color output enabled'):
            s += color('1;' + str(i % 6 + 31), c)
        logger.info(s)

    if unprocessed_output:
        logger.info('Showing unparsable output')

    if args.matcher_help:
        matcher.show_help(output)
        return

    filter_matcher = matcher.always
    if args.f:
        try:
            filter_matcher = matcher.parse(args.f).simplify()
            logger.info('Filter matcher: ' + str(filter_matcher))
        except RuntimeError as e:
            output.error(e)

    stop_matcher = matcher.never
    if args.b:
        try:
            stop_matcher = matcher.parse(args.b).simplify()
            logger.info('Break matcher: ' + str(stop_matcher))
        except RuntimeError as e:
            output.error(e)

    protocol.load_all(output)

    connection_list = ConnectionManager()
    ui_controller = Controller(output, connection_list, filter_matcher, stop_matcher)

    file_path = args.path

    if check_gdb():
        try:
            if file_path:
                output.warn('Ignoring load file because we\'re inside GDB')
            gdb_plugin.plugin.Plugin(output, connection_list, ui_controller, ui_controller)
        except:
            import traceback
            traceback.print_exc()
    elif file_path:
        file_input_main(file_path, output, connection_list, ui_controller, ui_controller, input_func)
    else:
        if args.b:
            output.warn('Ignoring stop matcher when stdin is used for messages')
        piped_input_main(output, connection_list)

def premain() -> None:
    # If isatty() is false, we might be redirecting to a file (or in another non-interactive context)
    # If we're not being run interactivly, we shouldn't use terminal color codes
    # If inside GDB, isatty() may return false but we stil want colors
    if check_gdb() or (hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()):
        set_color_output(True)

    if check_gdb():
        out_stream, err_stream = gdb_plugin.plugin.output_streams()
    else:
        out_stream = stream.Std(sys.stdout)
        err_stream = stream.Std(sys.stderr)

    main(out_stream, err_stream, sys.argv, input)

if __name__ == '__main__':
    premain()
