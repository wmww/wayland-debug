import sys
import subprocess
import os

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
    my_args_str = ', '.join('"' + i.replace('"', '\\"') + '"' for i in [''] + my_args[1:])
    # Yes, this is exactly what it looks like. It's is python code, inside python code which runs python code
    call_str = 'python import sys; sys.argv = [' + my_args_str + ']; exec(open("' + my_args[0] + '").read())'
    call_args = ['gdb', '-ex', call_str] + gdb_args
    print('Running subprocess: ' + repr(call_args))
    sp = subprocess.Popen(call_args, env=env)
    sp.communicate()

def main():
    # Look for the -d or --gdb arguments, and split the argument list based on where they are
    for i in range(len(sys.argv)):
        if sys.argv[i] == '-d' or sys.argv[i] == '--gdb':
            main_with_args(sys.argv[:i], sys.argv[i+1:])
            return True
    return False
