import os
import subprocess

import pytest

import main
from output import stream

def short_log_file():
    path = 'sample_logs/short.log'
    assert os.path.isfile(path)
    return path

def streams():
    return stream.String(), stream.String()

def arguments(*args):
    main_path = 'main.py'
    assert os.path.isfile(main_path)
    return [main_path, *args]

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

def raising_input_func(msg):
    assert False, 'Input should not be requested'

def test_bin_exists_works():
    assert bin_exists('ls') == True
    assert bin_exists('doesnotexist') == False

def test_load_from_file_doesnt_crash():
    out, err = streams()
    args = arguments('-l', short_log_file())
    input_func = lambda msg: 'q'
    main.main(out, err, args, input_func)

def test_load_from_file_shows_messages():
    out, err = streams()
    args = arguments('-l', short_log_file())
    input_func = lambda msg: 'q'
    main.main(out, err, args, input_func)
    assert 'get_registry' in out.buffer, 'output: ' + out.buffer
    assert 'create_surface' in out.buffer, 'output: ' + out.buffer

def test_load_from_file_with_filter():
    out, err = streams()
    args = arguments('-l', short_log_file(), '-f', 'wl_compositor')
    input_func = lambda msg: 'q'
    main.main(out, err, args, input_func)
    assert 'get_registry' not in out.buffer, 'output: ' + out.buffer
    assert 'create_surface' in out.buffer, 'output: ' + out.buffer

@pytest.mark.xfail(reason='see https://github.com/wmww/wayland-debug/issues/17')
def test_load_from_file_with_break():
    out, err = streams()
    args = arguments('-l', short_log_file(), '-b', '[global]')
    input_func = lambda msg: 'q'
    main.main(out, err, args, input_func)
    assert 'get_registry' in out.buffer, 'output: ' + out.buffer
    assert 'create_surface' not in out.buffer, 'output: ' + out.buffer

@pytest.mark.skipif(not bin_exists('weston-info'), reason='weston-info not installed')
def test_gdb_plugin_without_running():
    out, err = streams()
    args = arguments('-g', 'weston-info', '-ex', 'q')
    main.main(out, err, args, raising_input_func)

@pytest.mark.skipif(not bin_exists('weston-info'), reason='weston-info not installed')
@pytest.mark.skipif(not wayland_socket_exists(), reason='no Wayland compositor running')
def test_gdb_plugin_runs():
    '''
    These tests look nice, but they don't seem to detect any errors inside GDB
    Luckily we also have test_runner.py which does
    '''
    out, err = streams()
    args = arguments('-g', 'weston-info', '--ex', 'r')
    main.main(out, err, args, raising_input_func)
