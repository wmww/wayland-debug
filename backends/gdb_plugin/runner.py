import subprocess
import os
from typing import List, Optional

from core.util import check_gdb

class Args:
    '''The arguments processed by parse_args() that need to be passed to run_gdb()'''
    def __init__(self, wldbg_args: List[str], gdb_args: List[str]) -> None:
        self.wldbg = wldbg_args
        self.gdb = gdb_args

def run_gdb(args: Args, quiet: bool) -> int:
    '''
    Runs GDB, and runs a child instance of this script inside it as a plugin
    Returns GDB's exit status, or -1 for other error
    '''

    # Imports will be broken on the new instance, so we need to fix the python import path for the child process
    env = os.environ.copy()
    python_path_var = 'PYTHONPATH'
    prev = ''
    if python_path_var in env:
        prev = ':' + env[python_path_var]
    # Add the directeory the running file is located in to the path
    env[python_path_var] = os.path.dirname(os.path.realpath(args.wldbg[0])) + prev

    # All the args before the GDB option need to be sent along to the child instance
    # Since we run the child instance from the GDB command, we need to pack them all in there
    my_args_str = ', '.join('"' + i.replace('"', '\\"') + '"' for i in args.wldbg)
    # Yes, this is exactly what it looks like. It's is python code, inside python code which runs python code
    call_str = 'python import sys; sys.argv = [' + my_args_str + ']; exec(open("' + args.wldbg[0] + '").read())'
    call_args = ['gdb', '-ex', call_str] + args.gdb
    if not quiet:
        print('Running subprocess: ' + repr(call_args))
    sp = subprocess.Popen(call_args, env=env)
    while True:
        try:
            sp.wait()
            return sp.returncode
        except KeyboardInterrupt:
            pass
    return -1

def parse_args(args: List[str]) -> Optional[Args]:
    '''
    Looks for the special -g and --gdb arguements
    Returns None if not found
    Returns an instance of Args if found, which can be passed to run_gdb()
    Returned Args has the arguments before and after the -g split
    '''

    # debugging infinitaly nested debuggers isn't fun
    if check_gdb():
        return None

    # Look for the -d or --gdb arguments, and split the argument list based on where they are
    for i in range(len(args)):
        if args[i] == '-g' or args[i] == '--gdb':
            return Args(args[:i], args[i+1:])
        elif len(args[i]) > 2 and args[i][0] == '-' and args[i][1] != '-':
            # look for a g at the end of a list of single char args
            if 'g' in args[i][:-1]:
                raise RuntimeError(repr(args[i]) + ' invalid, -g option must be last in a list of single-character options')
            if args[i][-1] == 'g':
                return Args(args[:i] + [args[i][:-1]], args[i+1:])

    return None
