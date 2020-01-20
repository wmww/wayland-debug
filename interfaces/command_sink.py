class CommandSink:
    '''An interface for processing commands originating from the user'''

    def process_command(self, command):
        '''Parses and executes a user command
        command: str, the command from the user
        '''
        raise NotImplementedError()

    def toplevel_commands(self):
        '''Returns a list of toplevel commands
        returns: list of str
        '''
        raise NotImplementedError()
