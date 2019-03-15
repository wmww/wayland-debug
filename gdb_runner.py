import sys
import subprocess
import os

import util

def main_with_args(my_args, gdb_args):
    # The high level plan is to spin up an instance of gdb, and another instance of ourselves inside it

    # Imports will be broken on this new version, so we need to fix the python import path for the child process
    env = os.environ.copy()
    python_path_var = 'PYTHONPATH'
    prev = ''
    if python_path_var in env:
        prev = ':' + env[python_path_var]
    # Add the directeory the running file is located in to the path
    env[python_path_var] = os.path.dirname(os.path.realpath(my_args[0])) + prev

    # All the args before the -d/--gdb need to be sent along to the child instance
    # Since we run the child instance from the GDB command, we need to pack them all in there
    my_args_str = ', '.join('"' + i.replace('"', '\\"') + '"' for i in my_args)
    # Yes, this is exactly what it looks like. It's is python code, inside python code which runs python code
    call_str = 'python import sys; sys.argv = [' + my_args_str + ']; exec(open("' + my_args[0] + '").read())'
    call_args = ['gdb', '-ex', call_str] + gdb_args
    print('Running subprocess: ' + repr(call_args))
    sp = subprocess.Popen(call_args, env=env)
    while True:
        try:
            sp.wait()
            return
        except KeyboardInterrupt:
            pass

def main():
    if util.check_gdb():
        # debugging infinitaly nested debuggers isn't fun
        return False
    # Look for the -d or --gdb arguments, and split the argument list based on where they are
    for i in range(len(sys.argv)):
        if sys.argv[i] == '-g' or sys.argv[i] == '--gdb':
            main_with_args(sys.argv[:i+1], sys.argv[i+1:])
            return True
        elif len(sys.argv[i]) > 2 and sys.argv[i][0] == '-' and sys.argv[i][1] != '-':
            # look for a g in the list of single char args
            for c in sys.argv[i]:
                if c == 'g':
                    # the last batch of args will all go to the child wayland debug, which will simply ignore the 'g'
                    main_with_args(sys.argv[:i+1], sys.argv[i+1:])
                    return True
    return False
