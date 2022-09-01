#!/usr/bin/python3

import sys
import re
import logging
from typing import Callable, List

from interfaces import UIState, ConnectionIDSink, CommandSink
from core import matcher, ConnectionManager
from core.util import check_gdb, set_color_output, set_verbose, color
from core.wl import protocol
from frontends.tui import Controller, TerminalUI, parse_args, Arguments, Mode
from backends.libwayland_debug_output import parse
from backends import gdb_plugin
from core.output import stream, Output

logging.basicConfig()

set_verbose(False)
if sys.version_info[0] < 3 or sys.version_info[1] < 8:
    logging.error('Needs at least Python 3.8!')

def piped_input_main(output: Output, connection_id_sink: ConnectionIDSink) -> None:
    logging.info('Getting input piped from stdin')
    parse.into_sink(sys.stdin, output, connection_id_sink)
    logging.info('Done with input')

def file_input_main(
    file_path: str,
    output: Output,
    connection_id_sink: ConnectionIDSink,
    command_sink: CommandSink,
    ui_state: UIState,
    input_func: Callable[[str], str]
) -> None:
    ui = TerminalUI(command_sink, ui_state, input_func)
    logging.info('Opening ' + file_path)
    try:
        input_file = open(file_path)
        parse.into_sink(input_file, output, connection_id_sink)
        input_file.close()
    except FileNotFoundError:
        output.error(file_path + ' not found')
    ui.run_until_stopped()
    logging.info('Done with file')

def main(args: Arguments, output: Output, input_func: Callable[[str], str]) -> None:
    # If we want to run inside GDB, the rest of main does not get called in this instance of the script
    # Instead GDB is run, an instance of wayland-debug is run inside it and main() is run in that
    if args.mode == Mode.GDB_RUNNER:
        try:
            gdb_plugin.run_gdb(args.wayland_debug_args, args.command_args, False)
        except RuntimeError as e:
            logging.error(e)
    else:
        protocol.load_all(output)
        connection_list = ConnectionManager()
        ui_controller = Controller(output, connection_list, args.filter_matcher, args.stop_matcher)
        if args.mode == Mode.GDB_PLUGIN:
            try:
                gdb_plugin.plugin.Plugin(output, connection_list, ui_controller, ui_controller)
            except:
                import traceback
                traceback.print_exc()
        elif args.mode == Mode.LOAD_FROM_FILE:
            file_input_main(args.load_path, output, connection_list, ui_controller, ui_controller, input_func)
        elif args.mode == Mode.PIPE:
            if args.stop_matcher != matcher.never:
                output.warn('Ignoring stop matcher when stdin is used for messages')
            piped_input_main(output, connection_list)
        elif args.mode == Mode.RUN:
            output.error('Run mode not supported yet')
        else:
            assert False, 'invalid mode ' + repr(args.mode)

if __name__ == '__main__':
    if check_gdb():
        out_stream, err_stream = gdb_plugin.plugin.output_streams()
    else:
        out_stream = stream.Std(sys.stdout)
        err_stream = stream.Std(sys.stderr)
    try:
        args = parse_args(sys.argv)
        set_color_output(args.show_color)
        set_verbose(args.show_verbose)
        output = Output(args.show_verbose, args.show_unprocessed_output, out_stream, err_stream)
        main(args, output, input)
    except RuntimeError as e:
        logging.error(e)
        exit(1)
