import os
import subprocess

import main
from backends import gdb_plugin
from core.output import stream

def short_log_file():
    path = 'resources/libwayland_debug_logs/short.log'
    assert os.path.isfile(path), os.getcwd() + '/' + path + ' is not a file'
    return path

def bin_exists(name):
    '''Checks if a program exists on the system'''
    args = ['which', name]
    sp = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    _, _ = sp.communicate()
    return sp.returncode == 0

def wayland_socket_exists():
    xdg_runtime_dir = os.getenv('XDG_RUNTIME_DIR')
    if not xdg_runtime_dir:
        xdg_runtime_dir = '/run/user/1000'
    return os.path.exists(xdg_runtime_dir + '/wayland-0')

def get_main_path():
    main_path = 'main.py'
    assert os.path.isfile(main_path), os.getcwd() + '/' + main_path + ' is not a file'
    return main_path

def run_main(args):
    assert isinstance(args, list)
    args = [get_main_path()] + args
    out = stream.String()
    err = stream.String()
    input_func = lambda msg: 'q'
    main.main(out, err, args, input_func)
    assert err.buffer == '', err.buffer
    return out.buffer

def provision_tmp_path():
    prefix = '/tmp/wldbg-test-'
    for i in range(100):
        try:
            open(prefix + str(i) + '.lock', 'x')
            return prefix + str(i)
        except FileExistsError:
            pass
    raise RuntimeError('Failed to find a free tmp file (' + prefix + '{0 - 100})')

def release_tmp_path(file_path):
    assert file_path.startswith('/tmp')
    if os.path.exists(file_path):
        os.remove(file_path)
    os.remove(file_path + '.lock')

def run_in_gdb(wldbg_args, gdb_args):
    assert isinstance(wldbg_args, list)
    assert isinstance(gdb_args, list)
    tmp_file = provision_tmp_path()
    gdb_args = ['-ex', 'set logging file ' + tmp_file, '-ex', 'set logging on'] + gdb_args
    args = gdb_plugin.runner.Args([get_main_path()] + wldbg_args, gdb_args)
    gdb_plugin.run_gdb(args)
    if os.path.exists(tmp_file):
        with open(tmp_file, 'r') as f:
            result = f.read()
    else:
        result = ''
    release_tmp_path(tmp_file)
    return result

mock_program_path = 'test/mock_program'

def build_mock_program():
    assert bin_exists('meson') and bin_exists('ninja'), 'meson and ninja needed to build mock program'
    build_dir = os.path.join(mock_program_path, 'build')
    if not os.path.isdir(build_dir):
        subprocess.run(['meson', 'build'], cwd = mock_program_path).check_returncode()
    subprocess.run(['ninja', '-C', build_dir]).check_returncode()
    bin_path = os.path.join(build_dir, 'mock_program')
    assert os.path.isfile(bin_path)
    return bin_path
