import os

import pytest

import main
from output import stream

def short_log_file():
    path = 'sample_logs/short.log'
    assert os.path.isfile(path)
    return path

def streams():
    return stream.String(), stream.String()

def test_load_from_file_doesnt_crash():
    out, err = streams()
    args = ['-l', short_log_file()]
    input_func = lambda msg: 'q'
    main.main(out, err, args, input_func)

def test_load_from_file_shows_messages():
    out, err = streams()
    args = ['-l', short_log_file()]
    input_func = lambda msg: 'q'
    main.main(out, err, args, input_func)
    assert 'get_registry' in out.buffer, 'output: ' + out.buffer
    assert 'create_surface' in out.buffer, 'output: ' + out.buffer

def test_load_from_file_with_filter():
    out, err = streams()
    args = ['-l', short_log_file(), '-f', 'wl_compositor']
    input_func = lambda msg: 'q'
    main.main(out, err, args, input_func)
    assert 'get_registry' not in out.buffer, 'output: ' + out.buffer
    assert 'create_surface' in out.buffer, 'output: ' + out.buffer

@pytest.mark.xfail(reason="see https://github.com/wmww/wayland-debug/issues/17")
def test_load_from_file_with_break():
    out, err = streams()
    args = ['-l', short_log_file(), '-b', '[global]']
    input_func = lambda msg: 'q'
    main.main(out, err, args, input_func)
    assert 'get_registry' in out.buffer, 'output: ' + out.buffer
    assert 'create_surface' not in out.buffer, 'output: ' + out.buffer
