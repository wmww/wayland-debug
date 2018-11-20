import re
from util import *

class Session():
    def __init__(self, display_matcher, stop_matcher, output):
        assert display_matcher
        assert stop_matcher
        self.messages = []
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
        cmd = args[0]
        arg = '' if len(args) < 2 else args[1].strip()
        if cmd in self.commands:
            func = self.commands[cmd]
            self.out.log('Got ' + func.__name__ + ' \'' + arg + '\'')
            func(arg)
        else:
            self.out.warn('Unknown command \'' + cmd + '\'')

    def stop_point_command(self, arg):
        self.out.warn('Stop point command not implemented')

    def continue_command(self, arg):
        self.is_stopped = False
        self.out.log('Continuing...')

if __name__ == '__main__':
    print('File meant to be imported, not run')
    exit(1)
