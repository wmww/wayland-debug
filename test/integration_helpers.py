import os
import subprocess

import main
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

def _raising_input_func(msg):
    raise RuntimeError('Input should not be requested')

def run_main(args, error_on_input=False):
    assert isinstance(args, list)
    main_path = 'main.py'
    assert os.path.isfile(main_path), os.getcwd() + '/' + main_path + ' is not a file'
    args = [main_path] + args
    out = stream.String()
    err = stream.String()
    if error_on_input:
        input_func = _raising_input_func
    else:
        input_func = lambda msg: 'q'
    main.main(out, err, args, input_func)
    assert err.buffer == '', err.buffer
    return out.buffer

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
