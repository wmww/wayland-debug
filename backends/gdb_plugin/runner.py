import subprocess
import os
from typing import List

from core.util import check_gdb

def _get_preload_libs(args: List[str]) -> List[str]:
    # We need to parse --libwayland arg here because we need to add LD_PRELOAD before the instance
    # that parses the args starts up
    path = os.path.join(
        os.path.dirname(__file__),
        '..',
        '..',
        'resources',
        'wayland',
        'build',
        'src')
    path_explicit = False
    for i in range(len(args)):
        if args[i] == '--libwayland':
            assert i + 1 < len(args), '--libwayland requires an argument'
            path = args[i + 1]
            path_explicit = True
            break;
    path = os.path.realpath(path)
    if not os.path.isdir(path):
        if path_explicit:
            raise RuntimeError(path + ' is not a directory')
        else:
            raise RuntimeError(
                path +
                ' is not a directory, ' +
                'consider running resources/get-libwayland.sh or specifying --libwayland')
    client = os.path.join(path, 'libwayland-client.so')
    if not os.path.exists(client):
        raise RuntimeError('Wayland client library does not exist at ' + client)
    server = os.path.join(path, 'libwayland-server.so')
    if not os.path.exists(server):
        raise RuntimeError('Wayland server library does not exist at ' + server)
    return [client, server]

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

def run_gdb(wayland_debug_args: List[str], gdb_args: List[str], quiet: bool) -> int:
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
    env[python_path_var] = os.path.dirname(os.path.realpath(wayland_debug_args[0])) + prev

    # Get libwayland libs and make sure they have debug symbols
    preload_libs = _get_preload_libs(wayland_debug_args)
    for lib in preload_libs:
        verify_has_debug_symbols(lib)

    # Add libwayland libs to LD_PRELOAD
    env['LD_PRELOAD'] = ':'.join([env.get('LD_PRELOAD', '')] + preload_libs)

    # All the args before the GDB option need to be sent along to the child instance
    # Since we run the child instance from the GDB command, we need to pack them all in there
    my_args_str = ', '.join('"' + i.replace('"', '\\"') + '"' for i in wayland_debug_args)
    # Yes, this is exactly what it looks like. It's is python code, inside python code which runs python code
    call_str = 'python import sys; sys.argv = [' + my_args_str + ']; exec(open("' + wayland_debug_args[0] + '").read())'
    call_args = ['gdb', '-ex', call_str] + gdb_args
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
