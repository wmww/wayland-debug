import re
from util import *

help_command_color = '1;37'

class Command:
    def __init__(self, name, func, help_text):
        self.name = name
        self.func = func
        self.help = help_text
    def matches(self, command):
        return self.name.startswith(command.lower())

class Session():
    def __init__(self, display_matcher, stop_matcher, output):
        assert display_matcher
        assert stop_matcher
        self.messages = []
        self.commands = [
            Command('help', self.help_command,
                'Show this help message, or get help for a specific command'),
            Command('filter', self.filter_command,
                'Add a matcher to filter output, see $ ' + color('1;37', 'help matcher') + ' for matcher syntax'),
            Command('breakpoint', self.break_point_command,
                'Add a matcher that will stop execution, see $ ' + color('1;37', 'help matcher') + ' for matcher syntax'),
            Command('continue', self.break_point_command,
                'Continue processing events'),
            Command('quit', self.quit_command,
                'Quit the program'),
        ]
        self.is_stopped = False
        self.display_matcher = display_matcher
        self.stop_matcher = stop_matcher
        self.out = output

    def stopped(self):
        return self.is_stopped

    def message(self, message):
        self.messages.append(message)
        message.resolve_objects(self)
        if self.display_matcher.matches(message):
            self.out.show(color('37', '{:8.4f}'.format(message.timestamp)) + str(message))
        if self.stop_matcher.matches(message):
            self.out.show(color('1;27', 'Stopped at ') + str(message).strip())
            self.is_stopped = True

    def print_messages(self, matcher):
        for i in self.messages:
            if matcher.matches(i):
                print(i)

    def command(self, command):
        assert isinstance(command, str)
        command = command.strip()
        args = re.split('\s', command, 1)
        if len(args) == 0:
            return False
        cmd = args[0].strip()
        arg = None if len(args) < 2 else args[1].strip()
        cmd = self._get_command(cmd)
        if cmd:
            cmd.func(arg)

    def _get_command(self, command):
        found = []
        for c in self.commands:
            if c.name.startswith(command):
                found.append(c)
        if len(found) == 1:
            return found[0]
        else:
            if len(found) > 1:
                self.out.warn('\'' + command + '\' could refer to multiple commands: ' + ', '.join(c.name for c in found))
            else:
                self.out.warn('Unknown command \'' + command + '\'')
            return None

    def help_command(self, arg):
        if arg:
            if arg == 'matcher':
                import matcher
                matcher.print_help()
                return
            else:
                cmd = self._get_command(arg)
                if cmd:
                    self.out.show(cmd.name + ': ' + cmd.help)
                    return
        self.out.show('Usage: $ ' + color(help_command_color, '<command> <argument>'))
        self.out.show('Help for specific command: $ ' + color(help_command_color, 'help <command>'))
        self.out.show('Help with matcher syntax: $ ' + color(help_command_color, 'help matcher'))
        self.out.show('Commands can be abbreviated (down to just the first letter)')
        self.out.show('Commands:')
        for c in self.commands:
            self.out.show('  ' + color(help_command_color, c.name))

    def filter_command(self, arg):
        self.out.warn('Filter command not implemented')

    def break_point_command(self, arg):
        self.out.warn('Break point command not implemented')

    def continue_command(self, arg):
        self.is_stopped = False
        self.out.log('Continuing...')

    def quit_command(self, arg):
        self.out.warn('Quit command not implemented')

if __name__ == '__main__':
    print('File meant to be imported, not run')
    exit(1)
