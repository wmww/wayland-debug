import subprocess
import os
from typing import List

from core.util import check_gdb
from frontends.tui import Arguments

def verify_has_debug_symbols(lib: str) -> None:
    reallib = os.path.realpath(lib)
    result = subprocess.run(['file', reallib], check=True, capture_output=True, encoding='utf-8')
    if 'with debug_info' not in result.stdout:
        raise RuntimeError(
            lib + ' does not appear to have debug symbols. ' +
            'See https://github.com/wmww/wayland-debug/blob/master/libwayland_debug_symbols.md ' +
            'for more information')

def verify_gdb_available() -> None:
    result = subprocess.run(['which', 'gdb'], capture_output=True)
    if result.returncode != 0:
        raise RuntimeError('gdb not found, install gdb to use gdb mode')

def run_gdb(args: Arguments, quiet: bool) -> int:
    '''
    Runs GDB, and runs a child instance of this script inside it as a plugin
    Returns GDB's exit status, or -1 for other error
    '''
    # debugging infinitaly nested debuggers isn't fun
    assert not check_gdb(), 'Tried to run GDB from inside GDB'
    verify_gdb_available()
    # Imports will be broken on the new instance, so we need to fix the python import path for the child process
    env = os.environ.copy()
    python_path_var = 'PYTHONPATH'
    prev = ''
    if python_path_var in env:
        prev = ':' + env[python_path_var]
    # Add the directeory the running file is located in to the path
    env[python_path_var] = os.path.dirname(os.path.realpath(args.wayland_debug_args[0])) + prev

    # Get libwayland libs and make sure they have debug symbols
    if args.wayland_lib_dir is not None:
        for lib in ['client', 'server']:
            lib_path = os.path.join(args.wayland_lib_dir, 'libwayland-' + lib + '.so')
            if os.path.exists(lib_path):
                verify_has_debug_symbols(lib_path)

    # Add libwayland libs to the LD_LIBRARY_PATH
    env['LD_LIBRARY_PATH'] = ':'.join(filter(None, [args.wayland_lib_dir, env.get('LD_LIBRARY_PATH', '')]))

    # All the args before the GDB option need to be sent along to the child instance
    # Since we run the child instance from the GDB command, we need to pack them all in there
    my_args_str = ', '.join('"' + i.replace('"', '\\"') + '"' for i in args.wayland_debug_args)
    # Yes, this is exactly what it looks like. It's is python code, inside python code which runs python code
    call_str = 'python import sys; sys.argv = [' + my_args_str + ']; exec(open("' + args.wayland_debug_args[0] + '").read())'
    call_args = ['gdb', '-ex', call_str] + args.command_args
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
