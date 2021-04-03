from abc import abstractmethod
from typing import List

class CommandSink:
    '''An interface for processing commands originating from the user'''

    @abstractmethod
    def process_command(self, command: str) -> None:
        '''Parses and executes a user command
        command: the command from the user
        '''
        raise NotImplementedError()

    @abstractmethod
    def toplevel_commands(self) -> List[str]:
        '''Returns a list of toplevel commands'''
        raise NotImplementedError()
