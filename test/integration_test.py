import os

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
    assert 'get_registry' in out.buffer
