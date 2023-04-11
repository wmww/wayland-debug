from typing import List, Optional, Tuple
import sys
import os
from enum import Enum
import logging

from core.util import check_gdb, color, set_color_output
from core import matcher

class Mode(str, Enum):
    RUN = 'run'
    GDB_RUNNER = 'gdb-runner'
    GDB_PLUGIN = 'gdb-plugin'
    LOAD_FROM_FILE = 'load-from-file'
    PIPE = 'pipe'

class Arguments:
    '''
    show_verbose: if to show verbose output
    show_color: if to use terminal colors in output
    show_unprocessed_output: if to pass lines of output that aren't wayland messages through from the program
    mode: the requested mode to use
    load_path: file path to load protocol messages from (if mode is LOAD_FROM_FILE, empty string otherwise)
    filter_matcher: only messages matching this matcher will be shown by default
    stop_matcher: messages matching this matcher will be treated as a breakpoint (if the mode supports that)
    wayland_lib_dir: directory to add to the start of LD_LIBRARY_PATH, should contain a patched and debugable libwayland
    wayland_debug_args: raw arguments, excluding command_args and argument specifying command
    command_args: arguments after command that should be forwarded, or empty if none
    '''
    def __init__(
        self,
        show_verbose: bool,
        show_color: bool,
        show_unprocessed_output: bool,
        mode: Mode,
        load_path: str,
        filter_matcher: matcher.Matcher,
        stop_matcher: matcher.Matcher,
        wayland_lib_dir: Optional[str],
        wayland_debug_args: List[str],
        command_args: List[str]
    ) -> None:
        self.show_verbose = show_verbose
        self.show_color = show_color
        self.show_unprocessed_output = show_unprocessed_output
        self.mode = mode
        self.load_path = load_path
        self.filter_matcher = filter_matcher
        self.stop_matcher = stop_matcher
        self.wayland_lib_dir = wayland_lib_dir
        self.wayland_debug_args = wayland_debug_args
        self.command_args = command_args

    @staticmethod
    def default() -> 'Arguments':
        return Arguments(
            False,
            False,
            False,
            Mode.RUN,
            '',
            matcher.always,
            matcher.never,
            _get_libwayland_lib_path(None),
            ['main.py'],
            [],
        )

def _strip_dashes(s: str) -> str:
    while s.startswith('-'):
        s = s[1:]
    return s

def _starts_with_single_dash(s: str) -> bool:
    return s.startswith('-') and len(s) > 1 and s[1] != '-'

def _split_command(args: List[str], commands: List[List[str]]) -> Tuple[List[str], str, List[str]]:
    '''
    Looks for the first of the given commands, and splits the list into before and after it
    '''
    for i in range(len(args)):
        for command in commands:
            command_id = _strip_dashes(command[0])
            for alias in command:
                if args[i] == alias:
                    return (args[:i], command_id, args[i+1:])
                elif _starts_with_single_dash(alias) and len(args[i]) > 2 and _starts_with_single_dash(args[i]):
                    # look for alias at the end of a list of single char options
                    if _strip_dashes(alias) in args[i][:-1]:
                        raise RuntimeError(repr(args[i]) + ' invalid, ' + alias + ' option must be last when in a list of single-character options')
                    if args[i].endswith(_strip_dashes(alias)):
                        return (args[:i] + [args[i][:-1]], command_id, args[i+1:])
    return (args, '', [])

def _select_mode(command_id: str, args) -> Optional[Mode]:
    modes = []
    if command_id == '':
        pass
    elif command_id == 'g':
        modes.append(Mode.GDB_RUNNER)
    elif command_id == 'r':
        modes.append(Mode.RUN)
    else:
        assert False, 'invalid command ' + command_id

    if check_gdb():
        modes.append(Mode.GDB_PLUGIN)
    if args.path is not None:
        modes.append(Mode.LOAD_FROM_FILE)
    if args.pipe:
        modes.append(Mode.PIPE)

    if len(modes) == 0:
        logging.error('No mode specified')
        return None
    elif len(modes) > 1:
        logging.error(', '.join(modes[:-1]) + ' and ' + modes[-1] + ' modes conflict, please specify a single mode')
        return None
    else:
        return modes[0]

def _get_libwayland_lib_path(explicit_path: Optional[str]) -> Optional[str]:
    if explicit_path:
        path = explicit_path
    else:
        path = os.path.join(
            os.path.dirname(__file__),
            '..',
            '..',
            'resources',
            'wayland',
            'build',
            'src')
    if not os.path.isdir(path):
        logging.warning(path + ' is not a directory, will use the system\'s libwayland. ' +
            'consider running resources/get-libwayland.sh or specifying --libwayland')
        return None
    client = os.path.join(path, 'libwayland-client.so')
    if not os.path.exists(client):
        logging.warning('Wayland client library does not exist at ' + client)
    server = os.path.join(path, 'libwayland-server.so')
    if not os.path.exists(server):
        logging.warning('Wayland server library does not exist at ' + server)
    return path

