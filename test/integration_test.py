import pytest

from integration_helpers import *

def test_bin_exists_works():
    assert bin_exists('ls') == True
    assert bin_exists('doesnotexist') == False

def test_load_from_file_doesnt_crash():
    run(['-l', short_log_file()])

def test_load_from_file_shows_messages():
    result = run(['-l', short_log_file()])
    assert 'get_registry' in result, 'output: ' + result
    assert 'create_surface' in result, 'output: ' + result

def test_load_from_file_with_filter():
    result = run(['-l', short_log_file(), '-f', 'wl_compositor'])
    assert 'get_registry' not in result, 'output: ' + result
    assert 'create_surface' in result, 'output: ' + result

@pytest.mark.xfail(reason='see https://github.com/wmww/wayland-debug/issues/17')
def test_load_from_file_with_break():
    result = run(['-l', short_log_file(), '-b', '[global]'])
    assert 'get_registry' in result, 'output: ' + result
    assert 'create_surface' not in result, 'output: ' + result

@pytest.mark.skipif(not bin_exists('weston-info'), reason='weston-info not installed')
def test_gdb_plugin_without_running():
    run(['-g', 'weston-info', '-ex', 'q'], error_on_input=True)

@pytest.mark.skipif(not bin_exists('weston-info'), reason='weston-info not installed')
@pytest.mark.skipif(not wayland_socket_exists(), reason='no Wayland compositor running')
def test_gdb_plugin_runs():
    '''
    These tests look nice, but they don't seem to detect any errors inside GDB
    Luckily we also have test_runner.py which does
    '''
    run(['-g', 'weston-info', '--ex', 'r'], error_on_input=True)
