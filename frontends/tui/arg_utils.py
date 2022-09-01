from typing import List, Optional

class ParsedCommand:
    '''
    Represents arguments split into a section before and after a specific argument.
    wayland_debug_args: the arguments before the command that should be handled by wayland-debug
    command: the command with leading dashes removed (eg 'g'), or an empty string if none
    command_args: arguments after command that should be forwarded, or empty if none
    '''
    def __init__(self, wayland_debug_args: List[str], command: str, command_args: List[str]) -> None:
        self.wayland_debug_args = wayland_debug_args
        self.command = command
        self.command_args = command_args

def _strip_dashes(s: str) -> str:
    while s.startswith('-'):
        s = s[1:]
    return s

def _starts_with_single_dash(s: str) -> bool:
    return s.startswith('-') and len(s) > 1 and s[1] != '-'

def parse_command(args: List[str], commands: List[List[str]]) -> ParsedCommand:
    '''
    Looks for arguments that start a command (eg -g)
    '''
    for i in range(len(args)):
        for command in commands:
            command_id = _strip_dashes(command[0])
            for alias in command:
                if args[i] == alias:
                    return ParsedCommand(args[:i], command_id, args[i+1:])
                elif _starts_with_single_dash(alias) and len(args[i]) > 2 and _starts_with_single_dash(args[i]):
                    # look for alias at the end of a list of single char options
                    if _strip_dashes(alias) in args[i][:-1]:
                        raise RuntimeError(repr(args[i]) + ' invalid, ' + alias + ' option must be last when in a list of single-character options')
                    if args[i].endswith(_strip_dashes(alias)):
                        return ParsedCommand(args[:i] + [args[i][:-1]], command_id, args[i+1:])
    return ParsedCommand(args, '', [])
