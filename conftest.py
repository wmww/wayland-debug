# If this file doesn't exist imports fail when using pytest

import logging

class CustomHandler(logging.NullHandler):
    def __init__(self):
        logging.NullHandler.__init__(self)
        self.formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s');

    def handle(self, record):
        # According to https://docs.python.org/3/library/logging.html#levels >20 is more warning, error or critical
        if record.levelno > 20:
            raise AssertionError(self.formatter.format(record))

logging.getLogger().addHandler(CustomHandler())
