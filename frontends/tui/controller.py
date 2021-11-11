import re
import logging
from typing import Optional, Callable, List, Tuple

from interfaces import CommandSink, ConnectionList, Connection, UIState
from core import wl, matcher
from core.util import *
from core.output import Output

help_command_color = alert_color

def command_format(cmd: str) -> str:
    if check_gdb():
        return '(gdb) ' + color(help_command_color, 'wl' + cmd)
    else:
        return '$ ' + color(help_command_color, cmd)

class Command:
    def __init__(self, name: str, arg: Optional[str], func: Callable[[str], None], help_text: str) -> None:
        self.name = name
        self.arg = arg
        self.func = func
        self.help = help_text
    def matches(self, command: str) -> bool:
        return self.name.startswith(command.lower())

def _connection_get_type_str(connection: Connection) -> str:
    if connection.is_server() is None:
        return color(bad_color, 'unknown type')
    elif connection.is_server():
        return 'server'
    else:
        return 'client'

class Controller(CommandSink,
                 ConnectionList.Listener,
                 Connection.Listener,
                 UIState):
    def __init__(
        self,
        output: Output,
        connection_list: ConnectionList,
        display_matcher: matcher.MessageMatcher,
        stop_matcher: matcher.MessageMatcher
    ):
        self.out = output
        self.connection_list = connection_list
        connection_list.add_connection_list_listener(self, True)
        self.display_matcher = display_matcher
        self.stop_matcher = stop_matcher
        self.current_connection: Optional[Connection] = None # The connection that is currently being shown
        self.connection_explicitly_selected = False # If the current connection was selected by the user
        # NOTE: remember to also update the readme when command help text changes
        self.commands = [
            Command('help', '[COMMAND]', self.help_command,
                'Show this help message, or get help for a specific command'),
            Command('list', '[CONN:] [MATCHER] [~ COUNT]', self.list_command,
                'List messages matching given matcher (or use the current filter matcher if none provided)\n' +
                'Prepend "CONN:" to show messages from a different connection than the one currently active\n' +
                'Append "~ COUNT" to show at most the last COUNT messages that match\n' +
                'See ' + command_format('help matcher') + ' for matcher syntax'),
            Command('filter', '[MATCHER]', self.filter_command,
                'Show the current output filter matcher, or add a new one\n' +
                'See ' + command_format('help matcher') + ' for matcher syntax'),
            Command('breakpoint', '[MATCHER]', self.break_point_command,
                'Show the current breakpoint matcher, or add a new one\n' +
                'Use the matcher ! to disable existing breakpoints\n' +
                'See ' + command_format('help matcher') + ' for matcher syntax'),
            Command('matcher', '[MATCHER]', self.matcher_command,
                'Parse a matcher, and show it unsimplified'),
            Command('connection', '[CONNECTION]', self.connection_command,
                'Show Wayland connections, or switch to another connection'),
            Command('resume', None, self.resume_command,
                'Resume processing events\n' +
                'In GDB you can also use the continue gdb command'),
            Command('quit', None, self.quit_command,
                'Quit the program'),
        ]
        self.last_shown_timestamp: Optional[float] = None
        self.ui_state_listener = new_disseminator_of_type(UIState.Listener)

    def process_command(self, input_line: str) -> None:
        '''Overrides a method in CommandSink'''
        input_line = input_line.strip()
        args = re.split(r'\s', input_line, 1)
        assert args
        first = no_color(args[0]).strip()
        second = '' if len(args) < 2 else no_color(args[1]).strip()
        if first == '':
            assert not second
            self.out.error('No command specified')
            first = 'help'
        if first == 'w' or first == 'wl': # in case they use GDB style commands when not in GDB
            self.process_command(second)
            return
        if first.startswith('wl'): # in case they use GDB style commands when not in GDB
            first = first[2:]
        command = self._get_command(first)
        if command is not None:
            logging.info('Got ' + command.name + ' command' + (' with \'' + second + '\'' if second else ''))
            command.func(second)

    def toplevel_commands(self) -> List[str]:
        '''Overrides method in CommandSink'''
        return [command.name for command in self.commands]

    def connection_opened(self, connection_list: ConnectionList, connection: Connection) -> None:
        '''Overrides method in ConnectionList.Listener'''
        connection.add_connection_listener(self)
        if self.current_connection:
            if self.connection_explicitly_selected:
                switch_current = False
            elif self.current_connection.is_server() and not connection.is_server:
                switch_current = False
            else:
                switch_current = True
        else:
            switch_current = True
        if switch_current:
            self.current_connection = connection
            self.out.show(color(
                good_color,
                'Switching to new ' + _connection_get_type_str(connection) + ' connection ' + connection.name()))
        else:
            self.out.show(color(
                good_color,
                'New ' + _connection_get_type_str(connection) + ' connection ' + connection.name()))

    def connection_str_changed(self, connection: Connection) -> None:
        '''Overrides method in Connection.Listener'''
        pass

    def connection_app_id_set(self, connection: Connection, new_app_id: str) -> None:
        '''Overrides method in Connection.Listener'''
        pass

    def connection_got_new_message(self, connection: Connection, message: wl.Message) -> None:
        '''Overrides method in Connection.Listener'''
        assert isinstance(message, wl.Message)
        if connection == self.current_connection:
            if self.display_matcher.matches(message):
                self._show_message(message)
            if self.stop_matcher.matches(message):
                self.out.show(color(alert_color, '    Stopped at ') + str(message).strip())
                self.ui_state_listener.pause_requested()

    def connection_closed(self, connection: Connection) -> None:
        '''Overrides method in Connection.Listener'''
        self.out.show(color(
            bad_color,
            'Closed ' + _connection_get_type_str(connection) + ' connection ' + connection.name()))

    def add_ui_state_listener(self, listener: UIState.Listener) -> None:
        '''Overrides method in UIState'''
        self.ui_state_listener.add_listener(listener)

    def remove_ui_state_listener(self, listener: UIState.Listener) -> None:
        '''Overrides method in UIState'''
        self.ui_state_listener.remove_listener(listener)

    def show_messages(self, connection: Connection, matcher: matcher.MessageMatcher, cap: Optional[int]) -> None:
        msg = 'Messages that match ' + str(matcher)
        if connection != self.current_connection:
            msg += ' on connection ' + connection.name()
        msg += ':'
        self.out.show(msg)
        if connection == None:
            self.out.show(' ╰╴ No connection')
            return
        matching, matched, didnt_match, not_searched = self._get_matching(connection, matcher, cap)
        if not matching:
            if not self.connection_list.connections():
                self.out.show(' ╰╴ No messages yet')
            else:
                assert didnt_match == len(connection.messages())
                self.out.show(' ╰╴ None of the ' + color(bad_color, str(didnt_match)) + ' messages so far')
        else:
            self.last_shown_timestamp = None
            for message in matching:
                self._show_message(message)
            self.out.show(
                '(' +
                color((good_color if matched > 0 else symbol_color), str(matched)) + ' matched, ' +
                color((bad_color if didnt_match > 0 else symbol_color), str(didnt_match)) + ' didn\'t' +
                (', ' + color((symbol_color), str(not_searched)) + ' not checked' if not_searched != 0 else '') +
                ')')
            self.last_shown_timestamp = None

    def _show_message(self, message: wl.Message) -> None:
        delta = message.timestamp - self.last_shown_timestamp if self.last_shown_timestamp is not None else 0
        if delta > 1.0:
            self.out.show(color(timestamp_color, '    ───┤ {:0.4f}s ├───'.format(delta)))
        self.last_shown_timestamp = message.timestamp
        message.show(self.out)

    def _get_matching(
        self,
        connection: Connection,
        matcher: matcher.MessageMatcher,
        cap: Optional[int]
    ) -> Tuple[List[wl.Message], int, int, int]:
        if cap == 0:
            cap = None
        didnt_match = 0
        acc = []
        if connection:
            messages = connection.messages()
        else:
            messages = ()
        for message in reversed(messages):
            if matcher.matches(message):
                acc.append(message)
                if cap and len(acc) >= cap:
                    break
            else:
                didnt_match += 1
        return (list(reversed(acc)), len(acc), didnt_match, len(messages) - len(acc) - didnt_match)

    def _get_command(self, command: str) -> Optional[Command]:
        found = []
        for c in self.commands:
            if c.name.startswith(command):
                found.append(c)
        if len(found) == 1:
            return found[0]
        else:
            if len(found) > 1:
                self.out.error('\'' + command + '\' could refer to multiple commands: ' + ', '.join(c.name for c in found))
            else:
                self.out.error('Unknown command \'' + command + '\'')
            return None

    def help_command(self, arg: str) -> None:
        if arg:
            if arg.startswith('wl'):
                arg = arg[2:].strip()
            if arg == 'matcher':
                matcher.show_help(self.out)
                return
            else:
                cmd = self._get_command(arg)
                if cmd:
                    start = command_format(cmd.name) + ': '
                    body = cmd.help.replace('\n', '\n' + ' ' * len(no_color(start)))
                    self.out.show(start + body)
                    return
        self.out.show('Usage: ' + command_format('<COMMAND> [ARGUMENT]'))
        self.out.show('Commands can be abbreviated (down to just the first unique letter)')
        self.out.show('Help with matcher syntax: ' + command_format('help matcher'))
        self.out.show('Commands:')
        for c in self.commands:
            s = c.name
            if c.arg:
                s += ' ' + c.arg
            self.out.show('  ' + command_format(s))

    def parse_and_join(self, new_unparsed: str, old: Optional[matcher.MessageMatcher]) -> matcher.MessageMatcher:
        try:
            parsed = matcher.parse(new_unparsed)
            if old is not None:
                return matcher.join(parsed, old).simplify()
            else:
                return parsed.simplify()
        except RuntimeError as e:
            self.out.error('Failed to parse "' + new_unparsed + '":\n    ' + str(e))
            return old if old is not None else matcher.always

    def filter_command(self, arg: str) -> None:
        if arg:
            self.display_matcher = self.parse_and_join(arg, self.display_matcher)
            self.out.show('Only showing messages that match ' + str(self.display_matcher))
        else:
            self.out.show('Output filter: ' + str(self.display_matcher))

    def break_point_command(self, arg: str) -> None:
        if arg:
            self.stop_matcher = self.parse_and_join(arg, self.stop_matcher)
            self.out.show('Breaking on messages that match: ' + str(self.stop_matcher))
        else:
            self.out.show('Breakpoint matcher: ' + str(self.stop_matcher))

    def matcher_command(self, arg: str) -> None:
        if arg:
            try:
                parsed = matcher.parse(arg)
                unsimplified_str = str(parsed)
                self.out.show('Unsimplified: ' + unsimplified_str)
                self.out.show('  Simplified: ' + str(parsed.simplify()))
                self.out.show('    Reparsed: ' + str(matcher.parse(unsimplified_str).simplify()))
            except RuntimeError as e:
                self.out.error('Failed to parse "' + arg + '":\n    ' + str(e))
        else:
            self.out.show('No matcher to parse')

    def list_command(self, arg: str) -> None:
        cap = None
        connection = self.current_connection
        tilde_split = arg.split('~')
        if len(tilde_split) == 2:
            try:
                cap = int(tilde_split[1])
            except ValueError:
                self.out.error('Expected number after \'~\', got \'' + tilde_split[1] + '\'')
                return
        arg = tilde_split[0]
        m = self.display_matcher
        colon_split = arg.split(':')
        if len(colon_split) == 2:
            c = self._get_connection(colon_split[0])
            if c == None:
                self.out.error('"' + colon_split[0] + '" does not name a connection')
                return
            connection = c
            arg = colon_split[1]
        else:
            arg = colon_split[0]
        if arg:
            m = self.parse_and_join(arg, None)
        if connection is not None:
            self.show_messages(connection, m, cap)
        else:
            self.out.error('No connection')

    def _get_connection(self, name: str) -> Optional[Connection]:
        name = name.lower()
        for connection in self.connection_list.connections():
            if name == connection.name().lower():
                return connection
        return None

    def connection_command(self, arg: str) -> None:
        if arg:
            connection = self._get_connection(arg)
            if connection is not None:
                self.current_connection = connection
                self.out.show('Switched to connection ' + color('1;37', connection.name()))
                self.connection_explicitly_selected = True
                return
            else:
                self.out.error('"' + arg + '" does not name a connection')
        for connection in self.connection_list.connections():
            delim = ', '
            if connection == self.current_connection:
                clr: Optional[str] = alert_color
                line = ' => '
            else:
                clr = symbol_color
                line = '    '
            line += str(connection) + ': '
            line = color(clr, line)
            if connection.is_open():
                line += color(good_color, 'open')
            else:
                line += color(bad_color, 'closed')
            line += delim
            line += color(int_color, str(len(connection.messages()))) + ' messages'
            self.out.show(line)

    def resume_command(self, arg: str) -> None:
        logging.info('Resuming…')
        self.ui_state_listener.resume_requested()

    def quit_command(self, arg: str) -> None:
        logging.info('Quiting…')
        self.ui_state_listener.quit_requested()

if __name__ == '__main__':
    print('File meant to be imported, not run')
    exit(1)