def parse_args(argv: List[str]) -> Arguments:
    '''
    Parse command line arguments
    argv: A list of str arguments (should include the program name like sys.argv)
    '''

    wayland_debug_args, command_id, command_args = _split_command(argv, [
        ['-g', '--gdb'],
        ['-r', '--run'],
    ])

    import argparse
    parser = argparse.ArgumentParser(description='Debug Wayland protocol messages, see https://github.com/wmww/wayland-debug for additional info')
    parser.add_argument('--matcher-help', action='store_true', help='show how to write matchers and exit')
    parser.add_argument('-r', '--run', action='store_true', help='run the following program and parse it\'s libwayland debugging messages. All subsequent command line arguments are sent to the program')
    parser.add_argument('-g', '--gdb', action='store_true', help='run inside gdb. All subsequent arguments are sent to gdb. When inside gdb start commands with \'wl\'')
    parser.add_argument('-l', '--load', dest='path', type=str, help='load WAYLAND_DEBUG=1 messages from a file')
    parser.add_argument('-p', '--pipe', action='store_true', help='receive WAYLAND_DEBUG=1 messages from stdin (note: messages are printed to stderr so you may want to redirect using 2>&1 before piping)')
    parser.add_argument('-f', '--filter', dest='f', type=str, help='only show these objects/messages (see --matcher-help for syntax)')
    parser.add_argument('-b', '--break', dest='b', type=str, help='stop on these objects/messages (see --matcher-help for syntax)')
    parser.add_argument('-C', '--no-color', action='store_true', help='disable color output (default for non-interactive sessions)')
    parser.add_argument('--color', action='store_true', help='force color output (default for interactive sessions)')
    parser.add_argument('--supress', action='store_true', help='supress non-wayland output of the program')
    parser.add_argument('--verbose', action='store_true', help='verbose output, mostly used for debugging this program')
    parser.add_argument('--libwayland', type=str, help='path to directory that contains libwayland-client.so and libwayland-server.so. Only applies to GDB and run mode. Must come before --gdb/--run argument')
    # NOTE: -g/--gdb, -r/--run and --libwayland are here only for the help text, they are processed without argparse

    args = parser.parse_args(args=wayland_debug_args[1:]) # chop off the first argument (program name)

    show_color = False
    if args.no_color:
        if args.color:
            logging.warn('ignoring --color, since --no-color was also specified')
        show_color = False
        logging.info('color output disabled')
    elif args.color:
        show_color = True
        # Print message in rainbow colors
        s = ''
        for i, c in enumerate('color output enabled'):
            s += color('1;' + str(i % 6 + 31), c)
        logging.info(s)
    elif check_gdb() or (hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()):
        # If isatty() is false, we might be redirecting to a file (or in another non-interactive context)
        # If we're not being run interactivly, we shouldn't use terminal color codes
        # If inside GDB, isatty() may return false but we stil want colors
        show_color = True
    else:
        show_color = False

    show_verbose = bool(args.verbose)
    logging.info('verbose output ' + ('enabled' if show_verbose else 'disabled'))

    show_unprocessed_output = not bool(args.supress)
    logging.info(('showing' if show_unprocessed_output else 'hiding') + 'unprocessed output')

    if args.matcher_help:
        set_color_output(show_color)
        print(matcher.help_text())
        exit(0)

    mode = _select_mode(command_id, args)
    if mode is None:
        parser.print_help()
        exit(0)

    load_path = args.path if args.path else ''

    filter_matcher = matcher.always
    if args.f:
        try:
            filter_matcher = matcher.parse(args.f).simplify()
            logging.info('Filter matcher: ' + str(filter_matcher))
        except RuntimeError as e:
            raise RuntimeError('invalid filter matcher: ' + str(e))

    stop_matcher = matcher.never
    if args.b:
        try:
            stop_matcher = matcher.parse(args.b).simplify()
            logging.info('Break matcher: ' + str(stop_matcher))
        except RuntimeError as e:
            raise RuntimeError('invalid break matcher: ' + str(e))

    libwayland_lib_dir = _get_libwayland_lib_path(args.libwayland)

    return Arguments(
        show_verbose,
        show_color,
        show_unprocessed_output,
        mode,
        load_path,
        filter_matcher,
        stop_matcher,
        libwayland_lib_dir,
        wayland_debug_args,
        command_args
    )
